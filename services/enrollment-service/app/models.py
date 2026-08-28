"""
API-layer Pydantic models for the enrollment service.

These are the HTTP request/response shapes. Internal domain objects
(Voiceprint, CaptureSession, AuditLogEntry) are dataclasses defined
in enrollment.py — this separation keeps the API contract independent
of the domain representation.

DESIGN.md §7: no model here has a raw_audio field. Embedding vectors
only.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


# -----------------------------------------------------------------------
# Shared enum — used by both API layer (this file) and domain layer
# (enrollment.py). Mirrors proto/risk_assessment.proto EnrollmentStatus.
# -----------------------------------------------------------------------

class EnrollmentStatus(str, Enum):
    NOT_ENROLLED = "NOT_ENROLLED"             # proto value 1
    ENROLLED = "ENROLLED"                     # proto value 2
    ENROLLMENT_REVOKED = "ENROLLMENT_REVOKED" # proto value 3


# -----------------------------------------------------------------------
# Request models
# -----------------------------------------------------------------------

class StartEnrollmentRequest(BaseModel):
    subject_id: str


class SubmitSessionRequest(BaseModel):
    audio_data: str       # base64-encoded audio (decoded in main.py, never stored)
    challenge_phrase: str


class RevokeRequest(BaseModel):
    reason_code: str
    reason_detail: str


# -----------------------------------------------------------------------
# Response models
# -----------------------------------------------------------------------

class StartEnrollmentResponse(BaseModel):
    voiceprint_id: str
    status: EnrollmentStatus
    challenge_phrase: str
    message: str


class SubmitSessionResponse(BaseModel):
    session_id: str
    status: EnrollmentStatus
    sessions_completed: int
    sessions_remaining: int
    next_challenge_phrase: Optional[str]
    message: str


class RevokeResponse(BaseModel):
    voiceprint_id: str
    status: EnrollmentStatus
    revoked_at: str
    message: str


class VoiceprintStatusResponse(BaseModel):
    status: EnrollmentStatus
    voiceprint_id: Optional[str] = None
    version: Optional[int] = None
    sessions_completed: Optional[int] = None
    sessions_remaining: Optional[int] = None
    enrolled_at: Optional[str] = None
    revoked_at: Optional[str] = None


class AuditEntryOut(BaseModel):
    entry_id: str
    action: str
    actor_id: str
    actor_role: str
    timestamp: str
    detail: str


class AuditLogResponse(BaseModel):
    entries: list[AuditEntryOut]
