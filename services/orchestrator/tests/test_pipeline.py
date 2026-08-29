"""
End-to-end and unit tests for the orchestrator pipeline.

Uses ``httpx.AsyncClient`` with ``respx`` to mock every downstream
microservice call, ensuring no real network traffic is generated.

Test matrix:
  1. Happy path — all downstream services respond correctly.
  2. Feature-extraction failure — immediate degraded response.
  3. Spoof-detection failure — synthesis_signal unavailable, pipeline
     continues in degraded mode.
  4. Enrollment-service failure — speaker_match unavailable, pipeline
     continues in degraded mode.
  5. Risk-fusion-engine failure — degraded, RECOMMEND_CALLBACK_VERIFICATION.
  6. Policy-engine failure — uses fusion actions directly, degraded.
  7. Alerting-service failure — non-blocking, pipeline still succeeds.
  8. Health check endpoint.
"""

from __future__ import annotations

import sys
import os
import json
from pathlib import Path

import httpx
import pytest
import respx

# Ensure the app package is on the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from main import app, _client  # noqa: E402
from client import PipelineClient  # noqa: E402
from models import PipelineRequest  # noqa: E402


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------

@pytest.fixture
def pipeline_request_data() -> dict:
    """Minimal valid pipeline request payload."""
    return {
        "session_id": "sess-001",
        "tenant_id": "tenant-A",
        "subject_id": "subject-X",
        "audio_pcm_base64": "AAAA",  # dummy base64
        "sample_rate_hz": 16000,
        "channels": 1,
        "context_score": 0.3,
    }


def _extraction_response() -> dict:
    """Fixture: successful feature-extraction response."""
    return {
        "request_id": "sess-001",
        "log_mel": {
            "frames": [[0.1, 0.2], [0.3, 0.4]],
            "n_mels": 80,
            "hop_length_ms": 10.0,
            "sample_rate_hz": 16000,
        },
        "speaker_embedding": [0.5] * 192,
        "duration_ms": 3200.0,
    }


def _spoof_response() -> dict:
    """Fixture: successful spoof-detection response."""
    return {
        "score": 0.85,
        "confidence": 0.92,
        "available": True,
        "detail": "model=v1.2, accent=en-generic, route=primary",
    }


def _enrollment_response() -> dict:
    """Fixture: enrolled voiceprint status response."""
    return {
        "status": "ENROLLED",
        "voiceprint_id": "vp-123",
        "version": 2,
        "sessions_completed": 3,
        "sessions_remaining": 0,
        "enrolled_at": "2025-06-01T00:00:00Z",
        "revoked_at": None,
    }


def _risk_assessment_response() -> dict:
    """Fixture: successful risk-fusion response."""
    return {
        "call_session_id": "sess-001",
        "risk_score": 0.72,
        "confidence": 0.88,
        "actions": [
            "RECOMMEND_CALLBACK_VERIFICATION",
            "RECOMMEND_SUPERVISOR_ESCALATION",
        ],
        "explanation": "high risk (0.72): synthesis artifacts detected",
        "evaluated_at": "2025-06-15T12:00:00Z",
        "degraded": False,
    }


def _policy_decision_response() -> dict:
    """Fixture: successful policy-engine response."""
    return {
        "call_session_id": "sess-001",
        "tenant_id": "tenant-A",
        "risk_score": 0.72,
        "original_actions": [
            "RECOMMEND_CALLBACK_VERIFICATION",
            "RECOMMEND_SUPERVISOR_ESCALATION",
        ],
        "final_action": "RECOMMEND_SUPERVISOR_ESCALATION",
        "explanation": "high risk (0.72): synthesis artifacts detected",
        "policy_version": 3,
        "decided_at": "2025-06-15T12:00:01Z",
    }


def _alert_response() -> dict:
    """Fixture: successful alerting-service response."""
    return {
        "event_id": "evt-001",
        "channels_dispatched": 2,
        "message": "Event processed, dispatched to 2 channel(s)",
    }


def _mock_all_services(router: respx.MockRouter) -> None:
    """Register successful mocks for all downstream services."""
    router.post("http://localhost:8001/v1/extract").mock(
        return_value=httpx.Response(200, json=_extraction_response()),
    )
    router.post("http://localhost:8002/v1/detect").mock(
        return_value=httpx.Response(200, json=_spoof_response()),
    )
    router.get(
        url__regex=r"http://localhost:8003/v1/tenants/.*/subjects/.*/status",
    ).mock(
        return_value=httpx.Response(200, json=_enrollment_response()),
    )
    router.post("http://localhost:8004/v1/evaluate").mock(
        return_value=httpx.Response(200, json=_policy_decision_response()),
    )
    router.post("http://localhost:8000/v1/assess").mock(
        return_value=httpx.Response(200, json=_risk_assessment_response()),
    )
    router.post("http://localhost:8005/v1/events").mock(
        return_value=httpx.Response(200, json=_alert_response()),
    )


