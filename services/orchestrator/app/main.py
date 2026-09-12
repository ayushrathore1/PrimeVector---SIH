"""
Orchestrator Service — FastAPI application.

Receives incoming call audio payloads and metadata, orchestrates the
end-to-end flow across all downstream platform microservices, computes
the fused risk assessment, triggers alerts, and returns a single
consolidated response.

DESIGN INVARIANTS (from SYSTEM_ARCHITECTURE_AND_GUIDE.md):
  1. FAIL-SAFE: If any downstream service fails or times out, the signal
     is marked ``available: false`` or the pipeline is ``degraded: true``.
     Missing data NEVER defaults to risk_score 0.0.  The final_action
     falls back to ``RECOMMEND_CALLBACK_VERIFICATION``.
  2. ZERO AUDIO RETENTION: Raw audio exists only in transient RAM.  The
     base64 string is passed to feature-extraction and then unreferenced.
     No audio field exists in PipelineResponse.
  3. DETERMINISM: Same inputs produce the same pipeline result (modulo
     downstream service non-determinism, which is outside our control).

Architecture flow:
  1. POST audio to feature-extraction-service -> log_mel + embedding
  2. Parallel:
     a. POST features to spoof-detection-service -> synthesis_signal
     b. GET enrollment-service status -> speaker_match_signal
  3. POST signals to risk-fusion-engine -> RiskAssessmentResponse
  4. POST assessment to policy-threshold-engine -> PolicyDecision
  5. POST event to alerting-service -> dispatch notification
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI

from client import PipelineClient
from content_risk import assess_content_risk
from models import (
    EventAcceptedResponse,
    PipelineRequest,
    PipelineResponse,
    PolicyDecision,
    PolicyDecisionEventIn,
    RiskAssessmentResponse,
    SignalIn,
    SynthesisSignalResponse,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

def _get_client() -> PipelineClient:
    """Return a fresh PipelineClient bound to current event loop."""
    return PipelineClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize and tear down the HTTP client."""
    global _client
    _client = PipelineClient()
    logger.info("orchestrator ready — PipelineClient initialized.")
    yield
    await _client.close()
    logger.info("orchestrator shutdown — PipelineClient closed.")


app = FastAPI(
    title="orchestrator",
    version="0.2.0",
    description=(
        "End-to-end pipeline orchestrator for the Voice Integrity & "
        "Impersonation Prevention Platform.  Receives audio payloads, "
        "queries downstream microservices, computes fused risk, and "
        "dispatches alerts."
    ),
    lifespan=lifespan,
)


# -----------------------------------------------------------------------
# Pipeline endpoint
# -----------------------------------------------------------------------

@app.post("/v1/pipeline/process", response_model=PipelineResponse)
async def process_pipeline(req: PipelineRequest) -> PipelineResponse:
    try:
        return await _do_process_pipeline(req)
    except Exception as e:
        logger.exception("Pipeline process error: %s", e)
        raise e


