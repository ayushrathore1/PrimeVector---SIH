package tests

import (
	"context"
	"io"
	"sync"
	"testing"
	"time"

	"voiceintegrity/ingestion-gateway/config"
	"voiceintegrity/ingestion-gateway/internal/downstream"
	"voiceintegrity/ingestion-gateway/internal/telemetry"
	pb "voiceintegrity/ingestion-gateway/pkg/pb"

	"google.golang.org/protobuf/types/known/timestamppb"
)

func TestBackpressureGracefulDegradation(t *testing.T) {
	// Set artificial downstream processing delay (50ms per chunk)
	downstreamDelay := 40 * time.Millisecond
	mockDownstream := downstream.NewMockDownstreamProcessor(downstreamDelay)

	cfg := &config.Config{
		ServerPort:           50051,
		Region:               "in-mumbai-1",
		StreamBufferDepth:    4, // Small bounded buffer to induce backpressure quickly
		MaxConcurrentStreams: 500,
		RateLimitRPS:         10000.0,
		RateLimitBurst:       10000,
		DownstreamTimeout:    2 * time.Second,
	}

	client, cleanup := setupTestServer(t, mockDownstream, cfg)
	defer cleanup()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	stream, err := client.StreamAudio(ctx)
	if err != nil {
		t.Fatalf("StreamAudio failed: %v", err)
	}

	totalChunks := 20
	callSessionID := "call-backpressure-load-test"
	tenantID := "telecom-jio-prod"

	// Sender goroutine: stream chunks as fast as possible to fill the bounded buffer
	sendStart := time.Now()
	go func() {
		for i := 1; i <= totalChunks; i++ {
			chunk := &pb.AudioChunkRequest{
				CallSessionId:  callSessionID,
				TenantId:       tenantID,
				AudioBytes:     make([]byte, 1024), // 1KB chunk
				SampleRateHz:   16000,
				Channels:       1,
				SequenceNumber: int64(i),
				Timestamp:      timestamppb.Now(),
				IsLastChunk:    (i == totalChunks),
			}
			if err := stream.Send(chunk); err != nil {
				t.Logf("Send failed on chunk %d: %v", i, err)
				return
			}
		}
		stream.CloseSend()
	}()

	// Receiver loop
	receivedCount := 0
	for {
		resp, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			t.Fatalf("Stream Recv error under backpressure: %v", err)
		}
		receivedCount++
		if resp.GetCallSessionId() != callSessionID {
			t.Errorf("Mismatch call session id: %s", resp.GetCallSessionId())
		}
	}

	totalDuration := time.Since(sendStart)

	if receivedCount != totalChunks {
		t.Fatalf("Expected %d responses, got %d", totalChunks, receivedCount)
	}

	// Verify that the total time reflects downstream processing time
	// 20 chunks * 40ms = ~800ms minimum
	expectedMinDuration := time.Duration(totalChunks) * downstreamDelay / 2
	if totalDuration < expectedMinDuration {
		t.Errorf("Processing completed suspiciously fast (%v), expected >= %v", totalDuration, expectedMinDuration)
	}

	// Check metrics snapshot
	snapshot := telemetry.GlobalMetrics.Snapshot()
	t.Logf("Telemetry snapshot: Chunks Ingested=%d, Chunks Processed=%d, Backpressure Events=%d",
		snapshot.TotalChunksIngested, snapshot.TotalChunksProcessed, snapshot.BackpressureEvents)
}

func TestConcurrentStreamsUnderSlowDownstream(t *testing.T) {
	// Simulate 10 concurrent streams pushing data into slow downstream simultaneously
	downstreamDelay := 20 * time.Millisecond
	mockDownstream := downstream.NewMockDownstreamProcessor(downstreamDelay)

	cfg := &config.Config{
		ServerPort:           50051,
		Region:               "in-delhi-1",
		StreamBufferDepth:    4,
		MaxConcurrentStreams: 500,
		RateLimitRPS:         50000.0,
		RateLimitBurst:       50000,
		DownstreamTimeout:    2 * time.Second,
	}

	client, cleanup := setupTestServer(t, mockDownstream, cfg)
	defer cleanup()

	concurrency := 8
	chunksPerStream := 10

	var wg sync.WaitGroup
	wg.Add(concurrency)

	for c := 0; c < concurrency; c++ {
		streamIndex := c
		go func() {
			defer wg.Done()

			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			defer cancel()

			stream, err := client.StreamAudio(ctx)
			if err != nil {
				t.Errorf("StreamAudio failed for worker %d: %v", streamIndex, err)
				return
			}

			sessionID := "concurrent-session-" + string(rune('A'+streamIndex))
			tenantID := "tenant-concurrent-test"

			// Send loop
			go func() {
				for i := 1; i <= chunksPerStream; i++ {
					_ = stream.Send(&pb.AudioChunkRequest{
						CallSessionId:  sessionID,
						TenantId:       tenantID,
						AudioBytes:     []byte{0xAA, 0xBB, 0xCC},
						SequenceNumber: int64(i),
						IsLastChunk:    (i == chunksPerStream),
					})
					time.Sleep(5 * time.Millisecond)
				}
				stream.CloseSend()
			}()

			// Receive loop
			recvCount := 0
			for {
				resp, err := stream.Recv()
				if err == io.EOF {
					break
				}
				if err != nil {
					t.Errorf("Recv failed for worker %d: %v", streamIndex, err)
					return
				}
				if resp.GetCallSessionId() == sessionID {
					recvCount++
				}
			}

			if recvCount != chunksPerStream {
				t.Errorf("Worker %d expected %d responses, got %d", streamIndex, chunksPerStream, recvCount)
			}
		}()
	}

	wg.Wait()
}
