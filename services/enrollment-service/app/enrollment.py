"""
Enrollment domain logic for the voice-integrity platform.

Implements DESIGN.md §4.1–4.2:
- Multi-session voiceprint enrollment (≥3 sessions, different UTC days)
- Same-day session rejection
- Liveness check gating (stubbed interface, wired control flow)
- Voiceprint versioning and revocation
- Actor-identity audit trail

This module is the enrollment equivalent of risk-fusion-engine/fusion.py:
every design decision here is a business/compliance decision, documented
inline. See docs/DESIGN.md section 6.

Enrollment via inbound phone call is explicitly NOT supported —
DESIGN.md §4.2 designates inbound calls as an untrusted channel.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, date
from typing import Optional

from models import EnrollmentStatus
from interfaces import LivenessChecker, ModelRegistry
from challenge import generate_challenge
from matcher import compute_speaker_match_signal

# The number of capture sessions on distinct calendar days required before
# a voiceprint is marked ENROLLED. This is a security parameter from
# DESIGN.md §4.2: requiring multiple sessions on different days makes it
# much harder for an attacker to poison enrollment with a single spoofed
# sample.
MIN_SESSIONS_REQUIRED = 3


# ---------------------------------------------------------------------------
# Error hierarchy — used by main.py to map to HTTP status codes
# ---------------------------------------------------------------------------

class EnrollmentError(Exception):
    """Base class for enrollment domain errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class SameDaySessionError(EnrollmentError):
    """Raised when a second session is submitted on the same UTC day."""
    pass


class LivenessCheckFailedError(EnrollmentError):
    """Raised when the liveness check rejects a capture session."""
    pass


class AuthorizationError(EnrollmentError):
    """Raised when the caller lacks the required role or attempts self-enrollment."""
    pass


class AlreadyRevokedError(EnrollmentError):
    """Raised when attempting to revoke an already-revoked voiceprint."""
    pass


class NotEnrolledError(EnrollmentError):
    """Raised when referencing a voiceprint/enrollment that does not exist."""
    pass


# ---------------------------------------------------------------------------
# Domain data objects
# ---------------------------------------------------------------------------

@dataclass
class Voiceprint:
    """
    Represents the enrollment state for a (tenant, subject) pair.

    DESIGN.md §7: this object stores ONLY embedding vectors, never raw
    audio. There is no audio field on this class, and tests assert this
    structurally.
    """
    voiceprint_id: str
    tenant_id: str
    subject_id: str
    status: str  # EnrollmentStatus value
    version: int
    sessions_completed: int = 0
    # DESIGN.md §7: raw audio is never persisted — only embeddings
    embedding_vectors: list = field(default_factory=list)
    created_at: datetime = None
    updated_at: datetime = None
    revoked_at: Optional[datetime] = None


@dataclass(frozen=True)
class CaptureSession:
    """
    Record of a single successful capture session.

    Only stored when liveness check passes — failed sessions are rejected
    and do NOT appear in the store (DESIGN.md §4.2).

    DESIGN.md §7: stores the embedding vector only, never raw audio.
    """
    session_id: str
    tenant_id: str
    subject_id: str
    captured_date: date
    embedding_vector: list
    challenge_phrase: str
    timestamp: datetime


@dataclass(frozen=True)
class AuditLogEntry:
    """
    Immutable audit record. Frozen to prevent post-hoc tampering.

    DESIGN.md §4.8: every action is logged with actor identity, required
    for bank compliance review.
    """
    entry_id: str
    tenant_id: str
    subject_id: str
    action: str
    actor_id: str
    actor_role: str
    timestamp: datetime
    detail: str


# ---------------------------------------------------------------------------
# Core service
# ---------------------------------------------------------------------------

