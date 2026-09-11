"""
Async HTTP client layer for downstream microservice calls.

Each method corresponds to one step of the orchestration pipeline and
returns either a parsed Pydantic model or ``None`` if the call failed.

DESIGN INVARIANTS:
  - Timeout per downstream call: 5 s (configurable via DOWNSTREAM_TIMEOUT_S).
  - On ANY failure (timeout, HTTP error, decode error) the method returns
    ``None`` — callers MUST treat ``None`` as "signal unavailable" and
    switch the pipeline into degraded mode.  We NEVER default a missing
    signal to risk_score=0.0 (fail-safe, not fail-open).
  - Audio bytes are passed through as base64 strings and are never
    written to disk or persisted in any attribute beyond the call scope.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional, Tuple

import httpx

from models import (
    EventAcceptedResponse,
    ExtractionRequest,
    ExtractionResponse,
    EvaluateRequest,
    PolicyDecision,
    PolicyDecisionEventIn,
    RiskAssessmentInput,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    SignalIn,
    SpoofDetectionRequest,
    SynthesisSignalResponse,
    VoiceprintStatusResponse,
)

logger = logging.getLogger(__name__)

# Default service base URLs — overridable via environment or constructor.
DEFAULT_FEATURE_EXTRACTION_URL = os.environ.get("FEATURE_EXTRACTION_URL", "http://localhost:8001")
DEFAULT_SPOOF_DETECTION_URL = os.environ.get("SPOOF_DETECTION_URL", "http://localhost:8002")
DEFAULT_ENROLLMENT_URL = os.environ.get("ENROLLMENT_URL", "http://localhost:8003")
DEFAULT_RISK_FUSION_URL = os.environ.get("RISK_FUSION_URL", "http://localhost:8000")
DEFAULT_POLICY_ENGINE_URL = os.environ.get("POLICY_ENGINE_URL", "http://localhost:8004")
DEFAULT_ALERTING_URL = os.environ.get("ALERTING_URL", "http://localhost:8005")

DOWNSTREAM_TIMEOUT_S = 5.0


class PipelineClient:
    """Thin async wrapper around httpx for downstream service calls."""

    def __init__(
        self,
        *,
        feature_extraction_url: str = DEFAULT_FEATURE_EXTRACTION_URL,
        spoof_detection_url: str = DEFAULT_SPOOF_DETECTION_URL,
        enrollment_url: str = DEFAULT_ENROLLMENT_URL,
        risk_fusion_url: str = DEFAULT_RISK_FUSION_URL,
        policy_engine_url: str = DEFAULT_POLICY_ENGINE_URL,
        alerting_url: str = DEFAULT_ALERTING_URL,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.feature_extraction_url = feature_extraction_url
        self.spoof_detection_url = spoof_detection_url
        self.enrollment_url = enrollment_url
        self.risk_fusion_url = risk_fusion_url
        self.policy_engine_url = policy_engine_url
        self.alerting_url = alerting_url
        # Allow injection of a pre-configured AsyncClient (for testing).
        self._client = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(DOWNSTREAM_TIMEOUT_S),
        )

    async def close(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Step 1: Feature extraction
    # ------------------------------------------------------------------

    async def extract_features(
        self,
        request_id: str,
        tenant_id: str,
        audio_pcm_base64: str,
        sample_rate_hz: int = 16000,
        channels: int = 1,
    ) -> Optional[ExtractionResponse]:
        """POST /v1/extract -> ExtractionResponse or None on failure."""
        payload = ExtractionRequest(
            request_id=request_id,
            tenant_id=tenant_id,
            audio_bytes=audio_pcm_base64,
            sample_rate_hz=sample_rate_hz,
            channels=channels,
        )
        try:
            resp = await self._client.post(
                f"{self.feature_extraction_url}/v1/extract",
                json=payload.model_dump(),
            )
            resp.raise_for_status()
            return ExtractionResponse.model_validate(resp.json())
        except Exception:
            logger.exception("feature-extraction-service call failed")
            return None

    # ------------------------------------------------------------------
    # Step 2a: Spoof detection
    # ------------------------------------------------------------------

    async def detect_spoof(
        self,
        call_session_id: str,
        tenant_id: str,
        audio_features: List[float],
        audio_pcm_base64: Optional[str] = None,
    ) -> Optional[SynthesisSignalResponse]:
        """POST /v1/detect -> SynthesisSignalResponse or None on failure.

        When audio_pcm_base64 is provided, the spoof-detection service
        uses the trained ResNet18+GRU+Attention model on a 128-band mel
        spectrogram computed from the raw audio.  The audio is decoded
        in-memory and immediately dereferenced (DESIGN.md section 7).
        """
        payload = SpoofDetectionRequest(
            call_session_id=call_session_id,
            tenant_id=tenant_id,
            audio_features=audio_features,
            audio_pcm_base64=audio_pcm_base64,
        )
        try:
            resp = await self._client.post(
                f"{self.spoof_detection_url}/v1/detect",
                json=payload.model_dump(),
            )
            resp.raise_for_status()
            return SynthesisSignalResponse.model_validate(resp.json())
        except Exception:
            logger.exception("spoof-detection-service call failed")
            return None

    # ------------------------------------------------------------------
    # Step 2b: Enrollment status check
    # ------------------------------------------------------------------

    async def get_enrollment_status(
        self,
        tenant_id: str,
        subject_id: str,
    ) -> Optional[VoiceprintStatusResponse]:
        """GET /v1/tenants/{tenant_id}/subjects/{subject_id}/status."""
        try:
            resp = await self._client.get(
                f"{self.enrollment_url}/v1/tenants/{tenant_id}"
                f"/subjects/{subject_id}/status",
            )
            resp.raise_for_status()
            return VoiceprintStatusResponse.model_validate(resp.json())
        except Exception:
            logger.exception("enrollment-service call failed")
            return None

    async def match_speaker(
        self,
        tenant_id: str,
        subject_id: str,
        live_embedding: List[float],
    ) -> Optional[SignalIn]:
        """POST /v1/tenants/{id}/subjects/{id}/match -> SignalIn or None."""
        try:
            resp = await self._client.post(
                f"{self.enrollment_url}/v1/tenants/{tenant_id}"
                f"/subjects/{subject_id}/match",
                json={"live_embedding": live_embedding},
            )
            resp.raise_for_status()
            data = resp.json()
            return SignalIn(
                score=data.get("score", 0.5),
                confidence=data.get("confidence", 0.0),
                available=data.get("available", False),
                detail=data.get("detail", ""),
            )
        except Exception:
            logger.exception("enrollment-service match call failed")
            return None

    # ------------------------------------------------------------------
    # Step 3: Risk fusion
    # ------------------------------------------------------------------

    async def assess_risk(
        self,
        call_session_id: str,
        tenant_id: str,
        synthesis_signal: SignalIn,
        speaker_match_signal: SignalIn,
        contextual_signal: SignalIn,
        content_risk_signal: Optional[SignalIn] = None,
    ) -> Optional[RiskAssessmentResponse]:
        """POST /v1/assess -> RiskAssessmentResponse or None on failure."""
        payload = RiskAssessmentRequest(
            call_session_id=call_session_id,
            tenant_id=tenant_id,
            synthesis_signal=synthesis_signal,
            speaker_match_signal=speaker_match_signal,
            contextual_signal=contextual_signal,
            content_risk_signal=content_risk_signal,
        )
        try:
            resp = await self._client.post(
                f"{self.risk_fusion_url}/v1/assess",
                json=payload.model_dump(),
            )
            resp.raise_for_status()
            return RiskAssessmentResponse.model_validate(resp.json())
        except Exception:
            logger.exception("risk-fusion-engine call failed")
            return None

    # ------------------------------------------------------------------
    # Step 4: Policy evaluation
    # ------------------------------------------------------------------

    async def evaluate_policy(
        self,
        tenant_id: str,
        assessment: RiskAssessmentResponse,
    ) -> Optional[PolicyDecision]:
        """POST /v1/evaluate -> PolicyDecision or None on failure."""
        payload = EvaluateRequest(
            tenant_id=tenant_id,
            assessment=RiskAssessmentInput(
                call_session_id=assessment.call_session_id,
                risk_score=assessment.risk_score,
                confidence=assessment.confidence,
                actions=assessment.actions,
                explanation=assessment.explanation,
                evaluated_at=assessment.evaluated_at,
                degraded=assessment.degraded,
            ),
        )
        try:
            resp = await self._client.post(
                f"{self.policy_engine_url}/v1/evaluate",
                json=payload.model_dump(),
            )
            resp.raise_for_status()
            return PolicyDecision.model_validate(resp.json())
        except Exception:
            logger.exception("policy-threshold-engine call failed")
            return None

    # ------------------------------------------------------------------
    # Step 5: Alert dispatch
    # ------------------------------------------------------------------

    async def dispatch_alert(
        self,
        event: PolicyDecisionEventIn,
    ) -> Optional[EventAcceptedResponse]:
        """POST /v1/events -> EventAcceptedResponse or None on failure."""
        try:
            resp = await self._client.post(
                f"{self.alerting_url}/v1/events",
                json=event.model_dump(),
            )
            resp.raise_for_status()
            return EventAcceptedResponse.model_validate(resp.json())
        except Exception:
            logger.exception("alerting-service call failed")
            return None
