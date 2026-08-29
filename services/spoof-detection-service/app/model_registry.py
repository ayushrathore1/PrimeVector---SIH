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


import numpy as np


# MVP heuristic — not a trained model. Replace with a real classifier (AASIST/RawNet2-class) before production use.
def heuristic_synthesis_score(audio_features: Any) -> float:
    """
    Cheap heuristic: real speech has natural variance across frames;
    overly smooth/uniform spectra are more consistent with synthetic
    audio. Returns a score in [0, 1] — higher = more suspicious.
    NOT a trained classifier. Documented as a placeholder heuristic.
    """
    arr = np.array(audio_features, dtype=np.float32)
    if arr.size == 0:
        return 0.5
    if arr.size % 80 == 0 and arr.size >= 80:
        mel_spectrogram = arr.reshape(-1, 80)
    else:
        mel_spectrogram = arr.reshape(1, -1)

    frame_variance = float(np.var(mel_spectrogram, axis=0).mean())
    SOME_EMPIRICAL_BASELINE = 10.0
    score = 1.0 - min(frame_variance / SOME_EMPIRICAL_BASELINE, 1.0)
    return float(np.clip(score, 0.0, 1.0))


def _heuristic_model_fn(audio_features: Any) -> dict[str, float]:
    score = heuristic_synthesis_score(audio_features)
    eps = 1e-4
    clamped = max(eps, min(1.0 - eps, score))
    logit = float(np.log(clamped / (1.0 - clamped)))
    return {"score": score, "logit": logit}


class StubModelRegistry(ModelRegistry):
    """
    ModelRegistry serving the heuristic spoof detection model when enabled,
    or returning None when unconfigured (empty stub mode).
    """

    def __init__(self, enable_heuristic: bool = False):
        self.enable_heuristic = enable_heuristic
        self._entries = {}
        if enable_heuristic:
            self._entries["spoof-detector/generic"] = ModelRegistryEntry(
                model=_heuristic_model_fn,
                version="heuristic-v0.1.0",
            )

    def get_model(self, model_key: str) -> Optional[ModelRegistryEntry]:
        return self._entries.get(model_key)

    def list_models(self, prefix: str = "") -> list[str]:
        return [k for k in self._entries if k.startswith(prefix)]