# -----------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_healthz():
    """GET /healthz returns status ok."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        resp = await ac.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_happy_path(pipeline_request_data: dict):
    """All downstream services succeed — full pipeline response."""
    with respx.mock:
        _mock_all_services(respx)

        # Inject a PipelineClient that uses the mocked transport.
        import main as main_module
        client = PipelineClient(http_client=httpx.AsyncClient())
        main_module._client = client

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as ac:
                resp = await ac.post(
                    "/v1/pipeline/process",
                    json=pipeline_request_data,
                )

            assert resp.status_code == 200
            body = resp.json()

            # Pipeline completed
            assert body["session_id"] == "sess-001"
            assert body["tenant_id"] == "tenant-A"
            assert body["degraded"] is False

            # All stages present
            assert body["extraction"] is not None
            assert body["synthesis_signal"] is not None
            assert body["risk_assessment"] is not None
            assert body["policy_decision"] is not None
            assert body["alert_event"] is not None

            # Final action from policy engine
            assert body["final_action"] == "RECOMMEND_SUPERVISOR_ESCALATION"
            assert body["policy_decision"]["policy_version"] == 3
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_feature_extraction_failure(pipeline_request_data: dict):
    """Feature extraction fails — immediate degraded response."""
    with respx.mock:
        respx.post("http://localhost:8001/v1/extract").mock(
            return_value=httpx.Response(500, json={"detail": "boom"}),
        )

        import main as main_module
        client = PipelineClient(http_client=httpx.AsyncClient())
        main_module._client = client

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as ac:
                resp = await ac.post(
                    "/v1/pipeline/process",
                    json=pipeline_request_data,
                )

            assert resp.status_code == 200
            body = resp.json()
            assert body["degraded"] is True
            assert body["final_action"] == "RECOMMEND_CALLBACK_VERIFICATION"
            assert body["extraction"] is None
            assert body["risk_assessment"] is None
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_spoof_detection_failure(pipeline_request_data: dict):
    """Spoof detection fails — pipeline continues, synthesis unavailable."""
    with respx.mock:
        respx.post("http://localhost:8001/v1/extract").mock(
            return_value=httpx.Response(200, json=_extraction_response()),
        )
        respx.post("http://localhost:8002/v1/detect").mock(
            return_value=httpx.Response(503, json={"detail": "overloaded"}),
        )
        respx.get(
            url__regex=r"http://localhost:8003/v1/tenants/.*/subjects/.*/status",
        ).mock(
            return_value=httpx.Response(200, json=_enrollment_response()),
        )
        respx.post("http://localhost:8000/v1/assess").mock(
            return_value=httpx.Response(
                200, json=_risk_assessment_response(),
            ),
        )
        respx.post("http://localhost:8004/v1/evaluate").mock(
            return_value=httpx.Response(
                200, json=_policy_decision_response(),
            ),
        )
        respx.post("http://localhost:8005/v1/events").mock(
            return_value=httpx.Response(200, json=_alert_response()),
        )

        import main as main_module
        client = PipelineClient(http_client=httpx.AsyncClient())
        main_module._client = client

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as ac:
                resp = await ac.post(
                    "/v1/pipeline/process",
                    json=pipeline_request_data,
                )

            assert resp.status_code == 200
            body = resp.json()
            # Synthesis signal should be None (spoof service failed,
            # so the orchestrator sets a local unavailable signal for
            # fusion but does NOT store the SynthesisSignalResponse).
            assert body["synthesis_signal"] is None
            # Pipeline still reaches policy decision
            assert body["policy_decision"] is not None
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_enrollment_failure(pipeline_request_data: dict):
    """Enrollment service fails — speaker_match unavailable."""
    with respx.mock:
        respx.post("http://localhost:8001/v1/extract").mock(
            return_value=httpx.Response(200, json=_extraction_response()),
        )
        respx.post("http://localhost:8002/v1/detect").mock(
            return_value=httpx.Response(200, json=_spoof_response()),
        )
        respx.get(
            url__regex=r"http://localhost:8003/v1/tenants/.*/subjects/.*/status",
        ).mock(
            return_value=httpx.Response(500, json={"detail": "db error"}),
        )
        respx.post("http://localhost:8000/v1/assess").mock(
            return_value=httpx.Response(
                200, json=_risk_assessment_response(),
            ),
        )
        respx.post("http://localhost:8004/v1/evaluate").mock(
            return_value=httpx.Response(
                200, json=_policy_decision_response(),
            ),
        )
        respx.post("http://localhost:8005/v1/events").mock(
            return_value=httpx.Response(200, json=_alert_response()),
        )

        import main as main_module
        client = PipelineClient(http_client=httpx.AsyncClient())
        main_module._client = client

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as ac:
                resp = await ac.post(
                    "/v1/pipeline/process",
                    json=pipeline_request_data,
                )

            assert resp.status_code == 200
            body = resp.json()
            # Speaker match signal should be unavailable
            assert body["speaker_match_signal"]["available"] is False
            assert "unreachable" in body["speaker_match_signal"]["detail"]
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_risk_fusion_failure(pipeline_request_data: dict):
    """Risk fusion engine fails — degraded + RECOMMEND_CALLBACK_VERIFICATION."""
    with respx.mock:
        respx.post("http://localhost:8001/v1/extract").mock(
            return_value=httpx.Response(200, json=_extraction_response()),
        )
        respx.post("http://localhost:8002/v1/detect").mock(
            return_value=httpx.Response(200, json=_spoof_response()),
        )
        respx.get(
            url__regex=r"http://localhost:8003/v1/tenants/.*/subjects/.*/status",
        ).mock(
            return_value=httpx.Response(200, json=_enrollment_response()),
        )
        respx.post("http://localhost:8000/v1/assess").mock(
            return_value=httpx.Response(502, json={"detail": "gateway error"}),
        )

        import main as main_module
        client = PipelineClient(http_client=httpx.AsyncClient())
        main_module._client = client

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as ac:
                resp = await ac.post(
                    "/v1/pipeline/process",
                    json=pipeline_request_data,
                )

            assert resp.status_code == 200
            body = resp.json()
            assert body["degraded"] is True
            assert body["final_action"] == "RECOMMEND_CALLBACK_VERIFICATION"
            assert body["risk_assessment"] is None
            assert body["policy_decision"] is None
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_policy_engine_failure(pipeline_request_data: dict):
    """Policy engine fails — uses fusion actions, degraded."""
    with respx.mock:
        _mock_all_services(respx)
        # Override policy engine to fail
        respx.post("http://localhost:8004/v1/evaluate").mock(
            return_value=httpx.Response(500, json={"detail": "crash"}),
        )

        import main as main_module
        client = PipelineClient(http_client=httpx.AsyncClient())
        main_module._client = client

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as ac:
                resp = await ac.post(
                    "/v1/pipeline/process",
                    json=pipeline_request_data,
                )

            assert resp.status_code == 200
            body = resp.json()
            assert body["degraded"] is True
            # Falls back to first fusion action
            assert body["final_action"] == "RECOMMEND_CALLBACK_VERIFICATION"
            assert body["policy_decision"] is None
            assert "policy engine unavailable" in body["explanation"]
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_alerting_failure_non_blocking(pipeline_request_data: dict):
    """Alerting service fails — pipeline still succeeds (non-blocking)."""
    with respx.mock:
        _mock_all_services(respx)
        # Override alerting to fail
        respx.post("http://localhost:8005/v1/events").mock(
            return_value=httpx.Response(500, json={"detail": "smtp down"}),
        )

        import main as main_module
        client = PipelineClient(http_client=httpx.AsyncClient())
        main_module._client = client

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as ac:
                resp = await ac.post(
                    "/v1/pipeline/process",
                    json=pipeline_request_data,
                )

            assert resp.status_code == 200
            body = resp.json()
            # Pipeline still succeeded
            assert body["degraded"] is False
            assert body["policy_decision"] is not None
            assert body["final_action"] == "RECOMMEND_SUPERVISOR_ESCALATION"
            # But alert was not dispatched
            assert body["alert_event"] is None
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_not_enrolled_subject(pipeline_request_data: dict):
    """Subject is NOT_ENROLLED — speaker_match_signal unavailable."""
    not_enrolled_resp = {
        "status": "NOT_ENROLLED",
        "voiceprint_id": None,
        "version": None,
        "sessions_completed": None,
        "sessions_remaining": None,
        "enrolled_at": None,
        "revoked_at": None,
    }
    with respx.mock:
        _mock_all_services(respx)
        respx.get(
            url__regex=r"http://localhost:8003/v1/tenants/.*/subjects/.*/status",
        ).mock(
            return_value=httpx.Response(200, json=not_enrolled_resp),
        )

        import main as main_module
        client = PipelineClient(http_client=httpx.AsyncClient())
        main_module._client = client

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as ac:
                resp = await ac.post(
                    "/v1/pipeline/process",
                    json=pipeline_request_data,
                )

            assert resp.status_code == 200
            body = resp.json()
            assert body["speaker_match_signal"]["available"] is False
            assert "NOT_ENROLLED" in body["speaker_match_signal"]["detail"]
        finally:
            await client.close()
