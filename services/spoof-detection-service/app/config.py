"""
Configuration for the spoof-detection-service.

All settings are environment-variable driven via pydantic-settings,
so deployments can tune behavior without code changes (DESIGN.md §4.8:
every threshold/policy change via config, not code deploy).
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Service configuration, loaded from environment variables.

    All env vars are prefixed with SPOOF_ to avoid collisions.
    Example: SPOOF_INFERENCE_TIMEOUT_MS=300
    """

    # Maximum milliseconds to wait for model inference before treating
    # the call as a timeout (and returning available=false).
    # Default 250ms leaves headroom within the 300ms p99 SLO (§3).
    inference_timeout_ms: int = 250

    # Which ModelRegistry backend to use. Currently only "stub" is
    # implemented — a real backend (e.g., MLflow, custom registry)
    # must be plugged in before this service produces real scores.
    model_registry_backend: str = "stub"

    # Logging level for structured logs.
    log_level: str = "INFO"

    # Default accent cluster to use when language identification
    # fails or is unavailable (§4.4 fallback behavior).
    default_accent_cluster: str = "generic"

    model_config = {"env_prefix": "SPOOF_"}


settings = Settings()
