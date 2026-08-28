"""
Liveness checker tests for the enrollment service.

DESIGN.md §4.2: enrollment requires a liveness/anti-replay check at
enrollment time (challenge phrase, not a static passphrase). These
tests verify:
- Challenge phrases are random, not fixed
- Challenge phrases contain multiple words
- Failed liveness rejects the session
- Failed liveness does not count toward the 3-session requirement
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest

from enrollment import (
    EnrollmentService,
    LivenessCheckFailedError,
)
from interfaces import StubLivenessChecker, StubModelRegistry
from challenge import generate_challenge
from store import InMemoryVoiceprintStore


TENANT = "bank-liveness-test"
SUBJECT = "user-liveness"
ADMIN = "admin-liveness"
ADMIN_ROLE = "tenant_admin"
AUDIO = b"audio-for-liveness-test"


# ---------------------------------------------------------------------------
# Challenge phrase is random, not fixed (DESIGN.md §4.2)
# ---------------------------------------------------------------------------

def test_challenge_is_random_not_fixed():
    phrases = {generate_challenge() for _ in range(20)}
    # With a large word list and 5 words per phrase, getting 20
    # identical phrases is astronomically unlikely. If we see fewer
    # than 2 distinct, the generator is broken.
    assert len(phrases) >= 2, (
        "Challenge phrases appear to be fixed, not random — "
        "DESIGN.md §4.2 requires a random challenge phrase"
    )


# ---------------------------------------------------------------------------
# Challenge phrase contains multiple words
# ---------------------------------------------------------------------------

def test_challenge_contains_multiple_words():
    phrase = generate_challenge()
    words = phrase.split()
    assert len(words) >= 3, (
        f"Challenge phrase has only {len(words)} word(s): '{phrase}'. "
        f"Expected at least 3 for sufficient entropy."
    )


# ---------------------------------------------------------------------------
# Failed liveness rejects session with LivenessCheckFailedError
# ---------------------------------------------------------------------------

def test_failed_liveness_rejects_session():
    svc = EnrollmentService(
        store=InMemoryVoiceprintStore(),
        liveness_checker=StubLivenessChecker(force_fail=True),
        model_registry=StubModelRegistry(),
    )

    vp, challenge = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)

    with pytest.raises(LivenessCheckFailedError) as exc_info:
        svc.submit_session(
            TENANT, SUBJECT, AUDIO, challenge, ADMIN, ADMIN_ROLE,
        )
    assert "liveness" in exc_info.value.message.lower()


# ---------------------------------------------------------------------------
# Failed liveness session not counted toward 3-session requirement
# ---------------------------------------------------------------------------

def test_failed_liveness_session_not_counted():
    store = InMemoryVoiceprintStore()
    svc = EnrollmentService(
        store=store,
        liveness_checker=StubLivenessChecker(force_fail=True),
        model_registry=StubModelRegistry(),
    )

    vp, challenge = svc.start_enrollment(TENANT, SUBJECT, ADMIN, ADMIN_ROLE)

    # Attempt a session that will fail liveness
    try:
        svc.submit_session(
            TENANT, SUBJECT, AUDIO, challenge, ADMIN, ADMIN_ROLE,
        )
    except LivenessCheckFailedError:
        pass

    # Verify session was NOT stored
    sessions = store.get_sessions(TENANT, SUBJECT)
    assert len(sessions) == 0, (
        "Failed liveness session was stored — it should have been "
        "rejected and NOT counted toward the 3-session requirement."
    )

    # Verify sessions_completed is still 0
    status = svc.get_status(TENANT, SUBJECT)
    assert status.sessions_completed == 0


# ---------------------------------------------------------------------------
# StubLivenessChecker passes by default, fails when force_fail=True
# ---------------------------------------------------------------------------

def test_stub_liveness_checker_default_passes():
    checker = StubLivenessChecker()
    result = checker.check([0.1, 0.2, 0.3], "test phrase")
    assert result.passed is True


def test_stub_liveness_checker_force_fail():
    checker = StubLivenessChecker(force_fail=True)
    result = checker.check([0.1, 0.2, 0.3], "test phrase")
    assert result.passed is False
