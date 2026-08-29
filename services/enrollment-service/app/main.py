"""
Enrollment service — thin FastAPI wrapper.

The wrapper (this file) is boilerplate and can be safely regenerated or
extended by an AI coding tool. The logic it wraps (enrollment.py) is not —
see docs/DESIGN.md section 6.

Enrollment via inbound phone call is explicitly NOT supported as a flow
here — DESIGN.md §4.2 designates inbound calls as an untrusted channel.
"""

import base64
from fastapi import Depends, FastAPI, HTTPException, Path
from pydantic import BaseModel

from dependencies import (
    ActorContext,
    get_enrollment_service,
    require_tenant_admin,
)
from enrollment import (
    AlreadyRevokedError,
    AuthorizationError,
    EnrollmentError,
    EnrollmentService,
    LivenessCheckFailedError,
    MIN_SESSIONS_REQUIRED,
    NotEnrolledError,
    SameDaySessionError,
)
from models import (
    AuditEntryOut,
    AuditLogResponse,
    EnrollmentStatus,
    RevokeRequest,
    RevokeResponse,
    StartEnrollmentRequest,
    StartEnrollmentResponse,
    SubmitSessionRequest,
    SubmitSessionResponse,
    VoiceprintStatusResponse,
)

app = FastAPI(title="enrollment-service", version="0.1.0")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post(
    "/v1/tenants/{tenant_id}/enroll",
    response_model=StartEnrollmentResponse,
)
def start_enrollment(
    tenant_id: str,
    req: StartEnrollmentRequest,
    actor: ActorContext = Depends(require_tenant_admin),
    svc: EnrollmentService = Depends(get_enrollment_service),
):
    """Start enrollment for a subject. Requires tenant_admin role."""
    # Self-enrollment check at API layer
    if actor.actor_id == req.subject_id:
        raise HTTPException(
            status_code=403,
            detail=(
                "Self-enrollment is not permitted. Enrollment must be "
                "initiated by a tenant admin, not the person being enrolled."
            ),
        )
    try:
        voiceprint, challenge = svc.start_enrollment(
            tenant_id=tenant_id,
            subject_id=req.subject_id,
            actor_id=actor.actor_id,
            actor_role=actor.actor_role,
        )
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=e.message)

    return StartEnrollmentResponse(
        voiceprint_id=voiceprint.voiceprint_id,
        status=voiceprint.status,
        challenge_phrase=challenge,
        message=(
            f"Enrollment initiated. Complete {MIN_SESSIONS_REQUIRED} "
            f"capture sessions on different calendar days."
        ),
    )


@app.post(
    "/v1/tenants/{tenant_id}/subjects/{subject_id}/session",
    response_model=SubmitSessionResponse,
)
def submit_session(
    tenant_id: str,
    subject_id: str,
    req: SubmitSessionRequest,
    actor: ActorContext = Depends(require_tenant_admin),
    svc: EnrollmentService = Depends(get_enrollment_service),
):
    """Submit a capture session. Requires tenant_admin role."""
    if actor.actor_id == subject_id:
        raise HTTPException(
            status_code=403,
            detail=(
                "Self-enrollment is not permitted. Enrollment must be "
                "initiated by a tenant admin, not the person being enrolled."
            ),
        )

    # Decode base64 audio — used only to extract embedding, never stored.
    try:
        audio_bytes = base64.b64decode(req.audio_data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 audio data")

    try:
        voiceprint, next_challenge = svc.submit_session(
            tenant_id=tenant_id,
            subject_id=subject_id,
            audio_bytes=audio_bytes,
            challenge_phrase=req.challenge_phrase,
            actor_id=actor.actor_id,
            actor_role=actor.actor_role,
        )
    except SameDaySessionError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except LivenessCheckFailedError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except NotEnrolledError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=e.message)

    remaining = max(0, MIN_SESSIONS_REQUIRED - voiceprint.sessions_completed)

    if voiceprint.status == EnrollmentStatus.ENROLLED:
        message = "Enrollment complete. Voiceprint is now active."
    else:
        message = (
            f"Session recorded. {remaining} more session(s) required "
            f"on different calendar day(s)."
        )

    return SubmitSessionResponse(
        session_id=str(voiceprint.voiceprint_id),  # session tracked via voiceprint
        status=voiceprint.status,
        sessions_completed=voiceprint.sessions_completed,
        sessions_remaining=remaining,
        next_challenge_phrase=next_challenge,
        message=message,
    )


