"""
API endpoint integration tests.

Verifies that the HTTP interface matches the RiskSignal proto shape
and handles edge cases correctly. Uses FastAPI's TestClient for
in-process testing without starting a real server.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    """
    TestClient as a context manager to trigger the FastAPI lifespan
    (which initializes the ModelRegistry and SpoofDetector).
    """
    with TestClient(app) as c:
        yield c


# =====================================================================
# Health endpoint
# =====================================================================

def test_healthz_returns_200(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_registered" in data


def test_healthz_reports_registry_backend(client):
    response = client.get("/healthz")
    data = response.json()
    assert "registry_backend" in data


# =====================================================================
# Detection endpoint: response shape matches RiskSignal proto
# =====================================================================

def test_detect_returns_risk_signal_shape(client):
    """Response must have all four RiskSignal proto fields."""
    response = client.post("/v1/detect", json={
        "call_session_id": "test-001",
        "tenant_id": "tenant-001",
        "audio_features": [0.1] * 64,
    })
    assert response.status_code == 200
    data = response.json()

    # All four RiskSignal fields must be present.
    assert "score" in data
    assert "confidence" in data
    assert "available" in data
    assert "detail" in data

    # Types must match proto.
    assert isinstance(data["score"], (int, float))
    assert isinstance(data["confidence"], (int, float))
    assert isinstance(data["available"], bool)
    assert isinstance(data["detail"], str)


def test_detect_with_stub_registry_returns_unavailable(client):
    """With the default stub registry, detection returns available=false."""
    response = client.post("/v1/detect", json={
        "call_session_id": "test-002",
        "tenant_id": "tenant-001",
        "audio_features": [0.5] * 128,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is False


# =====================================================================
# Input validation
# =====================================================================

def test_detect_missing_audio_features_returns_422(client):
    """Missing required field should return 422."""
    response = client.post("/v1/detect", json={
        "call_session_id": "test-003",
        "tenant_id": "tenant-001",
        # audio_features missing
    })
    assert response.status_code == 422


def test_detect_empty_audio_features_returns_422(client):
    """Empty audio features list should return 422 (min_length=1)."""
    response = client.post("/v1/detect", json={
        "call_session_id": "test-004",
        "tenant_id": "tenant-001",
        "audio_features": [],
    })
    assert response.status_code == 422


def test_detect_missing_session_id_returns_422(client):
    response = client.post("/v1/detect", json={
        "tenant_id": "tenant-001",
        "audio_features": [0.1],
    })
    assert response.status_code == 422


def test_detect_missing_tenant_id_returns_422(client):
    response = client.post("/v1/detect", json={
        "call_session_id": "test-005",
        "audio_features": [0.1],
    })
    assert response.status_code == 422


# =====================================================================
# Score bounds on response
# =====================================================================

def test_detect_score_bounds(client):
    """Score and confidence must be in [0.0, 1.0]."""
    response = client.post("/v1/detect", json={
        "call_session_id": "test-006",
        "tenant_id": "tenant-001",
        "audio_features": [0.1] * 64,
    })
    data = response.json()
    assert 0.0 <= data["score"] <= 1.0
    assert 0.0 <= data["confidence"] <= 1.0


# =====================================================================
# Optional fields default correctly
# =====================================================================

def test_detect_optional_fields_default(client):
    """sample_rate and feature_type should use defaults if omitted."""
    response = client.post("/v1/detect", json={
        "call_session_id": "test-007",
        "tenant_id": "tenant-001",
        "audio_features": [0.1] * 10,
    })
    assert response.status_code == 200


def test_detect_custom_optional_fields(client):
    """Custom sample_rate and feature_type should be accepted."""
    response = client.post("/v1/detect", json={
        "call_session_id": "test-008",
        "tenant_id": "tenant-001",
        "audio_features": [0.1] * 10,
        "sample_rate": 8000,
        "feature_type": "mel-spectrogram",
    })
    assert response.status_code == 200
