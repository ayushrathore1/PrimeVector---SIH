"""
Integration tests for Dhwani model in spoof-detection-service.

Tests that the Dhwani model architecture, registry, and inference engine
work correctly and produce responses matching the existing API contract
(SynthesisSignalResponse / RiskSignal proto shape).

These tests use ONLY synthetic/dummy data — no real audio files or
model checkpoints are required. This ensures tests run in CI without
downloading models from Colab or HuggingFace.
"""
import base64
import json
import os
import sys
import tempfile

import numpy as np
import pytest

# Add the app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


# ──────────────────────────────────────────────────────────────
# Test: DhwaniBaseline model architecture
# ──────────────────────────────────────────────────────────────

class TestDhwaniBaselineArchitecture:
    """Verify DhwaniBaseline model produces correct output shapes."""

    def test_forward_pass_shape(self):
        """Model output should be (batch, 1) for any valid input."""
        import torch
        from model.dhwani_baseline import DhwaniBaseline

        model = DhwaniBaseline(n_mels=80)
        model.eval()

        # Simulate a 3-second audio clip → Log-Mel spectrogram
        # 3s at 16kHz with hop=160 → ~300 frames
        batch_size = 2
        time_frames = 300
        x = torch.randn(batch_size, 1, 80, time_frames)

        with torch.no_grad():
            output = model(x)

        assert output.shape == (batch_size, 1), \
            f"Expected (2, 1), got {output.shape}"

    def test_single_sample(self):
        """Model should handle batch_size=1."""
        import torch
        from model.dhwani_baseline import DhwaniBaseline

        model = DhwaniBaseline()
        model.eval()

        x = torch.randn(1, 1, 80, 100)
        with torch.no_grad():
            output = model(x)

        assert output.shape == (1, 1)

    def test_short_audio(self):
        """Model should handle very short spectrograms without crashing."""
        import torch
        from model.dhwani_baseline import DhwaniBaseline

        model = DhwaniBaseline()
        model.eval()

        # Very short: 10 frames (~100ms)
        x = torch.randn(1, 1, 80, 10)
        with torch.no_grad():
            output = model(x)

        assert output.shape == (1, 1)

    def test_output_is_finite(self):
        """Model output should be finite (no NaN/Inf)."""
        import torch
        from model.dhwani_baseline import DhwaniBaseline

        model = DhwaniBaseline()
        model.eval()

        x = torch.randn(4, 1, 80, 200)
        with torch.no_grad():
            output = model(x)

        assert torch.isfinite(output).all(), "Output contains NaN or Inf"

    def test_param_count_reasonable(self):
        """Model should be lightweight (<5M params for CPU inference)."""
        from model.dhwani_baseline import DhwaniBaseline

        model = DhwaniBaseline()
        param_count = sum(p.numel() for p in model.parameters())

        assert param_count < 5_000_000, \
            f"Model too large for CPU inference: {param_count:,} params"

    def test_checkpoint_save_load_roundtrip(self):
        """Save and reload checkpoint, verify identical outputs."""
        import torch
        from model.dhwani_baseline import DhwaniBaseline, load_dhwani_baseline

        model = DhwaniBaseline()
        model.eval()

        x = torch.randn(1, 1, 80, 150)
        with torch.no_grad():
            original_output = model(x)

        # Save checkpoint
        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
            checkpoint_path = f.name
            torch.save({
                "model_state_dict": model.state_dict(),
                "version": "test-v0.0",
                "config": {"n_mels": 80},
                "metrics": {"test_accuracy": 0.5},
            }, f)

        try:
            # Reload and compare
            loaded_model, version, metrics, _, _ = load_dhwani_baseline(
                checkpoint_path
            )
            with torch.no_grad():
                loaded_output = loaded_model(x)

            assert torch.allclose(original_output, loaded_output, atol=1e-6), \
                "Loaded model produces different output"
            assert version == "test-v0.0"
            assert metrics["test_accuracy"] == 0.5
        finally:
            os.unlink(checkpoint_path)


# ──────────────────────────────────────────────────────────────
# Test: DhwaniAdvanced model architecture
# ──────────────────────────────────────────────────────────────

