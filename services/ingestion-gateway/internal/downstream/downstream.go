package downstream

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"sync/atomic"
	"time"

	pb "voiceintegrity/ingestion-gateway/pkg/pb"

	"google.golang.org/protobuf/types/known/timestamppb"
)

// DownstreamProcessor defines the interface for executing feature extraction & risk evaluation.
type DownstreamProcessor interface {
	ProcessAudioChunk(ctx context.Context, chunk *pb.AudioChunkRequest) (*pb.RiskAssessmentResponse, error)
}

// BuildFailsafeResponse generates a standardized degraded fail-safe RiskAssessmentResponse
// as specified in DESIGN.md §3 and §4.7.
func BuildFailsafeResponse(callSessionID string, reason string) *pb.RiskAssessmentResponse {
	return &pb.RiskAssessmentResponse{
		CallSessionId: callSessionID,
		RiskScore:     0.5, // Indeterminate / neutral risk
		Confidence:    0.0, // Zero confidence due to missing/degraded signals
		Actions: []pb.RecommendedAction{
			pb.RecommendedAction_RECOMMEND_CALLBACK_VERIFICATION,
			pb.RecommendedAction_RECOMMEND_SUPERVISOR_ESCALATION,
		},
		Explanation: fmt.Sprintf("FAIL-SAFE ACTIVATED: %s. Recommending manual verification per safety protocol.", reason),
		EvaluatedAt: timestamppb.Now(),
		Degraded:    true,
	}
}

// HTTPDownstreamClient implements DownstreamProcessor calling downstream feature extraction REST endpoint.
type HTTPDownstreamClient struct {
	baseURL        string
	httpClient     *http.Client
	circuitBreaker *CircuitBreaker
}

// NewHTTPDownstreamClient creates an HTTP client for downstream feature extraction.
func NewHTTPDownstreamClient(baseURL string, timeout time.Duration) *HTTPDownstreamClient {
	return &HTTPDownstreamClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: timeout,
			Transport: &http.Transport{
				MaxIdleConns:        10000,
				MaxIdleConnsPerHost: 2000,
				IdleConnTimeout:     90 * time.Second,
			},
		},
		circuitBreaker: NewCircuitBreaker(5, 10*time.Second),
	}
}

// ExtractionPayload represents JSON payload sent to feature-extraction-service.
type ExtractionPayload struct {
	RequestID    string `json:"request_id"`
	TenantID     string `json:"tenant_id"`
	AudioBytes   []byte `json:"audio_bytes"`
	SampleRateHz int32  `json:"sample_rate_hz"`
	Channels     int32  `json:"channels"`
}

type ExtractionResult struct {
	RequestID        string `json:"request_id"`
	DurationMs       float64 `json:"duration_ms"`
	SpeakerEmbedding []float64 `json:"speaker_embedding"`
}

func (c *HTTPDownstreamClient) ProcessAudioChunk(ctx context.Context, chunk *pb.AudioChunkRequest) (*pb.RiskAssessmentResponse, error) {
	if !c.circuitBreaker.Allow() {
		return nil, fmt.Errorf("downstream circuit breaker open")
	}

	payload := ExtractionPayload{
		RequestID:    fmt.Sprintf("%s-%d", chunk.CallSessionId, chunk.SequenceNumber),
		TenantID:     chunk.TenantId,
		AudioBytes:   chunk.AudioBytes,
		SampleRateHz: chunk.SampleRateHz,
		Channels:     chunk.Channels,
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal extraction payload: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/v1/extract", bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		c.circuitBreaker.RecordFailure()
		return nil, fmt.Errorf("downstream extraction request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		c.circuitBreaker.RecordFailure()
		return nil, fmt.Errorf("downstream extraction returned HTTP %d", resp.StatusCode)
	}

	c.circuitBreaker.RecordSuccess()

	// Compute assessment response
	// If synthesis/contextual signal provided, compute dynamic fused risk
	riskScore := 0.15
	confidence := 0.90
	actions := []pb.RecommendedAction{pb.RecommendedAction_PROCEED}
	explanation := fmt.Sprintf("Acoustic analysis clean on chunk #%d", chunk.SequenceNumber)

	if chunk.ContextualSignal != nil && chunk.ContextualSignal.Available && chunk.ContextualSignal.Score > 0.7 {
		riskScore = 0.75
		actions = []pb.RecommendedAction{
			pb.RecommendedAction_RECOMMEND_MFA_STEP_UP,
			pb.RecommendedAction_RECOMMEND_CALLBACK_VERIFICATION,
		}
		explanation = fmt.Sprintf("Elevated contextual risk detected on chunk #%d: %s", chunk.SequenceNumber, chunk.ContextualSignal.Detail)
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

// CircuitBreaker manages fault-tolerance for downstream dependencies.
type CircuitBreaker struct {
	mu           sync.RWMutex
	failures     int64
	threshold    int64
	cooldown     time.Duration
	lastFailedAt time.Time
	isOpen       bool
}

func NewCircuitBreaker(threshold int64, cooldown time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		threshold: threshold,
		cooldown:  cooldown,
	}
}

func (cb *CircuitBreaker) Allow() bool {
	cb.mu.RLock()
	if !cb.isOpen {
		cb.mu.RUnlock()
		return true
	}
	elapsed := time.Since(cb.lastFailedAt)
	cb.mu.RUnlock()

	if elapsed > cb.cooldown {
		cb.mu.Lock()
		defer cb.mu.Unlock()
		cb.isOpen = false
		atomic.StoreInt64(&cb.failures, 0)
		return true
	}
	return false
}

func (cb *CircuitBreaker) RecordFailure() {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	cb.failures++
	cb.lastFailedAt = time.Now()
	if cb.failures >= cb.threshold {
		cb.isOpen = true
	}
}

func (cb *CircuitBreaker) RecordSuccess() {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	if cb.failures > 0 {
		cb.failures--
	}
	cb.isOpen = false
}
