"""
FastAPI HTTP integration tests for alerting-service.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest
from fastapi.testclient import TestClient

from dependencies import reset_dependencies
from main import app


@pytest.fixture(autouse=True)
def setup_and_teardown():
    reset_dependencies()
    yield
    reset_dependencies()


client = TestClient(app)


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_event_ingestion_and_alert_polling():
    event_payload = {
        "event_id": "evt-http-001",
        "call_session_id": "call-http-123",
        "tenant_id": "tenant-bank-1",
        "action": "RECOMMEND_CALLBACK_VERIFICATION",
        "risk_score": 0.88,
        "explanation": "synthesis detected",
    }
    # Ingest event
    res = client.post("/v1/events", json=event_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["event_id"] == "evt-http-001"
    assert data["channels_dispatched"] == 2

    # Poll UI alerts
    res = client.get("/v1/tenants/tenant-bank-1/alerts")
    assert res.status_code == 200
    alerts_data = res.json()
    assert len(alerts_data["alerts"]) == 1
    assert alerts_data["alerts"][0]["event_id"] == "evt-http-001"
    assert alerts_data["alerts"][0]["action"] == "RECOMMEND_CALLBACK_VERIFICATION"

    # Query audit trail
    res = client.get("/v1/tenants/tenant-bank-1/audit")
    assert res.status_code == 200
    audit_data = res.json()
    assert len(audit_data["entries"]) == 2
    for entry in audit_data["entries"]:
        assert entry["tenant_id"] == "tenant-bank-1"
        assert len(entry["recipient_hash"]) == 64
        assert entry["status"] == "delivered"


def test_http_idempotent_duplicate_event():
    event_payload = {
        "event_id": "evt-http-dup",
        "call_session_id": "call-http-dup",
        "tenant_id": "tenant-bank-1",
        "action": "RECOMMEND_MFA_STEP_UP",
        "risk_score": 0.65,
        "explanation": "moderate risk",
    }
    # First post
    res1 = client.post("/v1/events", json=event_payload)
    assert res1.status_code == 200
    assert res1.json()["channels_dispatched"] == 2

    # Second post with identical event_id
    res2 = client.post("/v1/events", json=event_payload)
    assert res2.status_code == 200
    assert res2.json()["channels_dispatched"] == 0

    # Ensure still only 1 alert in UI queue
    alerts = client.get("/v1/tenants/tenant-bank-1/alerts").json()["alerts"]
    assert len(alerts) == 1
