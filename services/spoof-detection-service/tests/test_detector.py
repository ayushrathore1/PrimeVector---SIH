"""
Tests for the core spoof detection logic.

Verifies the key design constraints from DESIGN.md §4.3:
  - Model version always appears in the detail field (shadow-mode eval)
  - Confidence is derived from model output, not hardcoded
  - Score and confidence are bounded to [0.0, 1.0]
  - Score direction: higher logit → higher suspicion
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest

from config import Settings
from detector import SpoofDetector, _sigmoid, _confidence_from_logit
from language_id import LanguageIdentifier
from model_registry import ModelRegistry, ModelRegistryEntry
from schemas import SpoofDetectionRequest


def _make_request(**kwargs):
    defaults = {
        "call_session_id": "test-session-001",
        "tenant_id": "test-tenant",
        "audio_features": [0.1] * 128,
    }
    defaults.update(kwargs)
    return SpoofDetectionRequest(**defaults)


class FakeModelRegistry(ModelRegistry):
    """Registry pre-loaded with fake models for testing."""

    def __init__(self, models: dict = None):
        self._models = models or {}

    def get_model(self, model_key: str):
        return self._models.get(model_key)

    def list_models(self, prefix: str = ""):
        return [k for k in self._models if k.startswith(prefix)]


def _make_model(logit: float):
    """Create a fake model callable that returns a fixed logit."""
    def model(features):
        return {"logit": logit}
    return model


def _make_detector(models: dict = None, settings_overrides: dict = None):
    """Helper to construct a SpoofDetector with a fake registry."""
    models = models or {}
    registry = FakeModelRegistry(models)
    s = Settings(**(settings_overrides or {}))
    lang_id = LanguageIdentifier(
        registry=registry, default_cluster=s.default_accent_cluster
    )
    return SpoofDetector(
        registry=registry, language_identifier=lang_id, settings=s
    )


# --- Model version in detail field (§4.3 shadow-mode requirement) ---

def test_model_version_in_detail():
    """Model version must appear in the detail field for shadow-mode eval."""
    version = "spoof-detector-v2.1.3"
    models = {
        "spoof-detector/generic": ModelRegistryEntry(
            model=_make_model(logit=1.5),
            version=version,
        )
    }
    detector = _make_detector(models)
    result = detector.detect(_make_request())

    assert result.available is True
    assert version in result.detail
    assert "model=" in result.detail


# --- Confidence varies with logit (not hardcoded) ---

def test_confidence_varies_with_logit():
    """Confidence must be derived from model output, not hardcoded."""
    results = []
    for logit in [-3.0, -0.1, 0.0, 0.1, 3.0]:
        models = {
            "spoof-detector/generic": ModelRegistryEntry(
                model=_make_model(logit=logit),
                version=f"v-logit-{logit}",
            )
        }
        detector = _make_detector(models)
        result = detector.detect(_make_request())
        results.append(result.confidence)

    # Confidence should not be the same for all logits.
    assert len(set(results)) > 1, (
        "Confidence should vary with logit, not be hardcoded"
    )


def test_confidence_low_near_boundary_high_far_from_boundary():
    """Confidence near decision boundary should be low; far should be high."""
    models_uncertain = {
        "spoof-detector/generic": ModelRegistryEntry(
            model=_make_model(logit=0.01),
            version="v-uncertain",
        )
    }
    models_certain = {
        "spoof-detector/generic": ModelRegistryEntry(
            model=_make_model(logit=5.0),
            version="v-certain",
        )
    }
    d_uncertain = _make_detector(models_uncertain)
    d_certain = _make_detector(models_certain)

    r_uncertain = d_uncertain.detect(_make_request())
    r_certain = d_certain.detect(_make_request())

    assert r_certain.confidence > r_uncertain.confidence


# --- Score and confidence bounds ---

@pytest.mark.parametrize("logit", [-100.0, -5.0, -1.0, 0.0, 1.0, 5.0, 100.0])
def test_score_bounded(logit):
    """Output score must always be in [0.0, 1.0]."""
    models = {
        "spoof-detector/generic": ModelRegistryEntry(
            model=_make_model(logit=logit),
            version="v-bounds-test",
        )
    }
    detector = _make_detector(models)
    result = detector.detect(_make_request())
    assert 0.0 <= result.score <= 1.0
    assert 0.0 <= result.confidence <= 1.0


# --- Sigmoid and confidence helpers ---

def test_sigmoid_basic():
    assert abs(_sigmoid(0.0) - 0.5) < 1e-9
    assert _sigmoid(100.0) > 0.999
    assert _sigmoid(-100.0) < 0.001


def test_confidence_from_logit_boundary():
    """At decision boundary (logit=0), confidence should be ~0."""
    assert abs(_confidence_from_logit(0.0)) < 1e-9


def test_confidence_from_logit_high():
    """Far from boundary, confidence should be near 1."""
    assert _confidence_from_logit(10.0) > 0.99
    assert _confidence_from_logit(-10.0) > 0.99


# --- Score directionality ---

def test_higher_logit_means_higher_score():
    """Higher logit → higher suspicion score (positive = more suspicious)."""
    models_low = {
        "spoof-detector/generic": ModelRegistryEntry(
            model=_make_model(logit=-2.0),
            version="v-low",
        )
    }
    models_high = {
        "spoof-detector/generic": ModelRegistryEntry(
            model=_make_model(logit=2.0),
            version="v-high",
        )
    }
    d_low = _make_detector(models_low)
    d_high = _make_detector(models_high)

    r_low = d_low.detect(_make_request())
    r_high = d_high.detect(_make_request())

    assert r_high.score > r_low.score


# --- Model returning score directly (no logit) ---

def test_model_returning_score_directly():
    """Some models may return a pre-computed score instead of logit."""
    def score_model(features):
        return {"score": 0.75}

    models = {
        "spoof-detector/generic": ModelRegistryEntry(
            model=score_model,
            version="v-score-direct",
        )
    }
    detector = _make_detector(models)
    result = detector.detect(_make_request())

    assert result.available is True
    assert abs(result.score - 0.75) < 1e-9
    # Confidence derived from score distance to 0.5, should be > 0.
    assert result.confidence > 0.0
