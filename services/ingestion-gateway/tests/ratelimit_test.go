package tests

import (
	"context"
	"testing"
	"time"

	"voiceintegrity/ingestion-gateway/config"
	"voiceintegrity/ingestion-gateway/internal/downstream"
	pb "voiceintegrity/ingestion-gateway/pkg/pb"

	"google.golang.org/genproto/googleapis/rpc/errdetails"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/timestamppb"
)

func TestTenantRateLimiterEnforcement(t *testing.T) {
	// Configure very tight rate limit: 1 RPS, burst 1
	cfg := &config.Config{
		ServerPort:           50051,
		Region:               "in-mumbai-1",
		StreamBufferDepth:    4,
		MaxConcurrentStreams: 100,
		RateLimitRPS:         1.0,
		RateLimitBurst:       1,
		DownstreamTimeout:    1 * time.Second,
	}

	mockDownstream := downstream.NewMockDownstreamProcessor(0)
	client, cleanup := setupTestServer(t, mockDownstream, cfg)
	defer cleanup()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	stream, err := client.StreamAudio(ctx)
	if err != nil {
		t.Fatalf("StreamAudio failed: %v", err)
	}

	tenantID := "rate-limited-tenant"
	callSessionID := "call-rate-test-1"

	// First chunk should succeed
	err = stream.Send(&pb.AudioChunkRequest{
		CallSessionId:  callSessionID,
		TenantId:       tenantID,
		AudioBytes:     []byte{0x01, 0x02},
		SequenceNumber: 1,
		Timestamp:      timestamppb.Now(),
	})
	if err != nil {
		t.Fatalf("First chunk send failed: %v", err)
	}

	// Immediately send rapid burst of chunks from the same tenant
	for i := 2; i <= 5; i++ {
		_ = stream.Send(&pb.AudioChunkRequest{
			CallSessionId:  callSessionID,
			TenantId:       tenantID,
			AudioBytes:     []byte{0x01, 0x02},
			SequenceNumber: int64(i),
			Timestamp:      timestamppb.Now(),
		})
	}
	stream.CloseSend()

	// Server should reject and return ResourceExhausted (429 equivalent)
	var gotRateLimitErr bool
	for {
		_, err := stream.Recv()
		if err != nil {
			st, ok := status.FromError(err)
			if ok && st.Code() == codes.ResourceExhausted {
				gotRateLimitErr = true

				// Assert retry-after hint in error details
				var foundRetryInfo bool
				for _, detail := range st.Details() {
					if retryInfo, ok := detail.(*errdetails.RetryInfo); ok {
						foundRetryInfo = true
						if retryInfo.GetRetryDelay().GetSeconds() <= 0 {
							t.Errorf("Expected positive RetryDelay seconds, got %v", retryInfo.GetRetryDelay())
						}
					}
				}
				if !foundRetryInfo {
					t.Errorf("Expected google.rpc.RetryInfo in status details")
				}
			}
			break
		}
	}

	if !gotRateLimitErr {
		t.Fatalf("Expected gRPC status codes.ResourceExhausted (429 equivalent), but did not receive it")
	}
}