class EnrollmentService:
    """
    Stateful enrollment workflow engine.

    Constructor dependencies are injected (store, liveness_checker,
    model_registry) so they can be swapped for stubs in tests and for
    real implementations in production.
    """

    def __init__(self, store, liveness_checker: LivenessChecker,
                 model_registry: ModelRegistry):
        self.store = store
        self.liveness = liveness_checker
        self.model_registry = model_registry

    # ---------------------------------------------------------------
    # Authorization guard (defense-in-depth, also checked at API layer)
    # ---------------------------------------------------------------

    @staticmethod
    def _check_auth(actor_id: str, actor_role: str,
                    subject_id: str | None = None) -> None:
        if actor_role != "tenant_admin":
            raise AuthorizationError(
                f"Only tenant_admin can perform this operation, "
                f"got role: {actor_role}"
            )
        if subject_id is not None and actor_id == subject_id:
            raise AuthorizationError(
                "Self-enrollment is not permitted. Enrollment must be "
                "initiated by a tenant admin, not the person being enrolled."
            )

    # ---------------------------------------------------------------
    # Start enrollment
    # ---------------------------------------------------------------

    def start_enrollment(
        self,
        tenant_id: str,
        subject_id: str,
        actor_id: str,
        actor_role: str,
    ) -> tuple[Voiceprint, str]:
        """
        Initiate enrollment for a subject. Returns (voiceprint, challenge_phrase).

        If a revoked voiceprint exists for this subject, the new voiceprint
        gets an incremented version number (DESIGN.md §4.2).
        """
        self._check_auth(actor_id, actor_role, subject_id)

        now = datetime.now(timezone.utc)

        # Check for existing voiceprint to determine version
        existing = self.store.get_voiceprint(tenant_id, subject_id)
        version = 1
        if existing is not None:
            if existing.status == EnrollmentStatus.ENROLLMENT_REVOKED:
                version = existing.version + 1
            elif existing.status == EnrollmentStatus.NOT_ENROLLED:
                # Re-starting a stalled enrollment — keep same version
                version = existing.version

        vp = Voiceprint(
            voiceprint_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            subject_id=subject_id,
            status=EnrollmentStatus.NOT_ENROLLED,
            version=version,
            sessions_completed=0,
            embedding_vectors=[],
            created_at=now,
            updated_at=now,
        )
        self.store.save_voiceprint(vp)

        challenge = generate_challenge()

        self.store.save_audit_entry(AuditLogEntry(
            entry_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            subject_id=subject_id,
            action="INITIATED",
            actor_id=actor_id,
            actor_role=actor_role,
            timestamp=now,
            detail=f"Enrollment initiated for subject {subject_id}",
        ))

        return vp, challenge

    # ---------------------------------------------------------------
    # Submit capture session
    # ---------------------------------------------------------------

    def submit_session(
        self,
        tenant_id: str,
        subject_id: str,
        audio_bytes: bytes,
        challenge_phrase: str,
        actor_id: str,
        actor_role: str,
    ) -> tuple[Voiceprint, str | None]:
        """
        Submit a capture session. Returns (updated voiceprint, next_challenge_or_None).

        Returns None as next_challenge when enrollment is complete (≥3 sessions
        on distinct days).

        DESIGN.md §4.1: rejects same-UTC-day duplicates.
        DESIGN.md §4.2: rejects if liveness check fails.
        DESIGN.md §7: raw audio is consumed here for embedding extraction
        and then discarded — never stored.
        """
        self._check_auth(actor_id, actor_role, subject_id)

        vp = self.store.get_voiceprint(tenant_id, subject_id)
        if vp is None:
            raise NotEnrolledError(
                f"No enrollment found for subject {subject_id}"
            )
        if vp.status == EnrollmentStatus.ENROLLED:
            raise EnrollmentError("Subject is already enrolled")
        if vp.status == EnrollmentStatus.ENROLLMENT_REVOKED:
            raise NotEnrolledError(
                "Voiceprint has been revoked. Start a new enrollment."
            )

        now = datetime.now(timezone.utc)
        today = now.date()

        # DESIGN.md §4.1: reject same-UTC-day session
        existing_sessions = self.store.get_sessions(tenant_id, subject_id)
        for s in existing_sessions:
            if s.captured_date == today:
                raise SameDaySessionError(
                    "Only one capture session allowed per calendar day (UTC). "
                    "Try again tomorrow."
                )

        # Extract embedding from audio (via ModelRegistry, DESIGN.md §4.3)
        model = self.model_registry.get_speaker_embedding_model()
        embedding = model.extract_embedding(audio_bytes)
        # DESIGN.md §7: audio_bytes is NOT stored — only the embedding.
        # The audio variable goes out of scope here; the caller (main.py)
        # also does not persist it.

        # DESIGN.md §4.2: liveness check with the challenge phrase
        liveness_result = self.liveness.check(embedding, challenge_phrase)
        if not liveness_result.passed:
            # Failed liveness does NOT count toward the 3-session requirement.
            # No session is stored. This is enforced by raising before save.
            raise LivenessCheckFailedError(
                f"Liveness check failed: {liveness_result.detail}"
            )

        # Liveness passed — store the session
        session = CaptureSession(
            session_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            subject_id=subject_id,
            captured_date=today,
            embedding_vector=embedding,
            challenge_phrase=challenge_phrase,
            timestamp=now,
        )
        self.store.save_session(session)

        # Re-read all sessions to count distinct days
        all_sessions = self.store.get_sessions(tenant_id, subject_id)
        distinct_days = len(set(s.captured_date for s in all_sessions))

        vp.sessions_completed = len(all_sessions)
        vp.embedding_vectors = [s.embedding_vector for s in all_sessions]
        vp.updated_at = now

        next_challenge = None
        if distinct_days >= MIN_SESSIONS_REQUIRED:
            vp.status = EnrollmentStatus.ENROLLED
        else:
            next_challenge = generate_challenge()

        self.store.save_voiceprint(vp)

        # Audit
        self.store.save_audit_entry(AuditLogEntry(
            entry_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            subject_id=subject_id,
            action="SESSION_CAPTURED",
            actor_id=actor_id,
            actor_role=actor_role,
            timestamp=now,
            detail=(
                f"Capture session recorded. "
                f"Total sessions: {vp.sessions_completed}, "
                f"distinct days: {distinct_days}"
            ),
        ))

        if vp.status == EnrollmentStatus.ENROLLED:
            self.store.save_audit_entry(AuditLogEntry(
                entry_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                subject_id=subject_id,
                action="ENROLLED",
                actor_id=actor_id,
                actor_role=actor_role,
                timestamp=now,
                detail=f"Enrollment complete. Version {vp.version}.",
            ))

        return vp, next_challenge

    # ---------------------------------------------------------------
    # Status query
    # ---------------------------------------------------------------

    def get_status(self, tenant_id: str, subject_id: str) -> Voiceprint | None:
        """Return the current voiceprint or None if no enrollment exists."""
        return self.store.get_voiceprint(tenant_id, subject_id)

    def match_speaker(
        self, tenant_id: str, subject_id: str, live_embedding: list[float],
    ) -> dict:
        """Compare a live_embedding vector against enrolled voiceprint vectors."""
        vp = self.get_status(tenant_id, subject_id)
        if vp is None or vp.status != EnrollmentStatus.ENROLLED:
            return compute_speaker_match_signal(live_embedding, [])
        return compute_speaker_match_signal(live_embedding, vp.embedding_vectors)

    # ---------------------------------------------------------------
    # ⚠️ COMPLIANCE: FLAG FOR REVIEW — revocation is compliance-relevant.
    # Do not auto-merge this code path. See DESIGN.md §4.2.
    # ---------------------------------------------------------------

    def revoke_voiceprint(
        self,
        tenant_id: str,
        subject_id: str,
        reason_code: str,
        reason_detail: str,
        actor_id: str,
        actor_role: str,
    ) -> Voiceprint:
        """
        Revoke an enrolled voiceprint.

        ⚠️ COMPLIANCE: FLAG FOR REVIEW — this is compliance-relevant.

        Creates an immutable audit log entry recording who revoked, when,
        and why (DESIGN.md §4.2, §4.8). The voiceprint can be re-enrolled
        afterward with an incremented version number.
        """
        self._check_auth(actor_id, actor_role)

        vp = self.store.get_voiceprint(tenant_id, subject_id)
        if vp is None:
            raise NotEnrolledError(
                f"No voiceprint found for subject {subject_id}"
            )
        if vp.status == EnrollmentStatus.ENROLLMENT_REVOKED:
            raise AlreadyRevokedError("Voiceprint is already revoked")
        if vp.status != EnrollmentStatus.ENROLLED:
            raise NotEnrolledError(
                "Can only revoke an ENROLLED voiceprint"
            )

        now = datetime.now(timezone.utc)
        vp.status = EnrollmentStatus.ENROLLMENT_REVOKED
        vp.revoked_at = now
        vp.updated_at = now
        self.store.save_voiceprint(vp)

        # ⚠️ COMPLIANCE: immutable audit record with full actor identity
        self.store.save_audit_entry(AuditLogEntry(
            entry_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            subject_id=subject_id,
            action="REVOKED",
            actor_id=actor_id,
            actor_role=actor_role,
            timestamp=now,
            detail=(
                f"Voiceprint revoked. "
                f"Reason: {reason_code} — {reason_detail}"
            ),
        ))

        return vp

    # ---------------------------------------------------------------
    # Audit log query
    # ---------------------------------------------------------------

    def get_audit_log(
        self, tenant_id: str, subject_id: str,
    ) -> list[AuditLogEntry]:
        """Return the full audit trail for a (tenant, subject) pair."""
        return self.store.get_audit_log(tenant_id, subject_id)
