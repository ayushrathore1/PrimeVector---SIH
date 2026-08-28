"""
⚠️ COMPLIANCE: FLAG FOR REVIEW — revocation tests.

Tests for the voiceprint revocation code path. This is compliance-relevant:
revocation creates immutable audit records with full actor identity
(DESIGN.md §4.2, §4.8).

Do not auto-merge changes to this file or the code it tests.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from enrollment import (
    AlreadyRevokedError,
    EnrollmentService,
    MIN_SESSIONS_REQUIRED,
    NotEnrolledError,
)
from interfaces import StubLivenessChecker, StubModelRegistry
from models import EnrollmentStatus
from store import InMemoryVoiceprintStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TENANT = "bank-001"
SUBJECT = "cfo-jane"
ADMIN = "admin-bob"
ADMIN_ROLE = "tenant_admin"
AUDIO = b"fake-audio-data-for-revocation-tests"


def _day(offset: int) -> datetime:
    base = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(days=offset)


def _make_enrolled_service():
    """Create a service with a fully-enrolled voiceprint."""
    store = InMemoryVoiceprintStore()
    svc = EnrollmentService(
        store=store,
        liveness_checker=StubLivenessChecker(),
        model_registry=StubModelRegistry(),
    )
    vp, challenge = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)
    for day_offset in range(MIN_SESSIONS_REQUIRED):
        with patch("enrollment.datetime") as mock_dt:
            mock_dt.now.return_value = _day(day_offset)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            vp, challenge = svc.submit_session(
                TENANT, SUBJECT, AUDIO, challenge or "dummy",
                ADMIN, ADMIN_ROLE,
            )
    assert vp.status == EnrollmentStatus.ENROLLED
    return svc, store


# ---------------------------------------------------------------------------
# ⚠️ COMPLIANCE: revocation creates audit entry with actor identity
# ---------------------------------------------------------------------------

def test_revocation_creates_audit_entry():
    svc, store = _make_enrolled_service()

    svc.revoke_voiceprint(
        TENANT, SUBJECT, "SECURITY_INCIDENT", "Voice sample leaked",
        ADMIN, ADMIN_ROLE,
    )

    log = store.get_audit_log(TENANT, SUBJECT)
    revoke_entries = [e for e in log if e.action == "REVOKED"]
    assert len(revoke_entries) == 1

    entry = revoke_entries[0]
    assert entry.actor_id == ADMIN
    assert entry.actor_role == ADMIN_ROLE
    assert "SECURITY_INCIDENT" in entry.detail
    assert "Voice sample leaked" in entry.detail
    assert entry.timestamp is not None
    assert entry.timestamp.tzinfo == timezone.utc


# ---------------------------------------------------------------------------
# ⚠️ COMPLIANCE: revoked voiceprint has correct status
# ---------------------------------------------------------------------------

def test_revoked_voiceprint_status():
    svc, _ = _make_enrolled_service()

    vp = svc.revoke_voiceprint(
        TENANT, SUBJECT, "COMPROMISED", "Test detail",
        ADMIN, ADMIN_ROLE,
    )

    assert vp.status == EnrollmentStatus.ENROLLMENT_REVOKED
    assert vp.revoked_at is not None

    # Also verify via get_status
    status = svc.get_status(TENANT, SUBJECT)
    assert status.status == EnrollmentStatus.ENROLLMENT_REVOKED


# ---------------------------------------------------------------------------
# ⚠️ COMPLIANCE: audit entries are immutable (frozen dataclass)
# ---------------------------------------------------------------------------

def test_audit_log_entries_are_immutable():
    svc, store = _make_enrolled_service()

    svc.revoke_voiceprint(
        TENANT, SUBJECT, "COMPROMISED", "detail",
        ADMIN, ADMIN_ROLE,
    )

    log = store.get_audit_log(TENANT, SUBJECT)
    assert len(log) > 0

    entry = log[0]
    try:
        entry.detail = "TAMPERED"
        assert False, "Expected FrozenInstanceError — audit entries must be immutable"
    except AttributeError:
        pass  # Correct: frozen dataclass rejects mutation


# ---------------------------------------------------------------------------
# ⚠️ COMPLIANCE: all audit fields are present and valid
# ---------------------------------------------------------------------------

def test_audit_log_has_required_fields():
    svc, store = _make_enrolled_service()

    svc.revoke_voiceprint(
        TENANT, SUBJECT, "COMPROMISED", "detail",
        ADMIN, ADMIN_ROLE,
    )

    log = store.get_audit_log(TENANT, SUBJECT)
    for entry in log:
        assert entry.actor_id is not None
        assert entry.actor_role is not None
        assert entry.timestamp is not None
        assert entry.timestamp.tzinfo == timezone.utc
        assert entry.action is not None
        assert entry.detail is not None
        assert entry.entry_id is not None


# ---------------------------------------------------------------------------
# Cannot revoke an already-revoked voiceprint
# ---------------------------------------------------------------------------

def test_revocation_only_for_enrolled():
    svc, _ = _make_enrolled_service()

    # First revocation succeeds
    svc.revoke_voiceprint(
        TENANT, SUBJECT, "TEST", "First",
        ADMIN, ADMIN_ROLE,
    )

    # Second revocation fails
    with pytest.raises(AlreadyRevokedError):
        svc.revoke_voiceprint(
            TENANT, SUBJECT, "TEST", "Second",
            ADMIN, ADMIN_ROLE,
        )


# ---------------------------------------------------------------------------
# Cannot revoke a NOT_ENROLLED voiceprint
# ---------------------------------------------------------------------------

def test_cannot_revoke_not_enrolled():
    store = InMemoryVoiceprintStore()
    svc = EnrollmentService(
        store=store,
        liveness_checker=StubLivenessChecker(),
        model_registry=StubModelRegistry(),
    )
    # Initiate but don't complete enrollment
    svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)

    with pytest.raises(NotEnrolledError):
        svc.revoke_voiceprint(
            TENANT, SUBJECT, "TEST", "Should fail",
            ADMIN, ADMIN_ROLE,
        )
