"""
Pydantic data models for the orchestrator service.

Mirrors the request/response shapes of every downstream microservice so
the orchestrator can serialize/deserialize payloads precisely.

DESIGN INVARIANTS (from SYSTEM_ARCHITECTURE_AND_GUIDE.md):
  - No audio_bytes field appears in any *response* model.
  - All signal models default ``available=False`` — a missing signal is
    NEVER treated as risk-score 0.0 (fail-safe, not fail-open).
  - ``degraded`` defaults to ``True`` so that any uninitialized response
    is already in degraded mode.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------
# Orchestrator inbound request (from the gateway / external caller)
# -----------------------------------------------------------------------

class PipelineRequest(BaseModel):
    """Top-level inbound payload for the orchestrator pipeline."""
    session_id: str
    tenant_id: str
    subject_id: str
    audio_pcm_base64: str = Field(
        description="Base64-encoded PCM audio.  Processed in-memory only — "
                    "NEVER written to disk (DESIGN.md §7).",
    )
    sample_rate_hz: int = 16000
    channels: int = 1
    context_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Contextual risk metadata (e.g., transfer amount, device risk).",
    )
    transcript: str = Field(
        default="",
        description="Conversation transcript for content-risk analysis. "
                    "PII-redacted by the caller before sending.",
    )


# -----------------------------------------------------------------------
# Feature-extraction-service  (POST /v1/extract)
# -----------------------------------------------------------------------

class ExtractionRequest(BaseModel):
    request_id: str
    tenant_id: str
    audio_bytes: str  # base64 string sent as JSON
    sample_rate_hz: int = 16000
    channels: int = 1


class LogMelFeatures(BaseModel):
    frames: List[List[float]]
    n_mels: int = 80
    hop_length_ms: float = 10.0
    sample_rate_hz: int = 16000


class ExtractionResponse(BaseModel):
    request_id: str
    log_mel: LogMelFeatures
    speaker_embedding: List[float]
    duration_ms: float


# -----------------------------------------------------------------------
# Spoof-detection-service  (POST /v1/detect)
# -----------------------------------------------------------------------

class SpoofDetectionRequest(BaseModel):
    call_session_id: str
    tenant_id: str
    audio_features: List[float]
    sample_rate: int = 16000
    feature_type: str = "log_mel"


class SynthesisSignalResponse(BaseModel):
    """Matches the RiskSignal proto shape exactly."""
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    available: bool
    detail: str


# -----------------------------------------------------------------------
# Enrollment-service  (GET /v1/tenants/{id}/subjects/{id}/status)
# -----------------------------------------------------------------------

class VoiceprintStatusResponse(BaseModel):
    status: str  # NOT_ENROLLED | ENROLLED | ENROLLMENT_REVOKED
    voiceprint_id: Optional[str] = None
    version: Optional[int] = None
    sessions_completed: Optional[int] = None
    sessions_remaining: Optional[int] = None
    enrolled_at: Optional[str] = None
    revoked_at: Optional[str] = None


# -----------------------------------------------------------------------
# Risk-fusion-engine  (POST /v1/assess)
# -----------------------------------------------------------------------

class SignalIn(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    available: bool = True
    detail: str = ""


class RiskAssessmentRequest(BaseModel):
    call_session_id: str
    tenant_id: str
    synthesis_signal: SignalIn
    speaker_match_signal: SignalIn
    contextual_signal: SignalIn
    content_risk_signal: Optional[SignalIn] = None


class RiskAssessmentResponse(BaseModel):
    call_session_id: str
    risk_score: float
    confidence: float
    actions: List[str]
    explanation: str
    evaluated_at: str
    degraded: bool


# -----------------------------------------------------------------------
# Policy-threshold-engine  (POST /v1/evaluate)
# -----------------------------------------------------------------------

class RiskAssessmentInput(BaseModel):
    call_session_id: str
    risk_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    actions: List[str]
    explanation: str
    evaluated_at: str
    degraded: bool


class EvaluateRequest(BaseModel):
    tenant_id: str
    assessment: RiskAssessmentInput


class PolicyDecision(BaseModel):
    call_session_id: str
    tenant_id: str
    risk_score: float
    original_actions: List[str]
    final_action: str
    explanation: str
    policy_version: int
    decided_at: str


# -----------------------------------------------------------------------
# Alerting-service  (POST /v1/events)
# -----------------------------------------------------------------------

class PolicyDecisionEventIn(BaseModel):
    event_id: str
    call_session_id: str
    tenant_id: str
    action: str
    risk_score: float
    explanation: str


class EventAcceptedResponse(BaseModel):
    event_id: str
    channels_dispatched: int
    message: str


# -----------------------------------------------------------------------
# Orchestrator pipeline response (returned to the caller)
# -----------------------------------------------------------------------

class PipelineResponse(BaseModel):
    """
    Complete orchestrator response.  Aggregates outputs from every
    pipeline stage so the caller receives a single, self-contained
    result.
    """
    session_id: str
    tenant_id: str
    degraded: bool = True

    # Stage outputs (None when stage could not be reached)
    extraction: Optional[ExtractionResponse] = None
    synthesis_signal: Optional[SynthesisSignalResponse] = None
    speaker_match_signal: Optional[SignalIn] = None
    content_risk_signal: Optional[SignalIn] = None
    risk_assessment: Optional[RiskAssessmentResponse] = None
    policy_decision: Optional[PolicyDecision] = None
    alert_event: Optional[EventAcceptedResponse] = None

    # Fail-safe summary (always populated)
    final_action: str = "RECOMMEND_CALLBACK_VERIFICATION"
    explanation: str = "Pipeline incomplete — manual verification recommended."
