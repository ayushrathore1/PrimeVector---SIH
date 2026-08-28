"""
Exceptions for Voice Integrity SDK.
"""

from typing import Optional


class VoiceIntegrityError(Exception):
    """Base exception for all Voice Integrity SDK errors."""
    pass


class APIError(VoiceIntegrityError):
    """
    Raised when the API returns an error response (4xx, 5xx).

    Attributes:
        status_code (int): HTTP status code
        message (str): Error message details
        response_body (str): Raw response body content
    """
    def __init__(self, status_code: int, message: str, response_body: Optional[str] = None):
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        super().__init__(f"API Error {status_code}: {message}")


class ConnectionError(VoiceIntegrityError):
    """Raised when communication with the Voice Integrity service fails."""
    pass
