package tests

import (
	"context"
	"io"
	"testing"
	"time"

	"voiceintegrity/ingestion-gateway/internal/downstream"
	pb "voiceintegrity/ingestion-gateway/pkg/pb"

	"google.golang.org/protobuf/types/known/timestamppb"
)

func TestDownstreamFailSafeGracefulDegradation(t *testing.T) {
	// Simulate total downstream service outage
	mockDownstream := downstream.NewMockDownstreamProcessor(0)
	mockDownstream.SetFailAll(true)

	client, cleanup := setupTestServer(t, mockDownstream, nil)
	defer cleanup()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	stream, err := client.StreamAudio(ctx)
	if err != nil {
		t.Fatalf("Failed to open StreamAudio: %v", err)
	}

	callSessionID := "call-failsafe-test-999"
	tenantID := "bank-icici-prod"
	numChunks := 3

	// Stream chunks to server while downstream is down
	go func() {
		for i := 1; i <= numChunks; i++ {
			_ = stream.Send(&pb.AudioChunkRequest{
				CallSessionId:  callSessionID,
				TenantId:       tenantID,
				AudioBytes:     []byte{0xDE, 0xAD, 0xBE, 0xEF},
				SequenceNumber: int64(i),
				Timestamp:      timestamppb.Now(),
				IsLastChunk:    (i == numChunks),
			})
			time.Sleep(10 * time.Millisecond)
		}
		stream.CloseSend()
	}()

	// Assert fail-safe behavior: stream must NOT crash, fail-safe responses MUST be emitted
	responsesReceived := 0
	for {
		resp, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			t.Fatalf("Stream Recv unexpectedly failed instead of returning fail-safe response: %v", err)
		}

		responsesReceived++

		// Verify fail-safe invariants (DESIGN.md §3 & §4.7)
		if !resp.GetDegraded() {
			t.Errorf("Expected Degraded=true when downstream fails")
		}

		if len(resp.GetActions()) == 0 {
			t.Errorf("Expected at least one fail-safe recommended action")
		}

		var hasRecommendAction bool
		for _, action := range resp.GetActions() {
			if action == pb.RecommendedAction_RECOMMEND_CALLBACK_VERIFICATION ||
				action == pb.RecommendedAction_RECOMMEND_SUPERVISOR_ESCALATION ||
				action == pb.RecommendedAction_RECOMMEND_MFA_STEP_UP {
				hasRecommendAction = true
				break
			}
		}

		if !hasRecommendAction {
			t.Errorf("Expected RECOMMEND_* action in fail-safe mode, got: %v", resp.GetActions())
		}
	}

	if responsesReceived != numChunks {
		t.Errorf("Expected %d fail-safe responses, got %d", numChunks, responsesReceived)
	}
}
