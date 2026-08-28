"""
Tests for failure/timeout/missing-model behavior.

Critical invariant from fusion.py design decision 4:
  "Missing/unavailable signals degrade gracefully rather than being
   treated as '0 risk' — an unavailable signal is evidence of nothing,
   not evidence of safety."

Every failure path in the detector must produce available=false.
A failed detection must NEVER look like "clean audio" to the
downstream fusion engine.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import time
import pytest

from config import Settings
from detector import SpoofDetector
from language_id import LanguageIdentifier
from model_registry import ModelRegistry, ModelRegistryEntry, StubModelRegistry
from schemas import SpoofDetectionRequest


def _make_request(**kwargs):
    defaults = {
        "call_session_id": "test-fail-session",
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


def _make_detector_with_registry(registry, settings_overrides=None):
    s = Settings(**(settings_overrides or {}))
    lang_id = LanguageIdentifier(
        registry=registry, default_cluster=s.default_accent_cluster
    )
    return SpoofDetector(
        registry=registry, language_identifier=lang_id, settings=s
    )


# --- No model registered (stub registry) ---

def test_stub_registry_returns_unavailable():
    """With StubModelRegistry, every detection must return available=false."""
    registry = StubModelRegistry()
    detector = _make_detector_with_registry(registry)
    result = detector.detect(_make_request())

    assert result.available is False
    assert "no model registered" in result.detail


def test_no_model_never_returns_low_score_as_available():
    """
    A missing model must not produce available=true with score=0.0.
    That would tell fusion 'we checked and it's clean' — which is a lie.
    """
    registry = StubModelRegistry()
    detector = _make_detector_with_registry(registry)
    result = detector.detect(_make_request())

    # The key invariant: available must be false.
    assert result.available is False


# --- Model raises exception ---

def test_model_exception_returns_unavailable():
    """A model that throws must result in available=false."""
    def exploding_model(features):
        raise RuntimeError("GPU out of memory")

    registry = FakeModelRegistry({
        "spoof-detector/generic": ModelRegistryEntry(
            model=exploding_model,
            version="v-exploding",
        )
    })
    detector = _make_detector_with_registry(registry)
    result = detector.detect(_make_request())

    assert result.available is False
    assert "inference error" in result.detail
    assert "v-exploding" in result.detail  # version still present


# --- Model times out ---

def test_model_timeout_returns_unavailable():
    """A model that takes too long must result in available=false."""
    def slow_model(features):
        time.sleep(2.0)  # Way longer than the test timeout
        return {"logit": 0.5}

    registry = FakeModelRegistry({
        "spoof-detector/generic": ModelRegistryEntry(
            model=slow_model,
            version="v-slow",
        )
    })
    # Set a very short timeout for the test.
    detector = _make_detector_with_registry(
        registry,
        settings_overrides={"inference_timeout_ms": 50},
    )
    result = detector.detect(_make_request())

    assert result.available is False
    assert "timeout" in result.detail.lower()
    assert "v-slow" in result.detail  # version still present


# --- Model returns bad output ---

def test_model_bad_output_returns_unavailable():
    """A model returning unexpected keys must result in available=false."""
    def bad_model(features):
        return {"unexpected_key": 42}

    registry = FakeModelRegistry({
        "spoof-detector/generic": ModelRegistryEntry(
            model=bad_model,
            version="v-bad-output",
        )
    })
    detector = _make_detector_with_registry(registry)
    result = detector.detect(_make_request())

    assert result.available is False
    assert "v-bad-output" in result.detail


# --- Failure detail always includes model version ---

def test_failure_detail_always_includes_version():
    """Even on failure, the model version must be in the detail field."""
    test_version = "v-fail-detail-test-42"

    def failing_model(features):
        raise ValueError("something went wrong")

    registry = FakeModelRegistry({
        "spoof-detector/generic": ModelRegistryEntry(
            model=failing_model,
            version=test_version,
        )
    })
    detector = _make_detector_with_registry(registry)
    result = detector.detect(_make_request())

    assert test_version in result.detail


# --- Multiple consecutive failures don't corrupt state ---

def test_failures_do_not_corrupt_subsequent_calls():
    """After a failure, the next call should behave normally."""
    call_count = 0

    def flaky_model(features):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("transient failure")
        return {"logit": 1.0}

    registry = FakeModelRegistry({
        "spoof-detector/generic": ModelRegistryEntry(
            model=flaky_model,
            version="v-flaky",
        )
    })
    detector = _make_detector_with_registry(registry)

    # First call fails.
    r1 = detector.detect(_make_request())
    assert r1.available is False

    # Second call succeeds.
    r2 = detector.detect(_make_request())
    assert r2.available is True
    assert r2.score > 0.0
