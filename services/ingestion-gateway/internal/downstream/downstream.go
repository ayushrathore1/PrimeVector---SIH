package downstream

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"sync"
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

type LogMelFeatures struct {
	Frames       [][]float64 `json:"frames"`
	NMels        int         `json:"n_mels"`
	HopLengthMs  float64     `json:"hop_length_ms"`
	SampleRateHz int         `json:"sample_rate_hz"`
}

type ExtractionResult struct {
	RequestID        string         `json:"request_id"`
	LogMel           LogMelFeatures `json:"log_mel"`
	SpeakerEmbedding []float64      `json:"speaker_embedding"`
	DurationMs       float64        `json:"duration_ms"`
}

type SpoofDetectionRequestPayload struct {
	CallSessionID string    `json:"call_session_id"`
	TenantID      string    `json:"tenant_id"`
	AudioFeatures []float64 `json:"audio_features"`
	SampleRate    int32     `json:"sample_rate"`
	FeatureType   string    `json:"feature_type"`
}

type SignalPayload struct {
	Score      float64 `json:"score"`
	Confidence float64 `json:"confidence"`
	Available  bool    `json:"available"`
	Detail     string  `json:"detail"`
}

type MatchSpeakerRequestPayload struct {
	LiveEmbedding []float64 `json:"live_embedding"`
}

type RiskFusionRequestPayload struct {
	CallSessionID      string         `json:"call_session_id"`
	TenantID           string         `json:"tenant_id"`
	SynthesisSignal    SignalPayload  `json:"synthesis_signal"`
	SpeakerMatchSignal SignalPayload  `json:"speaker_match_signal"`
	ContextualSignal   SignalPayload  `json:"contextual_signal"`
	ContentRiskSignal  *SignalPayload `json:"content_risk_signal,omitempty"`
}

type RiskFusionResponsePayload struct {
	CallSessionID string   `json:"call_session_id"`
	RiskScore     float64  `json:"risk_score"`
	Confidence    float64  `json:"confidence"`
	Actions       []string `json:"actions"`
	Explanation   string   `json:"explanation"`
	EvaluatedAt   string   `json:"evaluated_at"`
	Degraded      bool     `json:"degraded"`
}

