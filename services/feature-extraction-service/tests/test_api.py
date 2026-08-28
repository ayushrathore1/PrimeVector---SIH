import os
import sys
import pytest
from fastapi.testclient import TestClient
import numpy as np
import base64

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from main import app

client = TestClient(app)

def test_extract_endpoint_success():
    audio_bytes = np.zeros(16000, dtype=np.int16).tobytes()
    b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
    
    res = client.post("/v1/extract", json={
        "request_id": "req-123",
        "tenant_id": "tenant-abc",
        "audio_bytes": b64_audio
    })
    assert res.status_code == 200
    data = res.json()
    assert data["request_id"] == "req-123"
    assert "log_mel" in data
    assert "speaker_embedding" in data
    assert "audio_bytes" not in data

def test_extract_endpoint_empty_audio():
    res = client.post("/v1/extract", json={
        "request_id": "req-123",
        "tenant_id": "tenant-abc",
        "audio_bytes": ""
    })
    # Could be 422 (pydantic validation) or 400 (our custom logic)
    assert res.status_code in [400, 422]

def test_healthz():
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
