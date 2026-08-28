"""
Risk Fusion Engine — thin service wrapper.

The wrapper (this file) is boilerplate and can be safely regenerated or
extended by an AI coding tool. The logic it wraps (fusion.py) is not —
see docs/DESIGN.md section 6.
"""
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel, Field

from fusion import Signal, fuse

app = FastAPI(title="risk-fusion-engine", version="0.1.0")


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


class RiskAssessmentResponse(BaseModel):
    call_session_id: str
    risk_score: float
    confidence: float
    actions: list[str]
    explanation: str
    evaluated_at: str
    degraded: bool


@app.post("/v1/assess", response_model=RiskAssessmentResponse)
def assess(req: RiskAssessmentRequest) -> RiskAssessmentResponse:
    result = fuse(
        synthesis=Signal(**req.synthesis_signal.model_dump()),
        speaker_match=Signal(**req.speaker_match_signal.model_dump()),
        contextual=Signal(**req.contextual_signal.model_dump()),
    )
    return RiskAssessmentResponse(
        call_session_id=req.call_session_id,
        risk_score=result.risk_score,
        confidence=result.confidence,
        actions=result.actions,
        explanation=result.explanation,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
        degraded=result.degraded,
    )


@app.get("/healthz")
def healthz():
    # Liveness only. This service is stateless and has no dependencies to
    # check readiness against, which is deliberate (docs/DESIGN.md 5).
    return {"status": "ok"}
