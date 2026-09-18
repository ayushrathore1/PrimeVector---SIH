"""
DhwaniModelRegistry — ModelRegistry implementation for Dhwani models.

Follows the exact same pattern as DeepfakeModelRegistry in model_registry.py:
  - Loads a trained Dhwani checkpoint from disk
  - Registers as 'spoof-detector/generic' for language-agnostic detection
  - Computes 80-band Log-Mel internally from raw PCM (dual-path support)
  - Falls back to heuristic if checkpoint is not found

Integration:
  config.py:  model_registry_backend = "dhwani"
  main.py:    _create_registry() returns DhwaniModelRegistry

The DhwaniModelRegistry uses chunk-level inference (model/inference.py)
for streaming-compatible prediction smoothing. This is transparent to
the caller — the output still matches the RiskSignal proto shape exactly.

Architecture support:
  - dhwani_baseline_v2.pt → DhwaniV2 (ResNet-SE + BiGRU + Attention, 3-ch)
  - dhwani_baseline_v1.pt → DhwaniBaseline (CNN only, 1-ch)
  - dhwani_advanced_v1.pt → DhwaniAdvanced (CNN + Prosody + SSL)

The loader auto-detects v1 vs v2 from the checkpoint config.
Language-specific models can be added later without API changes by
registering additional entries under 'spoof-detector/{cluster}'.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Checkpoint search paths (relative to spoof-detection-service root)
# v2 is preferred over v1 — loader auto-detects architecture from config.
_CHECKPOINT_SEARCH_PATHS = [
    # v2 (preferred): ml/dhwani/checkpoints/
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "ml", "dhwani",
        "checkpoints", "dhwani_baseline_v2.pt"
    ),
    # v2 fallback: local app directory
    os.path.join(os.path.dirname(__file__), "dhwani_baseline_v2.pt"),
    # v1: ml/dhwani/checkpoints/ (backward compat)
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "ml", "dhwani",
        "checkpoints", "dhwani_baseline_v1.pt"
    ),
    # v1 fallback: local app directory
    os.path.join(os.path.dirname(__file__), "dhwani_baseline_v1.pt"),
]

_ADVANCED_CHECKPOINT_PATHS = [
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "ml", "dhwani",
        "checkpoints", "dhwani_advanced_v1.pt"
    ),
    os.path.join(os.path.dirname(__file__), "dhwani_advanced_v1.pt"),
]


def _find_checkpoint(search_paths: list[str]) -> Optional[str]:
    """Find the first existing checkpoint file from search paths."""
    for path in search_paths:
        resolved = os.path.abspath(path)
        if os.path.isfile(resolved):
            return resolved
    return None


class DhwaniModelRegistry:
    """
    ModelRegistry serving the Dhwani voice deepfake detector.

    Loads the Dhwani model trained on Google Colab and serves it
    through the existing ModelRegistry interface. The API contract
    (SynthesisSignalResponse) is unchanged.

    Usage:
        Set SPOOF_MODEL_REGISTRY_BACKEND=dhwani in environment.
    """

    def __init__(self):
        from model_registry import ModelRegistryEntry, _heuristic_model_fn

        self._entries = {}

        # Try to load Dhwani checkpoint
        checkpoint_path = _find_checkpoint(_CHECKPOINT_SEARCH_PATHS)
        advanced_path = _find_checkpoint(_ADVANCED_CHECKPOINT_PATHS)

        if advanced_path is not None:
            self._load_advanced(advanced_path)
        elif checkpoint_path is not None:
            self._load_baseline(checkpoint_path)
        else:
            logger.warning(
                "No Dhwani checkpoint found in search paths: %s. "
                "Dhwani detection will be unavailable. Falling back "
                "to heuristic for the generic spoof-detector slot.",
                [os.path.abspath(p) for p in _CHECKPOINT_SEARCH_PATHS],
            )

        # Always keep heuristic as fallback
        self._heuristic_entry = ModelRegistryEntry(
            model=_heuristic_model_fn,
            version="acoustic-heuristic-v4.0-fallback",
        )
        if "spoof-detector/generic" not in self._entries:
            self._entries["spoof-detector/generic"] = self._heuristic_entry

        self._entries["spoof-detector/generic-heuristic"] = self._heuristic_entry

        logger.info(
            "DhwaniModelRegistry initialized. Registered models: %s",
            list(self._entries.keys()),
        )

    def _load_baseline(self, checkpoint_path: str):
        """Load Dhwani-Baseline checkpoint."""
        from model_registry import ModelRegistryEntry
        from model.dhwani_baseline import load_dhwani_baseline
        from model.inference import predict_chunks

        model, version, metrics, param_count, mem_mb = load_dhwani_baseline(
            checkpoint_path, device="cpu"
        )

        # Detect v1 vs v2 for logging
        from model.dhwani_baseline import DhwaniV2
        is_v2 = isinstance(model, DhwaniV2)
        arch_label = "DhwaniV2-ResNetSE-BiGRU-Attention" if is_v2 else "DhwaniBaseline-CNN-4block"
        input_label = (
            "3-ch Log-Mel+Delta+Delta² (computed from raw PCM)" if is_v2
            else "80-band Log-Mel (computed from raw PCM)"
        )

        logger.info(
            "%s loaded: version=%s, params=%s, memory=%.1fMB, checkpoint=%s",
            arch_label, version, f"{param_count:,}", mem_mb, checkpoint_path,
        )

        # Create callable that accepts audio_pcm_base64
        def _dhwani_predict(audio_pcm_base64: str) -> dict:
            return predict_chunks(model, audio_pcm_base64)

        self._torch_model = model
        self._trained_entry = ModelRegistryEntry(
            model=_dhwani_predict,
            version=version,
            metadata={
                "architecture": arch_label,
                "input": input_label,
                "n_mels": 80,
                "n_fft": 2048,
                "hop_length": 160,
                "params": param_count,
                "metrics": metrics,
            },
        )
        self._entries["spoof-detector/generic"] = self._trained_entry

    def _load_advanced(self, checkpoint_path: str):
        """Load Dhwani-Advanced checkpoint."""
        from model_registry import ModelRegistryEntry
        from model.dhwani_advanced import load_dhwani_advanced
        from model.inference import predict_chunks

        model, version, metrics = load_dhwani_advanced(
            checkpoint_path, device="cpu"
        )

        param_count = sum(p.numel() for p in model.parameters())
        mem_mb = sum(
            p.numel() * p.element_size() for p in model.parameters()
        ) / (1024 * 1024)

        logger.info(
            "Dhwani-Advanced loaded: version=%s, params=%s, memory=%.1fMB, "
            "checkpoint=%s",
            version, f"{param_count:,}", mem_mb, checkpoint_path,
        )

        # For advanced model, we only use the mel branch for PCM inference
        # (prosody and SSL require separate feature extraction pipelines)
        def _dhwani_predict(audio_pcm_base64: str) -> dict:
            return predict_chunks(model, audio_pcm_base64)

        self._torch_model = model
        self._trained_entry = ModelRegistryEntry(
            model=_dhwani_predict,
            version=version,
            metadata={
                "architecture": "DhwaniAdvanced-MultiBranch",
                "input": "80-band Log-Mel + optional prosody + optional SSL",
                "n_mels": 80,
                "params": param_count,
                "metrics": metrics,
            },
        )
        self._entries["spoof-detector/generic"] = self._trained_entry

    @property
    def trained_entry(self):
        """The trained Dhwani model entry, for direct access by detector."""
        return self._trained_entry if hasattr(self, "_trained_entry") else None

    @property
    def heuristic_entry(self):
        """The heuristic fallback entry."""
        return self._heuristic_entry

    def get_model(self, model_key: str):
        return self._entries.get(model_key)

    def list_models(self, prefix: str = "") -> list[str]:
        return [k for k in self._entries if k.startswith(prefix)]
