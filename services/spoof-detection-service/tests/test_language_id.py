"""
Tests for language/accent identification and model routing.

Per DESIGN.md §4.4:
  - Language/accent ID runs as a first-pass classifier
  - Routes to accent-cluster-specific model if registered
  - Falls back to language-agnostic model otherwise
  - Logs which path was taken (for per-cluster fairness reporting)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest

from config import Settings
from detector import SpoofDetector
from language_id import (
    LanguageIdentifier,
    LanguageIdResult,
    KNOWN_CLUSTERS,
)
from model_registry import ModelRegistry, ModelRegistryEntry
from schemas import SpoofDetectionRequest


def _make_request(**kwargs):
    defaults = {
        "call_session_id": "test-lang-session",
        "tenant_id": "test-tenant",
        "audio_features": [0.1] * 128,
    }
    defaults.update(kwargs)
    return SpoofDetectionRequest(**defaults)


class FakeModelRegistry(ModelRegistry):
    def __init__(self, models=None):
        self._models = models or {}

    def get_model(self, key):
        return self._models.get(key)

    def list_models(self, prefix=""):
        return [k for k in self._models if k.startswith(prefix)]


# =====================================================================
# LanguageIdentifier unit tests
# =====================================================================

def test_no_language_id_model_falls_back_to_generic():
    """When no language-ID model is registered, default to 'generic'."""
    registry = FakeModelRegistry()
    lang_id = LanguageIdentifier(registry=registry, default_cluster="generic")
    result = lang_id.identify([0.1] * 128)

    assert result.cluster == "generic"
    assert result.fallback_reason is not None
    assert "not registered" in result.fallback_reason


def test_language_id_returns_known_cluster():
    """A working language-ID model returns a known cluster."""
    def lang_model(features):
        return {"cluster": "hi-IN", "confidence": 0.92}

    registry = FakeModelRegistry({
        "language-id/default": ModelRegistryEntry(
            model=lang_model,
            version="lang-id-v1.0",
        )
    })
    lang_id = LanguageIdentifier(registry=registry)
    result = lang_id.identify([0.1] * 128)

    assert result.cluster == "hi-IN"
    assert result.confidence == 0.92
    assert result.model_version == "lang-id-v1.0"
    assert result.fallback_reason is None


def test_language_id_unknown_cluster_falls_back():
    """If the model returns an unknown cluster, fall back to generic."""
    def lang_model(features):
        return {"cluster": "xx-UNKNOWN", "confidence": 0.5}

    registry = FakeModelRegistry({
        "language-id/default": ModelRegistryEntry(
            model=lang_model,
            version="lang-id-v1.0",
        )
    })
    lang_id = LanguageIdentifier(registry=registry)
    result = lang_id.identify([0.1] * 128)

    assert result.cluster == "generic"
    assert result.fallback_reason is not None
    assert "not in taxonomy" in result.fallback_reason


def test_language_id_exception_falls_back():
    """If the language-ID model throws, fall back to generic."""
    def failing_lang_model(features):
        raise RuntimeError("ONNX error")

    registry = FakeModelRegistry({
        "language-id/default": ModelRegistryEntry(
            model=failing_lang_model,
            version="lang-id-v1.0",
        )
    })
    lang_id = LanguageIdentifier(registry=registry)
    result = lang_id.identify([0.1] * 128)

    assert result.cluster == "generic"
    assert result.fallback_reason is not None
    assert "inference error" in result.fallback_reason


def test_language_id_preserves_model_version_on_failure():
    """Even on failure, the language-ID model version should be tracked."""
    def failing_lang_model(features):
        raise RuntimeError("model error")

    registry = FakeModelRegistry({
        "language-id/default": ModelRegistryEntry(
            model=failing_lang_model,
            version="lang-id-v2.3",
        )
    })
    lang_id = LanguageIdentifier(registry=registry)
    result = lang_id.identify([0.1] * 128)

    assert result.model_version == "lang-id-v2.3"


# =====================================================================
# End-to-end cluster routing in the full detector
# =====================================================================

def test_cluster_specific_model_used_when_available():
    """When a cluster-specific model is registered, it should be used."""
    def lang_model(features):
        return {"cluster": "ta-IN", "confidence": 0.85}

    def generic_spoof(features):
        return {"logit": 0.5}

    def tamil_spoof(features):
        return {"logit": 2.5}  # Different logit so we can distinguish

    registry = FakeModelRegistry({
        "language-id/default": ModelRegistryEntry(
            model=lang_model, version="lang-v1"),
        "spoof-detector/generic": ModelRegistryEntry(
            model=generic_spoof, version="generic-v1"),
        "spoof-detector/ta-IN": ModelRegistryEntry(
            model=tamil_spoof, version="tamil-v1"),
    })

    s = Settings()
    lang_id = LanguageIdentifier(
        registry=registry, default_cluster=s.default_accent_cluster
    )
    detector = SpoofDetector(
        registry=registry, language_identifier=lang_id, settings=s
    )
    result = detector.detect(_make_request())

    assert result.available is True
    assert "tamil-v1" in result.detail
    assert "cluster-specific" in result.detail


def test_falls_back_to_generic_when_no_cluster_model():
    """When no cluster-specific model exists, use generic."""
    def lang_model(features):
        return {"cluster": "bn-IN", "confidence": 0.9}

    def generic_spoof(features):
        return {"logit": 1.0}

    registry = FakeModelRegistry({
        "language-id/default": ModelRegistryEntry(
            model=lang_model, version="lang-v1"),
        "spoof-detector/generic": ModelRegistryEntry(
            model=generic_spoof, version="generic-v2"),
        # No spoof-detector/bn-IN registered
    })

    s = Settings()
    lang_id = LanguageIdentifier(
        registry=registry, default_cluster=s.default_accent_cluster
    )
    detector = SpoofDetector(
        registry=registry, language_identifier=lang_id, settings=s
    )
    result = detector.detect(_make_request())

    assert result.available is True
    assert "generic-v2" in result.detail
    assert "fallback" in result.detail


def test_detail_always_includes_cluster():
    """The detail field should always include which cluster was detected."""
    def lang_model(features):
        return {"cluster": "ml-IN", "confidence": 0.7}

    def generic_spoof(features):
        return {"logit": 0.0}

    registry = FakeModelRegistry({
        "language-id/default": ModelRegistryEntry(
            model=lang_model, version="lang-v1"),
        "spoof-detector/generic": ModelRegistryEntry(
            model=generic_spoof, version="generic-v1"),
    })

    s = Settings()
    lang_id = LanguageIdentifier(
        registry=registry, default_cluster=s.default_accent_cluster
    )
    detector = SpoofDetector(
        registry=registry, language_identifier=lang_id, settings=s
    )
    result = detector.detect(_make_request())
    assert "ml-IN" in result.detail


# =====================================================================
# Known clusters taxonomy
# =====================================================================

def test_known_clusters_include_major_indian_languages():
    """Verify the cluster taxonomy includes expected languages."""
    expected = {"hi-IN", "en-IN", "ta-IN", "te-IN", "bn-IN"}
    assert expected.issubset(KNOWN_CLUSTERS)


def test_known_clusters_count():
    """Verify we have 10 clusters (matching the implementation plan)."""
    assert len(KNOWN_CLUSTERS) == 10
