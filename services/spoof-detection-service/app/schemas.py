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
from typing import Optional

from pydantic import BaseModel, Field


class SpoofDetectionRequest(BaseModel):
    """
    Input for spoof-detection inference.

    Supports two detection paths (dual-path audio delivery):

    1. **Trained model path** (preferred): When ``audio_pcm_base64`` is
       provided, the service decodes the raw PCM in-memory, computes a
       128-band log-mel spectrogram internally, and runs the trained
       ResNet18+GRU+Attention deepfake classifier.  Audio bytes are
       immediately dereferenced after inference (DESIGN.md section 7).

    2. **Heuristic fallback**: When ``audio_pcm_base64`` is absent, the
       service falls back to the log-mel heuristic scorer using the
       pre-extracted ``audio_features`` vector.
    """
    call_session_id: str
    tenant_id: str
    audio_features: list[float] = Field(
        default_factory=list,
        description="Flattened log-mel feature vector from feature-extraction-service (heuristic fallback path)",
    )
    audio_pcm_base64: Optional[str] = Field(
        default=None,
        description=(
            "Base64-encoded 16-bit PCM audio for trained model inference. "
            "Processed in-memory only -- NEVER written to disk (DESIGN.md section 7)."
        ),
    )
    sample_rate: int = Field(
        default=16000,
        description="Sample rate of the original audio, for metadata/routing",
    )
    feature_type: str = Field(
        default="log_mel",
        description="Type of features provided (log_mel), for model compatibility checks",
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