# ⚠️ FLAGGED FOR MANUAL REVIEW — compliance-relevant endpoint.
# This endpoint triggers voiceprint revocation with an immutable audit
# trail. Do not auto-merge changes to this route.
@app.post(
    "/v1/tenants/{tenant_id}/subjects/{subject_id}/revoke",
    response_model=RevokeResponse,
)
def revoke_voiceprint(
    tenant_id: str,
    subject_id: str,
    req: RevokeRequest,
    actor: ActorContext = Depends(require_tenant_admin),
    svc: EnrollmentService = Depends(get_enrollment_service),
):
    """
    Revoke an enrolled voiceprint. Requires tenant_admin role.

    ⚠️ Compliance-relevant: writes an immutable audit record.
    Flagged for manual review before merge.
    """
    try:
        voiceprint = svc.revoke_voiceprint(
            tenant_id=tenant_id,
            subject_id=subject_id,
            reason_code=req.reason_code,
            reason_detail=req.reason_detail,
            actor_id=actor.actor_id,
            actor_role=actor.actor_role,
        )
    except NotEnrolledError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except AlreadyRevokedError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=e.message)

    return RevokeResponse(
        voiceprint_id=voiceprint.voiceprint_id,
        status=voiceprint.status,
        revoked_at=voiceprint.revoked_at.isoformat() if voiceprint.revoked_at else "",
        message="Voiceprint revoked. Audit log entry created.",
    )


@app.get(
    "/v1/tenants/{tenant_id}/subjects/{subject_id}/status",
    response_model=VoiceprintStatusResponse,
)
def get_status(
    tenant_id: str,
    subject_id: str,
    svc: EnrollmentService = Depends(get_enrollment_service),
):
    """Get enrollment status for a subject. No admin role required for reads."""
    voiceprint = svc.get_status(tenant_id, subject_id)
    if voiceprint is None:
        return VoiceprintStatusResponse(
            status=EnrollmentStatus.NOT_ENROLLED,
        )

    remaining = max(0, MIN_SESSIONS_REQUIRED - voiceprint.sessions_completed)
    return VoiceprintStatusResponse(
        voiceprint_id=voiceprint.voiceprint_id,
        status=voiceprint.status,
        version=voiceprint.version,
        sessions_completed=voiceprint.sessions_completed,
        sessions_remaining=remaining,
        enrolled_at=(
            voiceprint.updated_at.isoformat()
            if voiceprint.status == EnrollmentStatus.ENROLLED else None
        ),
        revoked_at=(
            voiceprint.revoked_at.isoformat()
            if voiceprint.revoked_at else None
        ),
    )


class MatchSpeakerRequest(BaseModel):
    live_embedding: list[float]


@app.post("/v1/tenants/{tenant_id}/subjects/{subject_id}/match")
def match_speaker_route(
    tenant_id: str,
    subject_id: str,
    req: MatchSpeakerRequest,
    svc: EnrollmentService = Depends(get_enrollment_service),
):
    """Compare a live embedding vector against enrolled voiceprint vectors."""
    return svc.match_speaker(tenant_id, subject_id, req.live_embedding)


@app.get(
    "/v1/tenants/{tenant_id}/subjects/{subject_id}/audit",
    response_model=AuditLogResponse,
)
def get_audit_log(
    tenant_id: str,
    subject_id: str,
    actor: ActorContext = Depends(require_tenant_admin),
    svc: EnrollmentService = Depends(get_enrollment_service),
):
    """Get the audit log for a subject. Requires tenant_admin role."""
    entries = svc.get_audit_log(tenant_id, subject_id)
    return AuditLogResponse(
        entries=[
            AuditEntryOut(
                entry_id=e.entry_id,
                action=e.action,
                actor_id=e.actor_id,
                actor_role=e.actor_role,
                timestamp=e.timestamp.isoformat(),
                detail=e.detail,
            )
            for e in entries
        ]
    )


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
