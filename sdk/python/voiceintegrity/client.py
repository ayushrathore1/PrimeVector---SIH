"""
Client for the Voice Integrity & Impersonation Prevention Service.

Provides a thin wrapper around the RiskFusionEngine.Assess RPC endpoint.
No hidden retries — network failures and API errors are raised directly.
"""

from __future__ import annotations

from typing import Optional
import httpx

from voiceintegrity.exceptions import APIError, ConnectionError
from voiceintegrity.models import (
    EnrollmentStatus,
    RecommendedAction,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    RiskSignal,
)


class VoiceIntegrityClient:
    """
    Client for RiskFusionEngine (voiceintegrity.v1).

    Parameters:
        base_url (str): Base URL of the Voice Integrity service (e.g. 'https://api.voiceintegrity.example.com')
        api_key (Optional[str]): API key for authentication via X-API-Key header
        timeout (float): Request timeout in seconds (default: 5.0)
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 5.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def assess(self, request: RiskAssessmentRequest) -> RiskAssessmentResponse:
        """
        Evaluate real-time risk assessment signals for a call session.

        Maps directly to `rpc Assess(RiskAssessmentRequest) returns (RiskAssessmentResponse)`.

        Request Shape:
            call_session_id (str): Unique identifier for the active call
            tenant_id (str): Organization/Tenant identifier
            synthesis_signal (RiskSignal):
                - score (float): 0.0-1.0 (synthesis/acoustic spoof detection)
                - confidence (float): 0.0-1.0
                - available (bool): true if acoustic synthesis score computed
                - detail (str): descriptive metadata
            speaker_match_signal (RiskSignal):
                - score (float): 0.0-1.0 (speaker mismatch score)
                - confidence (float): 0.0-1.0
                - available (bool): false if unenrolled
                - detail (str): descriptive metadata
            contextual_signal (RiskSignal):
                - score (float): 0.0-1.0 (transaction/caller risk factor)
                - confidence (float): 0.0-1.0
                - available (bool): true
                - detail (str): descriptive metadata
            enrollment_status (EnrollmentStatus): ENROLLMENT_STATUS_UNSPECIFIED | NOT_ENROLLED | ENROLLED | ENROLLMENT_REVOKED

        Response Shape:
            call_session_id (str): Identifier echoed back
            risk_score (float): Fused composite score between 0.0 and 1.0
            confidence (float): Fused confidence rating between 0.0 and 1.0
            actions (list[RecommendedAction]): List containing:
                - PROCEED
                - RECOMMEND_CALLBACK_VERIFICATION
                - RECOMMEND_MFA_STEP_UP
                - RECOMMEND_SUPERVISOR_ESCALATION
                - BLOCK_PENDING_VERIFICATION
            explanation (str): Human-readable justification of the score
            evaluated_at (str): ISO-8601 evaluation timestamp
            degraded (bool): True if computed under fail-safe mode

        Raises:
            APIError: If the remote service returns a 4xx or 5xx status code.
            ConnectionError: If network connection fails or request times out.
        """
        url = f"{self.base_url}/v1/assess"
        payload = request.to_dict()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    json=payload,
                    headers=self._get_headers(),
                )
        except httpx.RequestError as exc:
            raise ConnectionError(f"Failed to communicate with {url}: {exc}") from exc

        if response.is_error:
            raise APIError(
                status_code=response.status_code,
                message=response.text,
                response_body=response.text,
            )

        try:
            data = response.json()
        except Exception as exc:
            raise APIError(
                status_code=response.status_code,
                message="Invalid JSON response from server",
                response_body=response.text,
            ) from exc

        return RiskAssessmentResponse.from_dict(data)
