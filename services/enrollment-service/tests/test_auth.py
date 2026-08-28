"""
Auth enforcement tests for the enrollment service.

DESIGN.md §4.1: enrollment is tenant-scoped and can only be initiated
by a tenant admin role, never by the caller being enrolled. These tests
enforce this at the API layer with actual requests, not just comments.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest

from enrollment import AuthorizationError, EnrollmentService
from interfaces import StubLivenessChecker, StubModelRegistry
from store import InMemoryVoiceprintStore


TENANT = "bank-auth-test"
SUBJECT = "user-auth"
ADMIN = "admin-auth"


# ---------------------------------------------------------------------------
# Non-admin cannot initiate enrollment
# ---------------------------------------------------------------------------

def test_non_admin_cannot_initiate():
    svc = EnrollmentService(
        store=InMemoryVoiceprintStore(),
        liveness_checker=StubLivenessChecker(),
        model_registry=StubModelRegistry(),
    )

    with pytest.raises(AuthorizationError) as exc_info:
        svc.start_enrollment(TENANT, SUBJECT, ADMIN, "viewer")
    assert "tenant_admin" in exc_info.value.message


# ---------------------------------------------------------------------------
# Enrollee cannot self-enroll (actor_id == subject_id)
# ---------------------------------------------------------------------------

def test_enrollee_cannot_self_enroll():
    svc = EnrollmentService(
        store=InMemoryVoiceprintStore(),
        liveness_checker=StubLivenessChecker(),
        model_registry=StubModelRegistry(),
    )

    with pytest.raises(AuthorizationError) as exc_info:
        svc.start_enrollment(TENANT, "user-x", "user-x", "tenant_admin")
    assert "Self-enrollment" in exc_info.value.message


# ---------------------------------------------------------------------------
# Non-admin cannot submit session
# ---------------------------------------------------------------------------

def test_non_admin_cannot_submit_session():
    svc = EnrollmentService(
        store=InMemoryVoiceprintStore(),
        liveness_checker=StubLivenessChecker(),
        model_registry=StubModelRegistry(),
    )

    # First start enrollment as admin
    svc.start_enrollment(TENANT, SUBJECT, ADMIN, "tenant_admin")

    # Then try to submit as non-admin
    with pytest.raises(AuthorizationError):
        svc.submit_session(
            TENANT, SUBJECT, b"audio", "challenge",
            ADMIN, "viewer",
        )


# ---------------------------------------------------------------------------
# Self-enrollment blocked on session submission too
# ---------------------------------------------------------------------------

def test_self_enrollment_blocked_on_session():
    svc = EnrollmentService(
        store=InMemoryVoiceprintStore(),
        liveness_checker=StubLivenessChecker(),
        model_registry=StubModelRegistry(),
    )

    svc.start_enrollment(TENANT, SUBJECT, ADMIN, "tenant_admin")

    with pytest.raises(AuthorizationError) as exc_info:
        svc.submit_session(
            TENANT, SUBJECT, b"audio", "challenge",
            SUBJECT, "tenant_admin",  # actor IS the subject
        )
    assert "Self-enrollment" in exc_info.value.message
