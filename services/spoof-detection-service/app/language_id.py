"""
Language/accent identification pre-pass.

Per DESIGN.md §4.4, language/accent identification runs as a cheap
first-pass classifier before the main spoof detector. It routes to
accent-cluster-specific model variants where available, and falls back
to a language-agnostic acoustic model otherwise.

Supported accent clusters (matching Indian linguistic landscape):
  hi-IN (Hindi), en-IN (Indian English), ta-IN (Tamil), te-IN (Telugu),
  bn-IN (Bengali), mr-IN (Marathi), gu-IN (Gujarati), kn-IN (Kannada),
  ml-IN (Malayalam), pa-IN (Punjabi), generic (fallback)

The cluster taxonomy feeds per-cluster fairness reporting required
before any model promotion (§4.4): FPR and FNR must be measured and
reported per cluster, not just in aggregate.
"""
import logging
from dataclasses import dataclass
from typing import Optional

from model_registry import ModelRegistry

logger = logging.getLogger(__name__)

# Known accent clusters for the Indian linguistic landscape.
# This taxonomy feeds per-cluster fairness reporting (§4.4).
KNOWN_CLUSTERS = frozenset({
    "hi-IN",  # Hindi
    "en-IN",  # Indian English
    "ta-IN",  # Tamil
    "te-IN",  # Telugu
    "bn-IN",  # Bengali
    "mr-IN",  # Marathi
    "gu-IN",  # Gujarati
    "kn-IN",  # Kannada
    "ml-IN",  # Malayalam
    "pa-IN",  # Punjabi
})

LANGUAGE_ID_MODEL_KEY = "language-id/default"


@dataclass(frozen=True)
class LanguageIdResult:
    """Result of language/accent identification."""
    cluster: str               # e.g., "hi-IN" or "generic"
    confidence: float          # 0.0-1.0, how confident the classifier is
    model_version: str         # version of the language-ID model used
    fallback_reason: Optional[str] = None  # why we fell back, if we did


class LanguageIdentifier:
    """
    Runs the language/accent identification pre-pass (§4.4).

    Loads the language-ID model from ModelRegistry on construction.
    If the model is unavailable, all calls fall back to the default
    cluster. The fallback path is always logged — this feeds the
    per-cluster fairness reporting required before any model promotion.
    """

    def __init__(self, registry: ModelRegistry, default_cluster: str = "generic"):
        self._registry = registry
        self._default_cluster = default_cluster
        self._model_entry = registry.get_model(LANGUAGE_ID_MODEL_KEY)

        if self._model_entry is None:
            logger.warning(
                "Language-ID model not registered (key='%s'). "
                "All requests will use fallback cluster='%s'.",
                LANGUAGE_ID_MODEL_KEY, default_cluster,
            )

    def identify(self, audio_features: list[float]) -> LanguageIdResult:
        """
        Identify the language/accent cluster from audio features.

        Returns the detected cluster and confidence. If the language-ID
        model is unavailable or fails, falls back to the default cluster
        and logs the reason (for fairness tracking).
        """
        if self._model_entry is None:
            return LanguageIdResult(
                cluster=self._default_cluster,
                confidence=0.0,
                model_version="none",
                fallback_reason="language-id model not registered",
            )

        try:
            # Expected model interface:
            #   model(features) -> {"cluster": str, "confidence": float}
            prediction = self._model_entry.model(audio_features)
            cluster = prediction.get("cluster", self._default_cluster)
            confidence = float(prediction.get("confidence", 0.0))

            # Validate the cluster is in our known taxonomy.
            if cluster not in KNOWN_CLUSTERS:
                logger.info(
                    "Language-ID returned unknown cluster '%s', "
                    "falling back to '%s'. model_version=%s",
                    cluster, self._default_cluster,
                    self._model_entry.version,
                )
                return LanguageIdResult(
                    cluster=self._default_cluster,
                    confidence=confidence,
                    model_version=self._model_entry.version,
                    fallback_reason=f"unknown cluster '{cluster}' not in taxonomy",
                )

            logger.info(
                "Language-ID detected cluster='%s' with confidence=%.3f. "
                "model_version=%s",
                cluster, confidence, self._model_entry.version,
            )

            return LanguageIdResult(
                cluster=cluster,
                confidence=confidence,
                model_version=self._model_entry.version,
            )

        except Exception as exc:
            logger.error(
                "Language-ID inference failed: %s. "
                "Falling back to cluster='%s'. model_version=%s",
                exc, self._default_cluster, self._model_entry.version,
                exc_info=True,
            )
            return LanguageIdResult(
                cluster=self._default_cluster,
                confidence=0.0,
                model_version=self._model_entry.version,
                fallback_reason=f"inference error: {exc}",
            )
