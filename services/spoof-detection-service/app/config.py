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
    # Full pipeline (decode+mel+forward) averages ~30ms on CPU;
    # 500ms provides generous headroom for cold starts and load spikes.
    inference_timeout_ms: int = 500

    # Which ModelRegistry backend to use.
    #   - "deepfake": Trained ResNet18+GRU+Attention model (production)
    #   - "dhwani": Dhwani voice deepfake detector (CNN/multi-branch,
    #     trained on Colab with Vaani + spoof datasets)
    #   - "heuristic": Log-mel heuristic scorer v4.0 (fallback only)
    #   - "stub": No model registered (available=false for all requests)
    model_registry_backend: str = "deepfake"

    # Logging level for structured logs.
    log_level: str = "INFO"

    # Default accent cluster to use when language identification
    # fails or is unavailable (§4.4 fallback behavior).
    default_accent_cluster: str = "generic"

    model_config = {"env_prefix": "SPOOF_"}


settings = Settings()