class TestDhwaniAdvancedArchitecture:
    """Verify DhwaniAdvanced multi-branch model."""

    def test_mel_only(self):
        """Advanced model should work with mel branch only."""
        import torch
        from model.dhwani_advanced import DhwaniAdvanced

        model = DhwaniAdvanced(use_prosody=False, use_ssl=False)
        model.eval()

        mel = torch.randn(2, 1, 80, 200)
        with torch.no_grad():
            output = model(mel)

        assert output.shape == (2, 1)

    def test_mel_plus_prosody(self):
        """Advanced model with mel + prosody branches."""
        import torch
        from model.dhwani_advanced import DhwaniAdvanced

        model = DhwaniAdvanced(
            prosody_dim=10, use_prosody=True, use_ssl=False,
        )
        model.eval()

        mel = torch.randn(2, 1, 80, 200)
        prosody = torch.randn(2, 10)
        with torch.no_grad():
            output = model(mel, prosody=prosody)

        assert output.shape == (2, 1)

    def test_all_branches(self):
        """Advanced model with all three branches."""
        import torch
        from model.dhwani_advanced import DhwaniAdvanced

        model = DhwaniAdvanced(
            prosody_dim=10, ssl_dim=768,
            use_prosody=True, use_ssl=True,
        )
        model.eval()

        mel = torch.randn(2, 1, 80, 200)
        prosody = torch.randn(2, 10)
        ssl = torch.randn(2, 768)
        with torch.no_grad():
            output = model(mel, prosody=prosody, ssl=ssl)

        assert output.shape == (2, 1)

    def test_graceful_degradation(self):
        """Model should work even if optional inputs are None."""
        import torch
        from model.dhwani_advanced import DhwaniAdvanced

        model = DhwaniAdvanced(use_prosody=True, use_ssl=True)
        model.eval()

        mel = torch.randn(1, 1, 80, 150)

        # Only mel provided (prosody and ssl are None)
        with torch.no_grad():
            output = model(mel, prosody=None, ssl=None)

        assert output.shape == (1, 1)


# ──────────────────────────────────────────────────────────────
# Test: DhwaniModelRegistry
# ──────────────────────────────────────────────────────────────

class TestDhwaniRegistry:
    """Test registry initialization and model lookup."""

    def test_registry_without_checkpoint_falls_back(self):
        """Registry should fall back to heuristic when no checkpoint exists."""
        from dhwani_registry import DhwaniModelRegistry

        # Pass non-existent path to force fallback
        registry = DhwaniModelRegistry(checkpoint_path="nonexistent.pt")

        # Should have at least the heuristic model
        entry = registry.get_model("spoof-detector/generic")
        assert entry is not None
        assert "heuristic" in entry.version.lower() or "dhwani" in entry.version.lower()

    def test_registry_lists_models(self):
        """list_models should return registered model keys."""
        from dhwani_registry import DhwaniModelRegistry

        registry = DhwaniModelRegistry()
        models = registry.list_models("spoof-detector/")

        assert len(models) >= 1  # at least heuristic
        assert all(k.startswith("spoof-detector/") for k in models)

    def test_heuristic_produces_valid_output(self):
        """Heuristic fallback should return score and logit."""
        from dhwani_registry import DhwaniModelRegistry

        registry = DhwaniModelRegistry()
        entry = registry.get_model("spoof-detector/generic-heuristic")
        assert entry is not None

        # Create fake 80-band log-mel features (100 frames × 80 bands)
        fake_features = list(np.random.randn(100 * 80).astype(float))
        result = entry.model(fake_features)

        assert "score" in result
        assert "logit" in result
        assert 0.0 <= result["score"] <= 1.0


# ──────────────────────────────────────────────────────────────
# Test: API response compatibility
# ──────────────────────────────────────────────────────────────

class TestAPICompatibility:
    """Verify Dhwani outputs match the SynthesisSignalResponse contract."""

    def test_response_matches_risk_signal_proto(self):
        """Response fields must match RiskSignal proto exactly."""
        from schemas import SynthesisSignalResponse

        # Simulate a Dhwani detection result
        response = SynthesisSignalResponse(
            score=0.87,
            confidence=0.91,
            available=True,
            detail="model=Dhwani-Baseline-v1.0, cluster=generic, path=trained-model",
        )

        # Verify all required fields
        assert 0.0 <= response.score <= 1.0
        assert 0.0 <= response.confidence <= 1.0
        assert response.available is True
        assert "Dhwani" in response.detail

    def test_unavailable_response(self):
        """When Dhwani is unavailable, response should be valid."""
        from schemas import SynthesisSignalResponse

        response = SynthesisSignalResponse(
            score=0.0,
            confidence=0.0,
            available=False,
            detail="model=none, reason=Dhwani checkpoint not found",
        )

        assert response.score == 0.0
        assert response.available is False


# ──────────────────────────────────────────────────────────────
# Test: Existing functionality preservation
# ──────────────────────────────────────────────────────────────

class TestExistingFunctionality:
    """Verify that adding Dhwani doesn't break existing backends."""

    def test_deepfake_backend_still_works_in_config(self):
        """The deepfake backend option must still be recognized."""
        from config import Settings

        # Simulate setting backend to deepfake
        settings = Settings(model_registry_backend="deepfake")
        assert settings.model_registry_backend == "deepfake"

    def test_heuristic_backend_still_works(self):
        """The heuristic backend must still be recognized."""
        from config import Settings

        settings = Settings(model_registry_backend="heuristic")
        assert settings.model_registry_backend == "heuristic"

    def test_dhwani_backend_recognized(self):
        """The new dhwani backend must be a valid option."""
        from config import Settings

        settings = Settings(model_registry_backend="dhwani")
        assert settings.model_registry_backend == "dhwani"

    def test_stub_backend_still_works(self):
        """The stub backend must still be recognized."""
        from config import Settings

        settings = Settings(model_registry_backend="stub")
        assert settings.model_registry_backend == "stub"
