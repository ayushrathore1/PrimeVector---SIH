"""
ModelRegistry abstraction for the voice-integrity platform.

Per DESIGN.md §4.3, every model (spoof detector, speaker-embedding model)
is served via a versioned Model Registry entry, never hardcoded into a
service. This module defines the abstract interface and a stub
implementation for development/testing.

Registry key convention:
  - "spoof-detector/generic"     — language-agnostic fallback model
  - "spoof-detector/{cluster}"   — accent-cluster-specific variant
                                   (e.g., "spoof-detector/hi-IN")
  - "language-id/default"        — language/accent identification model

When a real model store backend is available (MLflow, custom registry,
S3-backed cache, etc.), implement the ModelRegistry ABC and wire it
in via config.model_registry_backend in main.py.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ModelNotRegisteredError(Exception):
    """Raised when a required model is not found in the registry."""
    pass


@dataclass(frozen=True)
class ModelRegistryEntry:
    """
    A loaded model with its metadata.

    The ``version`` field is critical: it appears in every RiskSignal
    detail string, enabling the shadow-mode evaluation pipeline (§4.3)
    to compare scores across model versions without code changes.
    """
    model: Any                    # The callable model object
    version: str                  # e.g. "spoof-detector-v2.1.3"
    registered_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


class ModelRegistry(ABC):
    """
    Abstract interface for model lookup.

    Implementations might back this with MLflow, a custom model store,
    an in-memory cache populated from S3/GCS, etc. The spoof-detection
    service depends only on this interface, never on a concrete backend.
    """

    @abstractmethod
    def get_model(self, model_key: str) -> Optional[ModelRegistryEntry]:
        """
        Look up a model by key.

        Returns the ModelRegistryEntry if a model is registered under
        the given key, or None if no model is registered.
        """
        ...

    @abstractmethod
    def list_models(self, prefix: str = "") -> list[str]:
        """
        List registered model keys matching the given prefix.

        Useful for discovery (e.g., listing all accent-cluster-specific
        spoof detector variants currently available).
        """
        ...


class StubModelRegistry(ModelRegistry):
    """
    Stub registry that returns None for all lookups.

    BLOCKING DEPENDENCY: the service will start and respond to requests,
    but every detection will return available=false because no model is
    loaded. This is the correct fail-safe behavior per fusion.py design
    decision 4: "an unavailable signal is evidence of nothing, not
    evidence of safety."

    To unblock: register a real wav2vec2-class checkpoint fine-tuned on
    ASVspoof-style data via a concrete ModelRegistry implementation.
    """

    def __init__(self):
        logger.warning(
            "StubModelRegistry is active — no real models are loaded. "
            "All spoof detection requests will return available=false. "
            "This is a BLOCKING DEPENDENCY: register a pretrained "
            "spoof-detection model to produce real scores."
        )

    def get_model(self, model_key: str) -> Optional[ModelRegistryEntry]:
        logger.debug("StubModelRegistry.get_model('%s') -> None", model_key)
        return None

    def list_models(self, prefix: str = "") -> list[str]:
        return []
