"""
Tests for the enrollment domain logic.

These test the business rules from DESIGN.md §4.1–4.2:
- Multi-session requirement (≥3 sessions on different days)
- Same-day rejection
- Liveness check gating
- Voiceprint versioning after revocation
- Revocation audit trail
- Challenge phrase randomness

Tests operate at the EnrollmentService layer (not HTTP), testing the
domain invariants directly. API-layer tests are in test_api.py.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from datetime import date, datetime, timezone, timedelta
from unittest.mock import patch

from enrollment import (
    EnrollmentService,
    LivenessCheckFailedError,
    MIN_SESSIONS_REQUIRED,
    SameDaySessionError,
    AuthorizationError,
    AlreadyRevokedError,
)
from interfaces import (
    StubLivenessChecker,
    StubModelRegistry,
    LivenessResult,
)
from models import EnrollmentStatus
from store import InMemoryVoiceprintStore
from challenge import generate_challenge


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(*, force_liveness_fail: bool = False) -> EnrollmentService:
    return EnrollmentService(
        store=InMemoryVoiceprintStore(),
        liveness_checker=StubLivenessChecker(force_fail=force_liveness_fail),
        model_registry=StubModelRegistry(),
    )


def _make_service_with_store(
    *, force_liveness_fail: bool = False,
) -> tuple[EnrollmentService, InMemoryVoiceprintStore]:
    store = InMemoryVoiceprintStore()
    svc = EnrollmentService(
        store=store,
        liveness_checker=StubLivenessChecker(force_fail=force_liveness_fail),
        model_registry=StubModelRegistry(),
    )
    return svc, store


TENANT = "bank-001"
SUBJECT = "cfo-jane"
ADMIN = "admin-bob"
ADMIN_ROLE = "tenant_admin"
AUDIO = b"fake-audio-data-for-testing"


def _day(offset: int) -> datetime:
    """Return a UTC datetime `offset` days from a fixed base date."""
    base = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(days=offset)


# ---------------------------------------------------------------------------
# Test: enrollment requires 3 sessions on different days
# ---------------------------------------------------------------------------

def test_enrollment_requires_three_sessions():
    svc = _make_service()

    vp, challenge = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)
    assert vp.status == EnrollmentStatus.NOT_ENROLLED
    assert vp.sessions_completed == 0

    # Submit 2 sessions on different days — still not enrolled
    for day_offset in range(2):
        with patch("enrollment.datetime") as mock_dt:
            mock_dt.now.return_value = _day(day_offset)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            vp, next_ch = svc.submit_session(
                TENANT, SUBJECT, AUDIO, challenge, ADMIN, ADMIN_ROLE,
            )
            challenge = next_ch or challenge

    assert vp.status == EnrollmentStatus.NOT_ENROLLED
    assert vp.sessions_completed == 2

    # 3rd session on a different day — now enrolled
    with patch("enrollment.datetime") as mock_dt:
        mock_dt.now.return_value = _day(2)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        vp, next_ch = svc.submit_session(
            TENANT, SUBJECT, AUDIO, challenge, ADMIN, ADMIN_ROLE,
        )

    assert vp.status == EnrollmentStatus.ENROLLED
    assert vp.sessions_completed == 3
    assert next_ch is None  # no more sessions needed


# ---------------------------------------------------------------------------
# Test: same-day session is rejected
# ---------------------------------------------------------------------------

def test_same_day_session_rejected():
    svc = _make_service()

    vp, challenge = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)

    fixed_time = _day(0)
    with patch("enrollment.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_time
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        svc.submit_session(TENANT, SUBJECT, AUDIO, challenge, ADMIN, ADMIN_ROLE)

    # Second submission on same day — should fail
    same_day_later = fixed_time + timedelta(hours=5)
    with patch("enrollment.datetime") as mock_dt:
        mock_dt.now.return_value = same_day_later
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        try:
            svc.submit_session(TENANT, SUBJECT, AUDIO, challenge, ADMIN, ADMIN_ROLE)
            assert False, "Expected SameDaySessionError"
        except SameDaySessionError:
            pass

    # Verify session count did not increase
    status = svc.get_status(TENANT, SUBJECT)
    assert status.sessions_completed == 1


# ---------------------------------------------------------------------------
# Test: liveness failure rejects session
# ---------------------------------------------------------------------------

def test_liveness_failure_rejects_session():
    svc = _make_service(force_liveness_fail=True)

    vp, challenge = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)

    try:
        svc.submit_session(TENANT, SUBJECT, AUDIO, challenge, ADMIN, ADMIN_ROLE)
        assert False, "Expected LivenessCheckFailedError"
    except LivenessCheckFailedError:
        pass


# ---------------------------------------------------------------------------
# Test: liveness failure does not count toward requirement
# ---------------------------------------------------------------------------

def test_liveness_failure_does_not_count_toward_requirement():
    svc, store = _make_service_with_store(force_liveness_fail=True)

    vp, challenge = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)

    # Attempt a session that will fail liveness
    try:
        svc.submit_session(TENANT, SUBJECT, AUDIO, challenge, ADMIN, ADMIN_ROLE)
    except LivenessCheckFailedError:
        pass

    status = svc.get_status(TENANT, SUBJECT)
    assert status.sessions_completed == 0
    assert status.status == EnrollmentStatus.NOT_ENROLLED

    # Verify no sessions were persisted
    sessions = store.get_sessions(TENANT, SUBJECT)
    assert len(sessions) == 0


# ---------------------------------------------------------------------------
# Test: challenge phrase is random, not fixed
# ---------------------------------------------------------------------------

def test_challenge_phrase_is_random_not_fixed():
    phrases = {generate_challenge() for _ in range(20)}
    # With 60^5 possible phrases, getting 20 identical ones is
    # astronomically unlikely — if we see fewer than 2 distinct,
    # something is broken.
    assert len(phrases) >= 2


# ---------------------------------------------------------------------------
# Test: voiceprint versioning after revocation + re-enrollment
# ---------------------------------------------------------------------------

def test_voiceprint_versioning():
    svc = _make_service()

    # Enroll fully
    vp, challenge = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)
    assert vp.version == 1

    for day_offset in range(MIN_SESSIONS_REQUIRED):
        with patch("enrollment.datetime") as mock_dt:
            mock_dt.now.return_value = _day(day_offset)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            vp, challenge = svc.submit_session(
                TENANT, SUBJECT, AUDIO, challenge or "dummy", ADMIN, ADMIN_ROLE,
            )

    assert vp.status == EnrollmentStatus.ENROLLED
    assert vp.version == 1

    # Revoke
    vp = svc.revoke_voiceprint(
        TENANT, SUBJECT, "COMPROMISED", "Key person left", ADMIN, ADMIN_ROLE,
    )
    assert vp.status == EnrollmentStatus.ENROLLMENT_REVOKED
    assert vp.version == 1

    # Re-enroll — version should increment
    vp2, _ = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)
    assert vp2.version == 2
    assert vp2.status == EnrollmentStatus.NOT_ENROLLED


# ---------------------------------------------------------------------------
# Test: revocation creates audit entry with actor identity
# ---------------------------------------------------------------------------

def test_revocation_creates_audit_entry():
    svc, store = _make_service_with_store()

    # Start + complete enrollment
    vp, challenge = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)
    for day_offset in range(MIN_SESSIONS_REQUIRED):
        with patch("enrollment.datetime") as mock_dt:
            mock_dt.now.return_value = _day(day_offset)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            vp, challenge = svc.submit_session(
                TENANT, SUBJECT, AUDIO, challenge or "dummy", ADMIN, ADMIN_ROLE,
            )

    assert vp.status == EnrollmentStatus.ENROLLED

    # Revoke
    svc.revoke_voiceprint(
        TENANT, SUBJECT, "SECURITY_INCIDENT", "Voice sample leaked", ADMIN, ADMIN_ROLE,
    )

    # Check audit log
    log = store.get_audit_log(TENANT, SUBJECT)
    revoke_entries = [e for e in log if e.action == "REVOKED"]
    assert len(revoke_entries) == 1

    entry = revoke_entries[0]
    assert entry.actor_id == ADMIN
    assert entry.actor_role == ADMIN_ROLE
    assert "SECURITY_INCIDENT" in entry.detail
    assert "Voice sample leaked" in entry.detail
    assert entry.timestamp is not None


# ---------------------------------------------------------------------------
# Test: audit entry is immutable (frozen dataclass)
# ---------------------------------------------------------------------------

def test_revocation_audit_entry_is_immutable():
    svc, store = _make_service_with_store()

    vp, challenge = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)
    log = store.get_audit_log(TENANT, SUBJECT)
    assert len(log) >= 1

    entry = log[0]
    try:
        entry.detail = "TAMPERED"
        assert False, "Expected FrozenInstanceError"
    except AttributeError:
        pass  # Correct: frozen dataclass rejects mutation


# ---------------------------------------------------------------------------
# Test: enrollment status transitions
# ---------------------------------------------------------------------------

def test_enrollment_status_transitions():
    svc = _make_service()

    # NOT_ENROLLED initially
    assert svc.get_status(TENANT, SUBJECT) is None

    vp, challenge = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)
    assert vp.status == EnrollmentStatus.NOT_ENROLLED

    # Complete enrollment → ENROLLED
    for day_offset in range(MIN_SESSIONS_REQUIRED):
        with patch("enrollment.datetime") as mock_dt:
            mock_dt.now.return_value = _day(day_offset)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            vp, challenge = svc.submit_session(
                TENANT, SUBJECT, AUDIO, challenge or "dummy", ADMIN, ADMIN_ROLE,
            )
    assert vp.status == EnrollmentStatus.ENROLLED

    # Revoke → ENROLLMENT_REVOKED
    vp = svc.revoke_voiceprint(
        TENANT, SUBJECT, "TEST", "Testing transitions", ADMIN, ADMIN_ROLE,
    )
    assert vp.status == EnrollmentStatus.ENROLLMENT_REVOKED

    # Re-enroll → NOT_ENROLLED (version 2)
    vp2, _ = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)
    assert vp2.status == EnrollmentStatus.NOT_ENROLLED
    assert vp2.version == 2


# ---------------------------------------------------------------------------
# Test: cannot revoke an already-revoked voiceprint
# ---------------------------------------------------------------------------

def test_double_revoke_rejected():
    svc = _make_service()

    vp, challenge = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)
    for day_offset in range(MIN_SESSIONS_REQUIRED):
        with patch("enrollment.datetime") as mock_dt:
            mock_dt.now.return_value = _day(day_offset)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            vp, challenge = svc.submit_session(
                TENANT, SUBJECT, AUDIO, challenge or "dummy", ADMIN, ADMIN_ROLE,
            )

    svc.revoke_voiceprint(TENANT, SUBJECT, "TEST", "First", ADMIN, ADMIN_ROLE)

    try:
        svc.revoke_voiceprint(TENANT, SUBJECT, "TEST", "Second", ADMIN, ADMIN_ROLE)
        assert False, "Expected AlreadyRevokedError"
    except AlreadyRevokedError:
        pass


# ---------------------------------------------------------------------------
# Test: self-enrollment is forbidden
# ---------------------------------------------------------------------------

def test_self_enrollment_forbidden():
    svc = _make_service()

    try:
        svc.start_enrollment(TENANT, "user-x", "user-x", ADMIN_ROLE)
        assert False, "Expected AuthorizationError"
    except AuthorizationError as e:
        assert "Self-enrollment" in e.message


# ---------------------------------------------------------------------------
# Test: non-admin cannot enroll
# ---------------------------------------------------------------------------

def test_non_admin_cannot_enroll():
    svc = _make_service()

    try:
        svc.start_enrollment(TENANT, SUBJECT, ADMIN, "viewer")
        assert False, "Expected AuthorizationError"
    except AuthorizationError as e:
        assert "tenant_admin" in e.message
