"""
Request/response schemas for the spoof-detection-service.

The response shape (SynthesisSignalResponse) matches the RiskSignal
message in proto/risk_assessment.proto exactly:

    message RiskSignal {
      double score = 1;          // 0.0-1.0, higher = more suspicious
      double confidence = 2;      // 0.0-1.0, model's confidence in `score`
      bool available = 3;         // false if this signal could not be computed
      string detail = 4;          // short human-readable reason, for audit/UI
    }
"""
from pydantic import BaseModel, Field


class SpoofDetectionRequest(BaseModel):
    """
    Input from feature-extraction-service.

    The audio_features field carries the feature vector extracted upstream
    (e.g., wav2vec2 hidden states, mel-spectrogram). Raw audio is never
    sent to this service — it stays transient in the extraction layer
    per DESIGN.md §7.
    """
    call_session_id: str
    tenant_id: str
    audio_features: list[float] = Field(
        ...,
        description="Feature vector extracted upstream (e.g., wav2vec2 hidden states)",
        min_length=1,
    )
    sample_rate: int = Field(
        default=16000,
        description="Sample rate of the original audio, for metadata/routing",
    )
    feature_type: str = Field(
        default="wav2vec2",
        description="Type of features provided, for model compatibility checks",
    )


class SynthesisSignalResponse(BaseModel):
    """
    Output matching RiskSignal proto shape exactly.

    This is the ``synthesis_signal`` consumed by risk-fusion-engine's
    ``/v1/assess`` endpoint. The field names, types, and semantics
    match proto/risk_assessment.proto RiskSignal 1:1.
    """
    score: float = Field(
        ge=0.0, le=1.0,
        description="0.0-1.0, higher = more suspicious",
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="0.0-1.0, model's confidence in score itself",
    )
    available: bool = Field(
        description="false if detection failed, timed out, or no model registered",
    )
    detail: str = Field(
        description=(
            "Human-readable reason for audit/UI. Always includes model "
            "version (required for shadow-mode evaluation pipeline, §4.3), "
            "detected accent cluster, and routing path taken."
        ),
    )
