"""
Usage metering and rate limiting for PrimeVector API Gateway.

Wraps storage layer with rate-limit enforcement and
provides convenience functions for the main router.
"""
from __future__ import annotations

from fastapi import HTTPException, status

import storage


def enforce_rate_limit(key_info: dict) -> None:
    """
    Check rate limit for the given API key.
    Raises 429 if the daily limit is exceeded.
    """
    key_id = key_info["key_id"]
    tier = key_info["tier"]

    if not storage.check_rate_limit(key_id, tier):
        daily_limit = storage.TIER_LIMITS[storage.Tier(tier)][0]
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Daily detection limit ({daily_limit:,}) reached for "
                           f"'{tier}' tier. Resets at midnight UTC.",
                "tier": tier,
                "daily_limit": daily_limit,
                "upgrade_url": "https://primevector.dev/pricing",
            },
        )


def record_detection(
    key_id: str,
    session_id: str,
    verdict: str,
    spoof_score: float,
    confidence: float,
    latency_ms: float,
) -> None:
    """Record a detection in the metering system."""
    storage.log_detection(
        api_key_id=key_id,
        session_id=session_id,
        verdict=verdict,
        spoof_score=spoof_score,
        confidence=confidence,
        latency_ms=latency_ms,
    )