func (c *HTTPDownstreamClient) ProcessAudioChunk(ctx context.Context, chunk *pb.AudioChunkRequest) (*pb.RiskAssessmentResponse, error) {
	if !c.circuitBreaker.Allow() {
		return nil, fmt.Errorf("downstream circuit breaker open")
	}

	// Environment endpoints with standard defaults
	featureExtractionURL := c.baseURL
	spoofDetectionURL := getEnvOrDefault("SPOOF_DETECTION_URL", "http://spoof-detection-service:8002")
	enrollmentURL := getEnvOrDefault("ENROLLMENT_URL", "http://enrollment-service:8003")
	riskFusionURL := getEnvOrDefault("RISK_FUSION_URL", "http://risk-fusion-engine:8000")

	// 1. Call feature-extraction-service (/v1/extract)
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

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, featureExtractionURL+"/v1/extract", bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create extraction request: %w", err)
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

	var extractionRes ExtractionResult
	if err := json.NewDecoder(resp.Body).Decode(&extractionRes); err != nil {
		c.circuitBreaker.RecordFailure()
		return nil, fmt.Errorf("failed to decode extraction response: %w", err)
	}

	// Flatten log mel frames for spoof detection
	var flattenedMel []float64
	for _, frame := range extractionRes.LogMel.Frames {
		flattenedMel = append(flattenedMel, frame...)
	}

	// 2. Call spoof-detection-service (/v1/detect)
	spoofReqPayload := SpoofDetectionRequestPayload{
		CallSessionID: chunk.CallSessionId,
		TenantID:      chunk.TenantId,
		AudioFeatures: flattenedMel,
		SampleRate:    chunk.SampleRateHz,
		FeatureType:   "mel",
	}
	spoofBody, err := json.Marshal(spoofReqPayload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal spoof payload: %w", err)
	}

	sReq, err := http.NewRequestWithContext(ctx, http.MethodPost, spoofDetectionURL+"/v1/detect", bytes.NewReader(spoofBody))
	if err != nil {
		return nil, fmt.Errorf("failed to create spoof request: %w", err)
	}
	sReq.Header.Set("Content-Type", "application/json")

	sResp, err := c.httpClient.Do(sReq)
	if err != nil {
		c.circuitBreaker.RecordFailure()
		return nil, fmt.Errorf("spoof detection request failed: %w", err)
	}
	defer sResp.Body.Close()

	var synthesisSignal SignalPayload
	if sResp.StatusCode >= 200 && sResp.StatusCode < 300 {
		_ = json.NewDecoder(sResp.Body).Decode(&synthesisSignal)
	} else {
		synthesisSignal = SignalPayload{Score: 0.0, Confidence: 0.0, Available: false, Detail: "spoof detection service HTTP error"}
	}

	// 3. Call enrollment-service (/v1/tenants/{tenant_id}/subjects/{subject_id}/match)
	subjectID := chunk.CallSessionId // or session subject identifier
	matchReqPayload := MatchSpeakerRequestPayload{
		LiveEmbedding: extractionRes.SpeakerEmbedding,
	}
	matchBody, err := json.Marshal(matchReqPayload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal match payload: %w", err)
	}

	mURL := fmt.Sprintf("%s/v1/tenants/%s/subjects/%s/match", enrollmentURL, chunk.TenantId, subjectID)
	mReq, err := http.NewRequestWithContext(ctx, http.MethodPost, mURL, bytes.NewReader(matchBody))
	if err != nil {
		return nil, fmt.Errorf("failed to create match request: %w", err)
	}
	mReq.Header.Set("Content-Type", "application/json")

	mResp, err := c.httpClient.Do(mReq)
	if err != nil {
		c.circuitBreaker.RecordFailure()
		return nil, fmt.Errorf("speaker match request failed: %w", err)
	}
	defer mResp.Body.Close()

	var speakerMatchSignal SignalPayload
	if mResp.StatusCode >= 200 && mResp.StatusCode < 300 {
		_ = json.NewDecoder(mResp.Body).Decode(&speakerMatchSignal)
	} else {
		speakerMatchSignal = SignalPayload{Score: 0.5, Confidence: 0.0, Available: false, Detail: "no enrollment record found"}
	}

	// 4. Forward chunk.ContextualSignal and chunk.EnrollmentStatus
	contextualSignal := SignalPayload{
		Score:      0.0,
		Confidence: 0.0,
		Available:  false,
		Detail:     "no contextual signal provided",
	}
	if chunk.ContextualSignal != nil {
		contextualSignal.Score = float64(chunk.ContextualSignal.Score)
		contextualSignal.Confidence = float64(chunk.ContextualSignal.Confidence)
		contextualSignal.Available = chunk.ContextualSignal.Available
		contextualSignal.Detail = chunk.ContextualSignal.Detail
	}

	// Forward enrollment_status from proto (previously silently dropped).
	// Appended to contextual detail so it reaches fusion engine audit trail.
	if es := chunk.GetEnrollmentStatus(); es != pb.EnrollmentStatus_ENROLLMENT_STATUS_UNSPECIFIED {
		contextualSignal.Detail = fmt.Sprintf("%s; enrollment_status=%s", contextualSignal.Detail, es.String())
	}

	// 5. Call risk-fusion-engine (/v1/assess)
	fusionReqPayload := RiskFusionRequestPayload{
		CallSessionID:      chunk.CallSessionId,
		TenantID:           chunk.TenantId,
		SynthesisSignal:    synthesisSignal,
		SpeakerMatchSignal: speakerMatchSignal,
		ContextualSignal:   contextualSignal,
	}

	// Forward content_risk_signal if contextual detail contains transcript analysis
	if chunk.ContextualSignal != nil && chunk.ContextualSignal.Available {
		crs := SignalPayload{
			Score:      float64(chunk.ContextualSignal.Score),
			Confidence: float64(chunk.ContextualSignal.Confidence),
			Available:  chunk.ContextualSignal.Available,
			Detail:     chunk.ContextualSignal.Detail,
		}
		fusionReqPayload.ContentRiskSignal = &crs
	}
	fusionBody, err := json.Marshal(fusionReqPayload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal fusion payload: %w", err)
	}

	fReq, err := http.NewRequestWithContext(ctx, http.MethodPost, riskFusionURL+"/v1/assess", bytes.NewReader(fusionBody))
	if err != nil {
		return nil, fmt.Errorf("failed to create fusion request: %w", err)
	}
	fReq.Header.Set("Content-Type", "application/json")

	fResp, err := c.httpClient.Do(fReq)
	if err != nil {
		c.circuitBreaker.RecordFailure()
		return nil, fmt.Errorf("risk fusion request failed: %w", err)
	}
	defer fResp.Body.Close()

	if fResp.StatusCode < 200 || fResp.StatusCode >= 300 {
		c.circuitBreaker.RecordFailure()
		return nil, fmt.Errorf("risk fusion returned HTTP %d", fResp.StatusCode)
	}

	c.circuitBreaker.RecordSuccess()

	var fusionRes RiskFusionResponsePayload
	if err := json.NewDecoder(fResp.Body).Decode(&fusionRes); err != nil {
		return nil, fmt.Errorf("failed to decode fusion response: %w", err)
	}

	// Map string actions to proto enum actions
	var protoActions []pb.RecommendedAction
	for _, actStr := range fusionRes.Actions {
		switch actStr {
		case "PROCEED":
			protoActions = append(protoActions, pb.RecommendedAction_PROCEED)
		case "RECOMMEND_CALLBACK_VERIFICATION":
			protoActions = append(protoActions, pb.RecommendedAction_RECOMMEND_CALLBACK_VERIFICATION)
		case "RECOMMEND_SUPERVISOR_ESCALATION":
			protoActions = append(protoActions, pb.RecommendedAction_RECOMMEND_SUPERVISOR_ESCALATION)
		case "RECOMMEND_MFA_STEP_UP":
			protoActions = append(protoActions, pb.RecommendedAction_RECOMMEND_MFA_STEP_UP)
		default:
			protoActions = append(protoActions, pb.RecommendedAction_PROCEED)
		}
	}

	return &pb.RiskAssessmentResponse{
		CallSessionId: fusionRes.CallSessionID,
		RiskScore:     fusionRes.RiskScore,

		Confidence:    fusionRes.Confidence,
		Actions:       protoActions,
		Explanation:   fusionRes.Explanation,
		EvaluatedAt:   timestamppb.Now(),
		Degraded:      fusionRes.Degraded,
	}, nil
}

func getEnvOrDefault(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
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
		cb.failures = 0
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
