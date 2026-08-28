"""
Voice Integrity Python SDK (voiceintegrity.v1)

Maps 1:1 to proto/risk_assessment.proto data structures.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Optional


class EnrollmentStatus(str, Enum):
    """
    Enrollment status of the speaker.
    Mirrors voiceintegrity.v1.EnrollmentStatus enum.
    """
    ENROLLMENT_STATUS_UNSPECIFIED = "ENROLLMENT_STATUS_UNSPECIFIED"
    NOT_ENROLLED = "NOT_ENROLLED"
    ENROLLED = "ENROLLED"
    ENROLLMENT_REVOKED = "ENROLLMENT_REVOKED"


class RecommendedAction(str, Enum):
    """
    Recommended action returned by the risk fusion engine.
    Mirrors voiceintegrity.v1.RecommendedAction enum.
    """
    ACTION_UNSPECIFIED = "ACTION_UNSPECIFIED"
    PROCEED = "PROCEED"
    RECOMMEND_CALLBACK_VERIFICATION = "RECOMMEND_CALLBACK_VERIFICATION"
    RECOMMEND_MFA_STEP_UP = "RECOMMEND_MFA_STEP_UP"
    RECOMMEND_SUPERVISOR_ESCALATION = "RECOMMEND_SUPERVISOR_ESCALATION"
    BLOCK_PENDING_VERIFICATION = "BLOCK_PENDING_VERIFICATION"


@dataclass
class RiskSignal:
    """
    One independent evidence signal feeding the fusion engine.
    Mirrors voiceintegrity.v1.RiskSignal message.

    Attributes:
        score (float): 0.0-1.0, higher = more suspicious
        confidence (float): 0.0-1.0, model's confidence in `score` itself
        available (bool): false if this signal could not be computed
        detail (str): short human-readable reason, for audit/UI
    """
    score: float = 0.0
    confidence: float = 0.0
    available: bool = True
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RiskSignal:
        return cls(
            score=float(data.get("score", 0.0)),
            confidence=float(data.get("confidence", 0.0)),
            available=bool(data.get("available", True)),
            detail=str(data.get("detail", "")),
        )


@dataclass
class RiskAssessmentRequest:
    """
    Request message for RiskFusionEngine.Assess.
    Mirrors voiceintegrity.v1.RiskAssessmentRequest message.

    Attributes:
        call_session_id (str): Unique call session identifier
        tenant_id (str): Tenant / organization identifier
        synthesis_signal (RiskSignal): Synthesis/spoof detection signal
        speaker_match_signal (RiskSignal): Speaker verification signal
        contextual_signal (RiskSignal): Contextual metadata risk signal
        enrollment_status (EnrollmentStatus): Enrollment status of subject
    """
    call_session_id: str
    tenant_id: str
    synthesis_signal: RiskSignal
    speaker_match_signal: RiskSignal
    contextual_signal: RiskSignal
    enrollment_status: EnrollmentStatus = EnrollmentStatus.ENROLLMENT_STATUS_UNSPECIFIED

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_session_id": self.call_session_id,
            "tenant_id": self.tenant_id,
            "synthesis_signal": self.synthesis_signal.to_dict(),
            "speaker_match_signal": self.speaker_match_signal.to_dict(),
            "contextual_signal": self.contextual_signal.to_dict(),
            "enrollment_status": (
                self.enrollment_status.value
                if isinstance(self.enrollment_status, EnrollmentStatus)
                else str(self.enrollment_status)
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RiskAssessmentRequest:
        status_val = data.get("enrollment_status", EnrollmentStatus.ENROLLMENT_STATUS_UNSPECIFIED)
        try:
            status = EnrollmentStatus(status_val)
        except ValueError:
            status = EnrollmentStatus.ENROLLMENT_STATUS_UNSPECIFIED

        return cls(
            call_session_id=str(data.get("call_session_id", "")),
            tenant_id=str(data.get("tenant_id", "")),
            synthesis_signal=RiskSignal.from_dict(data.get("synthesis_signal", {})),
            speaker_match_signal=RiskSignal.from_dict(data.get("speaker_match_signal", {})),
            contextual_signal=RiskSignal.from_dict(data.get("contextual_signal", {})),
            enrollment_status=status,
        )


@dataclass
class RiskAssessmentResponse:
    """
    Response message from RiskFusionEngine.Assess.
    Mirrors voiceintegrity.v1.RiskAssessmentResponse message.

    Attributes:
        call_session_id (str): Unique call session identifier
        risk_score (float): Fused risk score between 0.0 and 1.0
        confidence (float): Fused confidence between 0.0 and 1.0
        actions (list[RecommendedAction]): Ordered list of recommended actions
        explanation (str): Human-readable reason built from contributing signals
        evaluated_at (str): ISO-8601 timestamp string
        degraded (bool): True if evaluated under partial-signal/fail-safe mode
    """
    call_session_id: str
    risk_score: float
    confidence: float
    actions: list[RecommendedAction]
    explanation: str
    evaluated_at: str
    degraded: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RiskAssessmentResponse:
        raw_actions = data.get("actions", [])
        actions: list[RecommendedAction] = []
        for a in raw_actions:
            try:
                actions.append(RecommendedAction(a))
            except ValueError:
                actions.append(RecommendedAction.ACTION_UNSPECIFIED)

        return cls(
            call_session_id=str(data.get("call_session_id", "")),
            risk_score=float(data.get("risk_score", 0.0)),
            confidence=float(data.get("confidence", 0.0)),
            actions=actions,
            explanation=str(data.get("explanation", "")),
            evaluated_at=str(data.get("evaluated_at", "")),
            degraded=bool(data.get("degraded", False)),
        )
