package downstream

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"

	pb "voiceintegrity/ingestion-gateway/pkg/pb"

	"google.golang.org/protobuf/types/known/timestamppb"
)

// MockDownstreamProcessor is a mock implementation of DownstreamProcessor
// that allows simulating variable latency, outages, and custom score generation.
type MockDownstreamProcessor struct {
	mu            sync.RWMutex
	delay         time.Duration
	failAll       bool
	failRate      float64
	processedSeq  []int64
	callCount     int64
	customHandler func(ctx context.Context, chunk *pb.AudioChunkRequest) (*pb.RiskAssessmentResponse, error)
}

// NewMockDownstreamProcessor creates a mock processor with a specified artificial latency.
func NewMockDownstreamProcessor(delay time.Duration) *MockDownstreamProcessor {
	return &MockDownstreamProcessor{
		delay: delay,
	}
}

func (m *MockDownstreamProcessor) SetDelay(d time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.delay = d
}

func (m *MockDownstreamProcessor) SetFailAll(fail bool) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.failAll = fail
}

func (m *MockDownstreamProcessor) SetCustomHandler(h func(ctx context.Context, chunk *pb.AudioChunkRequest) (*pb.RiskAssessmentResponse, error)) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.customHandler = h
}

func (m *MockDownstreamProcessor) GetCallCount() int64 {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.callCount
}

func (m *MockDownstreamProcessor) ProcessAudioChunk(ctx context.Context, chunk *pb.AudioChunkRequest) (*pb.RiskAssessmentResponse, error) {
	m.mu.Lock()
	delay := m.delay
	failAll := m.failAll
	handler := m.customHandler
	m.callCount++
	m.processedSeq = append(m.processedSeq, chunk.SequenceNumber)
	m.mu.Unlock()

	if delay > 0 {
		select {
		case <-time.After(delay):
		case <-ctx.Done():
			return nil, ctx.Err()
		}
	}

	if failAll {
		return nil, errors.New("simulated downstream 503 service unavailable")
	}

	if handler != nil {
		return handler(ctx, chunk)
	}

	// Default dynamic risk assessment simulation
	riskScore := 0.10 + (float64(chunk.SequenceNumber%5) * 0.05)
	confidence := 0.95
	actions := []pb.RecommendedAction{pb.RecommendedAction_PROCEED}
	explanation := fmt.Sprintf("Clean chunk #%d verified", chunk.SequenceNumber)

	if chunk.ContextualSignal != nil && chunk.ContextualSignal.Available && chunk.ContextualSignal.Score > 0.6 {
		riskScore = 0.82
		confidence = 0.88
		actions = []pb.RecommendedAction{
			pb.RecommendedAction_RECOMMEND_CALLBACK_VERIFICATION,
			pb.RecommendedAction_RECOMMEND_SUPERVISOR_ESCALATION,
		}
		explanation = fmt.Sprintf("High contextual suspicion on chunk #%d: %s", chunk.SequenceNumber, chunk.ContextualSignal.Detail)
	}

	return &pb.RiskAssessmentResponse{
		CallSessionId: chunk.CallSessionId,
		RiskScore:     riskScore,
		Confidence:    confidence,
		Actions:       actions,
		Explanation:   explanation,
		EvaluatedAt:   timestamppb.Now(),
		Degraded:      false,
	}, nil
}
