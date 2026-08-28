"""
API-layer tests for enrollment service RBAC enforcement.

These tests verify that the FastAPI endpoints correctly enforce:
- tenant_admin role requirement (not just a comment — a test)
- Self-enrollment rejection (actor cannot enroll themselves)
- Missing actor headers rejection
- Full enrollment flow end-to-end

Uses FastAPI's TestClient (backed by httpx).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import base64
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Reset dependencies before importing the app to ensure test isolation
import dependencies
dependencies.reset_dependencies()

from main import app

client = TestClient(app)

TENANT = "bank-001"
SUBJECT = "cfo-jane"
ADMIN = "admin-bob"
AUDIO_B64 = base64.b64encode(b"fake-audio-for-testing").decode()


@pytest.fixture(autouse=True)
def _reset():
    """Reset all singletons between tests."""
    dependencies.reset_dependencies()


def _admin_headers(actor_id: str = ADMIN, role: str = "tenant_admin"):
    return {"X-Actor-Id": actor_id, "X-Actor-Role": role}


# ---------------------------------------------------------------------------
# Test: non-admin cannot start enrollment
# ---------------------------------------------------------------------------

def test_non_admin_cannot_start_enrollment():
    resp = client.post(
        f"/v1/tenants/{TENANT}/enroll",
        json={"subject_id": SUBJECT},
        headers=_admin_headers(role="viewer"),
    )
    assert resp.status_code == 403
    assert "tenant_admin" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Test: self-enrollment is rejected at the API layer
# ---------------------------------------------------------------------------

def test_self_enrollment_rejected():
    resp = client.post(
        f"/v1/tenants/{TENANT}/enroll",
        json={"subject_id": ADMIN},  # actor IS the subject
        headers=_admin_headers(actor_id=ADMIN),
    )
    assert resp.status_code == 403
    assert "Self-enrollment" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Test: missing actor headers are rejected
# ---------------------------------------------------------------------------

def test_missing_actor_headers_rejected():
    # No headers at all
    resp = client.post(
        f"/v1/tenants/{TENANT}/enroll",
        json={"subject_id": SUBJECT},
    )
    assert resp.status_code == 403


def test_missing_actor_role_rejected():
    resp = client.post(
        f"/v1/tenants/{TENANT}/enroll",
        json={"subject_id": SUBJECT},
        headers={"X-Actor-Id": ADMIN},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Test: admin can start enrollment and gets a challenge phrase
# ---------------------------------------------------------------------------

def test_admin_can_start_enrollment():
    resp = client.post(
        f"/v1/tenants/{TENANT}/enroll",
        json={"subject_id": SUBJECT},
        headers=_admin_headers(),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "NOT_ENROLLED"
    assert len(body["challenge_phrase"]) > 0
    assert body["voiceprint_id"] is not None


# ---------------------------------------------------------------------------
# Test: revoke requires admin role
# ---------------------------------------------------------------------------

def test_revoke_requires_admin():
    resp = client.post(
        f"/v1/tenants/{TENANT}/subjects/{SUBJECT}/revoke",
        json={"reason_code": "TEST", "reason_detail": "testing"},
        headers=_admin_headers(role="viewer"),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Test: self-enrollment rejected on session submission
# ---------------------------------------------------------------------------

def test_self_enrollment_rejected_on_session():
    resp = client.post(
        f"/v1/tenants/{TENANT}/subjects/{ADMIN}/session",
        json={"audio_data": AUDIO_B64, "challenge_phrase": "test phrase"},
        headers=_admin_headers(actor_id=ADMIN),
    )
    assert resp.status_code == 403
    assert "Self-enrollment" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Test: full enrollment flow (start → 3 sessions → ENROLLED)
# ---------------------------------------------------------------------------

def test_full_enrollment_flow():
    # Start enrollment
    resp = client.post(
        f"/v1/tenants/{TENANT}/enroll",
        json={"subject_id": SUBJECT},
        headers=_admin_headers(),
    )
    assert resp.status_code == 200
    challenge = resp.json()["challenge_phrase"]

    # Submit 3 sessions on different days
    base_time = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)

    for day_offset in range(3):
        mock_time = base_time + timedelta(days=day_offset)

        with patch("enrollment.datetime") as mock_dt:
            mock_dt.now.return_value = mock_time
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            resp = client.post(
                f"/v1/tenants/{TENANT}/subjects/{SUBJECT}/session",
                json={"audio_data": AUDIO_B64, "challenge_phrase": challenge},
                headers=_admin_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()

            if day_offset < 2:
                assert body["status"] == "NOT_ENROLLED"
                challenge = body.get("next_challenge_phrase", challenge)
            else:
                assert body["status"] == "ENROLLED"
                assert body["sessions_remaining"] == 0

    # Verify status
    resp = client.get(
        f"/v1/tenants/{TENANT}/subjects/{SUBJECT}/status",
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ENROLLED"
    assert resp.json()["version"] == 1
    assert resp.json()["sessions_completed"] == 3


# ---------------------------------------------------------------------------
# Test: same-day session returns 409
# ---------------------------------------------------------------------------

def test_same_day_session_returns_409():
    # Start enrollment
    resp = client.post(
        f"/v1/tenants/{TENANT}/enroll",
        json={"subject_id": SUBJECT},
        headers=_admin_headers(),
    )
    challenge = resp.json()["challenge_phrase"]

    fixed_time = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)

    # First session
    with patch("enrollment.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_time
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        resp = client.post(
            f"/v1/tenants/{TENANT}/subjects/{SUBJECT}/session",
            json={"audio_data": AUDIO_B64, "challenge_phrase": challenge},
            headers=_admin_headers(),
        )
        assert resp.status_code == 200

    # Second session same day — should be 409
    later_same_day = fixed_time + timedelta(hours=6)
    with patch("enrollment.datetime") as mock_dt:
        mock_dt.now.return_value = later_same_day
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        resp = client.post(
            f"/v1/tenants/{TENANT}/subjects/{SUBJECT}/session",
            json={"audio_data": AUDIO_B64, "challenge_phrase": challenge},
            headers=_admin_headers(),
        )
        assert resp.status_code == 409
        assert "calendar day" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test: liveness failure returns 422
# ---------------------------------------------------------------------------

def test_liveness_failure_returns_422():
    from interfaces import StubLivenessChecker
    dependencies.set_liveness_checker(StubLivenessChecker(force_fail=True))

    # Start enrollment
    resp = client.post(
        f"/v1/tenants/{TENANT}/enroll",
        json={"subject_id": SUBJECT},
        headers=_admin_headers(),
    )
    challenge = resp.json()["challenge_phrase"]

    # Submit session — should fail liveness
    resp = client.post(
        f"/v1/tenants/{TENANT}/subjects/{SUBJECT}/session",
        json={"audio_data": AUDIO_B64, "challenge_phrase": challenge},
        headers=_admin_headers(),
    )
    assert resp.status_code == 422
    assert "liveness" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test: healthz endpoint
# ---------------------------------------------------------------------------

def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
