"""
API integration tests for the policy-threshold-engine.

Tests the FastAPI endpoints using TestClient, covering:
- Evaluate endpoint returns correct PolicyDecision
- Admin endpoints enforce tenant_admin auth
- Policy updates take effect for subsequent evaluations
- Policy versioning stamps decisions correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from fastapi.testclient import TestClient

from main import app, _store, _audit_log


def _fresh_client():
    """
    Return a TestClient with a clean store/audit state.

    We clear the in-memory stores between tests to avoid cross-contamination.
    """
    _store._policies.clear()
    _audit_log._entries.clear()
    return TestClient(app)


def _make_assessment(risk_score: float = 0.5) -> dict:
    """Helper: build a valid RiskAssessmentInput dict."""
    return {
        "call_session_id": "call-001",
        "risk_score": risk_score,
        "confidence": 0.9,
        "actions": ["RECOMMEND_CALLBACK_VERIFICATION"],
        "explanation": "test explanation",
        "evaluated_at": "2026-01-01T00:00:00Z",
        "degraded": False,
    }


# =====================================================================
# Evaluate endpoint
# =====================================================================

def test_evaluate_returns_policy_decision():
    """Evaluate endpoint returns a well-formed PolicyDecision."""
    client = _fresh_client()
    resp = client.post("/v1/evaluate", json={
        "tenant_id": "bank-A",
        "assessment": _make_assessment(risk_score=0.50),
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["tenant_id"] == "bank-A"
    assert data["call_session_id"] == "call-001"
    assert data["risk_score"] == 0.50
    assert data["final_action"] == "RECOMMEND_CALLBACK_VERIFICATION"
    assert data["policy_version"] == 1  # default policy
    assert "decided_at" in data


def test_evaluate_high_risk_escalation():
    """High risk score triggers supervisor escalation by default."""
    client = _fresh_client()
    resp = client.post("/v1/evaluate", json={
        "tenant_id": "bank-A",
        "assessment": _make_assessment(risk_score=0.80),
    })
    assert resp.status_code == 200
    assert resp.json()["final_action"] == "RECOMMEND_SUPERVISOR_ESCALATION"


def test_evaluate_low_risk_proceed():
    """Low risk score produces PROCEED."""
    client = _fresh_client()
    resp = client.post("/v1/evaluate", json={
        "tenant_id": "bank-A",
        "assessment": _make_assessment(risk_score=0.10),
    })
    assert resp.status_code == 200
    assert resp.json()["final_action"] == "PROCEED"


def test_evaluate_preserves_original_actions():
    """The original actions from the fusion engine are passed through."""
    client = _fresh_client()
    resp = client.post("/v1/evaluate", json={
        "tenant_id": "bank-A",
        "assessment": _make_assessment(risk_score=0.50),
    })
    assert resp.json()["original_actions"] == ["RECOMMEND_CALLBACK_VERIFICATION"]


def test_evaluate_max_score_no_block_without_opt_in():
    """
    Risk score of 1.0 with default policy (auto_block_enabled=False)
    must NOT produce BLOCK_PENDING_VERIFICATION.
    """
    client = _fresh_client()
    resp = client.post("/v1/evaluate", json={
        "tenant_id": "bank-A",
        "assessment": _make_assessment(risk_score=1.0),
    })
    assert resp.status_code == 200
    assert resp.json()["final_action"] != "BLOCK_PENDING_VERIFICATION"
    assert resp.json()["final_action"] == "RECOMMEND_SUPERVISOR_ESCALATION"


# =====================================================================
# Auth enforcement
# =====================================================================

def test_get_policy_requires_admin():
    """GET policy without tenant_admin header returns 403."""
    client = _fresh_client()
    resp = client.get("/v1/tenants/bank-A/policy")
    assert resp.status_code == 403


def test_update_policy_requires_admin():
    """PUT policy without tenant_admin header returns 403."""
    client = _fresh_client()
    resp = client.put(
        "/v1/tenants/bank-A/policy",
        json={"callback_verification_threshold": 0.5},
    )
    assert resp.status_code == 403


def test_update_policy_requires_actor_identity():
    """PUT policy with admin header but without actor identity returns 400."""
    client = _fresh_client()
    resp = client.put(
        "/v1/tenants/bank-A/policy",
        json={"callback_verification_threshold": 0.5},
        headers={"X-Tenant-Admin": "true"},
    )
    assert resp.status_code == 400


def test_audit_log_requires_admin():
    """GET audit log without tenant_admin header returns 403."""
    client = _fresh_client()
    resp = client.get("/v1/tenants/bank-A/audit-log")
    assert resp.status_code == 403


# =====================================================================
# Policy updates + versioning
# =====================================================================

def test_policy_update_changes_thresholds():
    """Updating a threshold changes the policy config."""
    client = _fresh_client()
    resp = client.put(
        "/v1/tenants/bank-A/policy",
        json={"callback_verification_threshold": 0.60},
        headers={
            "X-Tenant-Admin": "true",
            "X-Actor-Identity": "admin@bank-a.com",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["callback_verification_threshold"] == 0.60
    assert data["policy_version"] == 2  # bumped from default 1


def test_evaluate_uses_updated_policy():
    """After a policy update, evaluate uses the new thresholds."""
    client = _fresh_client()

    # Default threshold for callback is 0.40, score 0.45 should trigger it
    resp = client.post("/v1/evaluate", json={
        "tenant_id": "bank-A",
        "assessment": _make_assessment(risk_score=0.45),
    })
    assert resp.json()["final_action"] == "RECOMMEND_CALLBACK_VERIFICATION"

    # Raise the callback threshold to 0.60
    client.put(
        "/v1/tenants/bank-A/policy",
        json={"callback_verification_threshold": 0.60},
        headers={
            "X-Tenant-Admin": "true",
            "X-Actor-Identity": "admin@bank-a.com",
        },
    )

    # Same score 0.45 should now PROCEED (below new threshold)
    resp = client.post("/v1/evaluate", json={
        "tenant_id": "bank-A",
        "assessment": _make_assessment(risk_score=0.45),
    })
    assert resp.json()["final_action"] == "PROCEED"
    assert resp.json()["policy_version"] == 2  # new version stamped


def test_enable_auto_block_then_block():
    """Enable auto_block, then verify blocking works at high scores."""
    client = _fresh_client()

    # Enable auto-block
    client.put(
        "/v1/tenants/bank-A/policy",
        json={"auto_block_enabled": True, "block_threshold": 0.90},
        headers={
            "X-Tenant-Admin": "true",
            "X-Actor-Identity": "admin@bank-a.com",
        },
    )

    # Score 0.95 should now produce BLOCK_PENDING_VERIFICATION
    resp = client.post("/v1/evaluate", json={
        "tenant_id": "bank-A",
        "assessment": _make_assessment(risk_score=0.95),
    })
    assert resp.json()["final_action"] == "BLOCK_PENDING_VERIFICATION"


# =====================================================================
# Health check
# =====================================================================

def test_healthz():
    """Health endpoint returns ok."""
    client = _fresh_client()
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
