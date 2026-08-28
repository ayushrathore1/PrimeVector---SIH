"""
Tests for Voice Integrity Python SDK client.
"""

import pytest
import respx
import httpx

from voiceintegrity import (
    VoiceIntegrityClient,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    RiskSignal,
    EnrollmentStatus,
    RecommendedAction,
    APIError,
    ConnectionError,
)


@pytest.fixture
def client():
    return VoiceIntegrityClient(
        base_url="https://api.voiceintegrity.test",
        api_key="test_api_key_123",
        timeout=3.0,
    )


@pytest.fixture
def sample_request():
    return RiskAssessmentRequest(
        call_session_id="call-sess-001",
        tenant_id="tenant-test-bank",
        synthesis_signal=RiskSignal(score=0.9, confidence=0.95, available=True, detail="synthesis detected"),
        speaker_match_signal=RiskSignal(score=0.8, confidence=0.9, available=True, detail="mismatch"),
        contextual_signal=RiskSignal(score=0.5, confidence=1.0, available=True, detail="wire transfer"),
        enrollment_status=EnrollmentStatus.ENROLLED,
    )


@respx.mock
def test_assess_success(client, sample_request):
    mock_route = respx.post("https://api.voiceintegrity.test/v1/assess").respond(
        status_code=200,
        json={
            "call_session_id": "call-sess-001",
            "risk_score": 0.95,
            "confidence": 0.90,
            "actions": ["RECOMMEND_CALLBACK_VERIFICATION", "RECOMMEND_SUPERVISOR_ESCALATION"],
            "explanation": "high risk: synthesis artifacts detected; voice mismatch",
            "evaluated_at": "2026-08-28T18:00:00Z",
            "degraded": False,
        },
    )

    response = client.assess(sample_request)

    assert mock_route.called
    sent_request = mock_route.calls.last.request
    assert sent_request.headers["X-API-Key"] == "test_api_key_123"
    assert sent_request.headers["Content-Type"] == "application/json"

    assert isinstance(response, RiskAssessmentResponse)
    assert response.call_session_id == "call-sess-001"
    assert response.risk_score == 0.95
    assert response.confidence == 0.90
    assert response.actions == [
        RecommendedAction.RECOMMEND_CALLBACK_VERIFICATION,
        RecommendedAction.RECOMMEND_SUPERVISOR_ESCALATION,
    ]
    assert response.explanation == "high risk: synthesis artifacts detected; voice mismatch"
    assert response.evaluated_at == "2026-08-28T18:00:00Z"
    assert response.degraded is False


@respx.mock
def test_assess_api_error(client, sample_request):
    respx.post("https://api.voiceintegrity.test/v1/assess").respond(
        status_code=400,
        text="Invalid signal score value",
    )

    with pytest.raises(APIError) as exc_info:
        client.assess(sample_request)

    assert exc_info.value.status_code == 400
    assert "Invalid signal score value" in exc_info.value.message


@respx.mock
def test_assess_connection_error(client, sample_request):
    respx.post("https://api.voiceintegrity.test/v1/assess").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    with pytest.raises(ConnectionError):
        client.assess(sample_request)
