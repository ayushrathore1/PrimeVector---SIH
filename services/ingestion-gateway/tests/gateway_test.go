package tests

import (
	"context"
	"io"
	"log/slog"
	"net"
	"testing"
	"time"

	"voiceintegrity/ingestion-gateway/config"
	"voiceintegrity/ingestion-gateway/internal/downstream"
	"voiceintegrity/ingestion-gateway/internal/limiter"
	"voiceintegrity/ingestion-gateway/internal/server"
	pb "voiceintegrity/ingestion-gateway/pkg/pb"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/test/bufconn"
	"google.golang.org/protobuf/types/known/timestamppb"
)

const bufSize = 1024 * 1024

func setupTestServer(t *testing.T, downstreamProc downstream.DownstreamProcessor, cfg *config.Config) (pb.IngestionGatewayClient, func()) {
	if cfg == nil {
		cfg = &config.Config{
			ServerPort:           50051,
			Region:               "in-mumbai-1",
			StreamBufferDepth:    8,
			MaxConcurrentStreams: 1000,
			RateLimitRPS:         1000.0,
			RateLimitBurst:       1000,
			DownstreamTimeout:    1 * time.Second,
		}
	}

	lis := bufconn.Listen(bufSize)
	s := grpc.NewServer()

	tenantLimiter := limiter.NewTenantLimiter(cfg.RateLimitRPS, cfg.RateLimitBurst)
	logger := slog.Default()
	gwServer := server.NewGatewayServer(cfg, tenantLimiter, downstreamProc, logger)

	pb.RegisterIngestionGatewayServer(s, gwServer)

	go func() {
		if err := s.Serve(lis); err != nil && err != grpc.ErrServerStopped {
			t.Errorf("Server exited with error: %v", err)
		}
	}()

	bufDialer := func(context.Context, string) (net.Conn, error) {
		return lis.Dial()
	}

	conn, err := grpc.DialContext(
		context.Background(),
		"passthrough://bufnet",
		grpc.WithContextDialer(bufDialer),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		t.Fatalf("Failed to dial bufnet: %v", err)
	}

	client := pb.NewIngestionGatewayClient(conn)

	cleanup := func() {
		conn.Close()
		s.Stop()
		lis.Close()
	}

	return client, cleanup
}

func TestStreamAudioBidirectionalSuccess(t *testing.T) {
	mockDownstream := downstream.NewMockDownstreamProcessor(0)
	client, cleanup := setupTestServer(t, mockDownstream, nil)
	defer cleanup()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Attach region metadata
	ctx = metadata.AppendToOutgoingContext(ctx, "x-region", "in-delhi-1")

	stream, err := client.StreamAudio(ctx)
	if err != nil {
		t.Fatalf("StreamAudio failed to open: %v", err)
	}

	callSessionID := "call-session-abc-123"
	tenantID := "bank-hdfc-prod"
	numChunks := 5

	// Send chunks in background
	go func() {
		for i := 1; i <= numChunks; i++ {
			isLast := (i == numChunks)
			chunk := &pb.AudioChunkRequest{
				CallSessionId:    callSessionID,
				TenantId:         tenantID,
				AudioBytes:       []byte{0x00, 0x01, 0x02, 0x03, 0x04},
				SampleRateHz:     16000,
				Channels:         1,
				SequenceNumber:   int64(i),
				Timestamp:        timestamppb.Now(),
				IsLastChunk:      isLast,
				EnrollmentStatus: pb.EnrollmentStatus_ENROLLED,
			}
			if err := stream.Send(chunk); err != nil {
				t.Errorf("Failed to send chunk %d: %v", i, err)
				return
			}
			time.Sleep(10 * time.Millisecond)
		}
		stream.CloseSend()
	}()

	// Read responses
	receivedCount := 0
	for {
		resp, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			t.Fatalf("Stream Recv error: %v", err)
		}

		receivedCount++
		if resp.GetCallSessionId() != callSessionID {
			t.Errorf("Expected call_session_id %s, got %s", callSessionID, resp.GetCallSessionId())
		}
		if resp.GetDegraded() {
			t.Errorf("Expected non-degraded response in healthy condition")
		}
		if len(resp.GetActions()) == 0 {
			t.Errorf("Expected at least one recommended action")
		}
		if resp.GetRiskScore() < 0.0 || resp.GetRiskScore() > 1.0 {
			t.Errorf("Risk score out of bounds: %f", resp.GetRiskScore())
		}
	}

	if receivedCount != numChunks {
		t.Errorf("Expected %d responses, got %d", numChunks, receivedCount)
	}
}

func TestPingRPC(t *testing.T) {
	mockDownstream := downstream.NewMockDownstreamProcessor(0)
	client, cleanup := setupTestServer(t, mockDownstream, nil)
	defer cleanup()

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	ctx = metadata.AppendToOutgoingContext(ctx, "region", "in-mumbai-1")

	resp, err := client.Ping(ctx, &pb.PingRequest{Message: "hello"})
	if err != nil {
		t.Fatalf("Ping failed: %v", err)
	}

	if resp.GetMessage() != "pong: hello" {
		t.Errorf("Unexpected ping response message: %s", resp.GetMessage())
	}
	if resp.GetRegion() != "in-mumbai-1" {
		t.Errorf("Expected region in-mumbai-1, got %s", resp.GetRegion())
	}
}