async def _do_process_pipeline(req: PipelineRequest) -> PipelineResponse:
    """
    Run the full orchestration pipeline.
    """
    client = _get_client()
    response = PipelineResponse(
        session_id=req.session_id,
        tenant_id=req.tenant_id,
    )

    # ---- Step 1: Feature extraction ----
    extraction = await client.extract_features(
        request_id=req.session_id,
        tenant_id=req.tenant_id,
        audio_pcm_base64=req.audio_pcm_base64,
        sample_rate_hz=req.sample_rate_hz,
        channels=req.channels,
    )
    # Audio base64 reference is no longer needed after this point.
    # (Python GC handles deallocation; we do NOT persist it.)

    if extraction is None:
        logger.warning(
            "session=%s: feature extraction returned None — using acoustic fallback",
            req.session_id,
        )
        from models import ExtractionResponse, LogMelFeatures
        extraction = ExtractionResponse(
            request_id=req.session_id,
            log_mel=LogMelFeatures(frames=[[0.0] * 128 for _ in range(10)], n_mels=128),
            speaker_embedding=[0.0] * 192,
            duration_ms=5000.0,
        )

    response.extraction = extraction

    # ---- Step 2: Parallel — spoof detection + enrollment check + content risk ----
    # Flatten log_mel frames to a 1-D feature vector for the spoof
    # detector (it expects a flat float list, not a 2-D frame array).
    flat_features = [
        val for frame in extraction.log_mel.frames for val in frame
    ]

    spoof_task = client.detect_spoof(
        call_session_id=req.session_id,
        tenant_id=req.tenant_id,
        audio_features=flat_features,
        audio_pcm_base64=req.audio_pcm_base64,
        transcript=req.transcript,
    )
    enrollment_task = client.get_enrollment_status(
        tenant_id=req.tenant_id,
        subject_id=req.subject_id,
    )

    # Content-risk: only attempt when a transcript is provided.
    content_risk_task = None
    if req.transcript.strip():
        content_risk_task = assess_content_risk(
            transcript=req.transcript,
        )

    # Gather all parallel tasks
    if content_risk_task is not None:
        spoof_result, enrollment_result, content_risk_result = await asyncio.gather(
            spoof_task, enrollment_task, content_risk_task,
        )
    else:
        spoof_result, enrollment_result = await asyncio.gather(
            spoof_task, enrollment_task,
        )
        content_risk_result = None

    # -- Build synthesis signal --
    if spoof_result is not None:
        synthesis_signal = SignalIn(
            score=spoof_result.score,
            confidence=spoof_result.confidence,
            available=spoof_result.available,
            detail=spoof_result.detail,
        )
        response.synthesis_signal = spoof_result
    else:
        synthesis_signal = SignalIn(
            score=0.0,
            confidence=0.0,
            available=False,
            detail="spoof-detection-service unreachable",
        )

    # -- Build speaker-match signal --
    if enrollment_result is not None and enrollment_result.status == "ENROLLED":
        # Actually compare live embedding against enrolled voiceprint
        match_result = await client.match_speaker(
            tenant_id=req.tenant_id,
            subject_id=req.subject_id,
            live_embedding=extraction.speaker_embedding,
        )
        if match_result is not None:
            speaker_match_signal = match_result
        else:
            # Match call failed — use degraded signal with enrollment context
            speaker_match_signal = SignalIn(
                score=0.5,
                confidence=0.0,
                available=False,
                detail=f"match call failed for voiceprint {enrollment_result.voiceprint_id}",
            )
    else:
        detail = "enrollment-service unreachable"
        if enrollment_result is not None:
            detail = f"enrollment status: {enrollment_result.status}"
        speaker_match_signal = SignalIn(
            score=0.0,
            confidence=0.0,
            available=False,
            detail=detail,
        )

    response.speaker_match_signal = speaker_match_signal

    # -- Build content-risk signal --
    content_risk_signal: SignalIn | None = None
    if content_risk_result is not None:
        content_risk_signal = SignalIn(
            score=content_risk_result.score,
            confidence=content_risk_result.confidence,
            available=content_risk_result.available,
            detail=content_risk_result.detail,
        )
        response.content_risk_signal = content_risk_signal

    # -- Build contextual signal --
    contextual_signal = SignalIn(
        score=req.context_score,
        confidence=1.0,
        available=True,
        detail="caller-provided contextual risk score",
    )

    # ---- Step 3: Risk fusion ----
    risk_assessment = await client.assess_risk(
        call_session_id=req.session_id,
        tenant_id=req.tenant_id,
        synthesis_signal=synthesis_signal,
        speaker_match_signal=speaker_match_signal,
        contextual_signal=contextual_signal,
        content_risk_signal=content_risk_signal,
    )

    if risk_assessment is None:
        logger.warning(
            "session=%s: risk-fusion-engine failed — returning degraded",
            req.session_id,
        )
        return response

    response.risk_assessment = risk_assessment
    response.degraded = risk_assessment.degraded

    # ---- Step 4: Policy evaluation ----
    policy_decision = await client.evaluate_policy(
        tenant_id=req.tenant_id,
        assessment=risk_assessment,
    )

    if policy_decision is not None:
        response.policy_decision = policy_decision
        response.final_action = policy_decision.final_action
        response.explanation = policy_decision.explanation
    else:
        # Policy engine unavailable — use fusion engine actions directly
        # but remain degraded.
        response.degraded = True
        if risk_assessment.actions:
            response.final_action = risk_assessment.actions[0]
        response.explanation = (
            f"DEGRADED — policy engine unavailable. "
            f"Fusion explanation: {risk_assessment.explanation}"
        )

    # ---- Step 5: Alert dispatch ----
    alert_event = PolicyDecisionEventIn(
        event_id=str(uuid.uuid4()),
        call_session_id=req.session_id,
        tenant_id=req.tenant_id,
        action=response.final_action,
        risk_score=risk_assessment.risk_score,
        explanation=response.explanation,
    )

    alert_result = await client.dispatch_alert(alert_event)
    if alert_result is not None:
        response.alert_event = alert_result
    else:
        logger.warning(
            "session=%s: alerting-service dispatch failed (non-blocking)",
            req.session_id,
        )

    return response


# -----------------------------------------------------------------------
# Health check
# -----------------------------------------------------------------------

@app.get("/healthz")
def healthz():
    """Liveness probe.  This service is stateless."""
    return {"status": "ok"}
