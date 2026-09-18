"""
API Key authentication middleware for PrimeVector Gateway.

Validates X-API-Key header against the storage backend.
Public endpoints (health, docs) bypass authentication.
"""
from __future__ import annotations

from fastapi import HTTPException, Request, status

import storage

# Endpoints that don't require authentication
PUBLIC_PATHS = {"/v1/health", "/docs", "/openapi.json", "/redoc", "/"}


async def authenticate(request: Request) -> dict:
    """
    Validate the API key from the X-API-Key header.

    Returns the key info dict on success.
    Raises 401 if missing/invalid, 403 if revoked.
    """
    # Skip auth for public endpoints
    if request.url.path in PUBLIC_PATHS:
        return {}

    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_api_key",
                "message": "X-API-Key header is required. "
                           "Get your key at https://primevector.dev/pricing",
            },
        )

    key_info = storage.validate_api_key(api_key)
    if key_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_api_key",
                "message": "The provided API key is invalid or has been revoked.",
            },
        )

    return key_info


def check_tier_access(key_info: dict, required_tier: str) -> None:
    """
    Check if the API key's tier allows access to a feature.

    Tier hierarchy: enterprise > pro > free
    """
    tier_order = {"free": 0, "pro": 1, "enterprise": 2}
    current = tier_order.get(key_info.get("tier", "free"), 0)
    required = tier_order.get(required_tier, 0)

    if current < required:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "tier_insufficient",
                "message": f"This endpoint requires '{required_tier}' tier or higher. "
                           f"Your current tier: '{key_info['tier']}'. "
                           f"Upgrade at https://primevector.dev/pricing",
                "current_tier": key_info["tier"],
                "required_tier": required_tier,
            },
        )
