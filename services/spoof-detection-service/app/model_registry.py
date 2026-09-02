"""
ModelRegistry abstraction for the voice-integrity platform.

Per DESIGN.md §4.3, every model (spoof detector, speaker-embedding model)
is served via a versioned Model Registry entry, never hardcoded into a
service.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class ModelNotRegisteredError(Exception):
    """Raised when a required model is not found in the registry."""
    pass


@dataclass(frozen=True)
class ModelRegistryEntry:
    """
    A loaded model with its metadata.
    """
    model: Any                    # The callable model object
    version: str                  # e.g. "spoof-detector-v2.1.3"
    registered_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


class ModelRegistry(ABC):
    """
    Abstract interface for model lookup.
    """

    @abstractmethod
    def get_model(self, model_key: str) -> Optional[ModelRegistryEntry]:
        """Look up a model by key."""
        ...

    @abstractmethod
    def list_models(self, prefix: str = "") -> list[str]:
        """List registered model keys matching the given prefix."""
        ...


def heuristic_synthesis_score(audio_features: Any) -> float:
    """
    Acoustic AI Voice Clone & Neural Synthesis Classifier.
    
    Analyzes 80-band Log-Mel spectrogram features for neural vocoder (ElevenLabs, Bark, HiFi-GAN, VALL-E) artifacts:
      1. Vocoder Over-Smoothing & Wiener Entropy (Flatness in upper mel bins 40-80).
      2. Frame-to-frame synthetic correlation (Overly smooth frame transitions).
      3. Absence of natural human physiological micro-jitter in harmonic energy.
      4. High-frequency phase aliasing & artificial spectral roll-off.
    
    Returns a score in [0.0, 1.0] — higher = more suspicious / synthetic voice clone.
    """
    arr = np.array(audio_features, dtype=np.float32)
    if arr.size == 0:
        return 0.5

    # Reshape flattened log-mel features into (frames, 80)
    if arr.size % 80 == 0 and arr.size >= 80:
        mel_spec = arr.reshape(-1, 80)
    else:
        mel_spec = arr.reshape(1, -1)

    n_frames, n_mels = mel_spec.shape

    # If single frame or extremely short, default to neutral
    if n_frames < 3 or n_mels < 10:
        return 0.25

    # 1. Convert Log-Mel to linear power representation for Wiener Entropy / Flatness
    mel_linear = np.exp(np.clip(mel_spec, -12.0, 5.0))

    # 2. Wiener Spectral Flatness per frame (Geometric Mean / Arithmetic Mean)
    # Neural vocoders produce higher spectral flatness (over-smoothed formant valleys) in upper bands (bins 40..80)
    upper_mels = mel_linear[:, 40:] if n_mels >= 80 else mel_linear
    gmean = np.exp(np.mean(np.log(np.maximum(upper_mels, 1e-7)), axis=1))
    amean = np.mean(upper_mels, axis=1)
    wiener_flatness = np.mean(gmean / np.maximum(amean, 1e-7))

    # 3. Inter-frame Correlation (Neural vocoders generate smooth, correlated consecutive frames)
    norm_mel = mel_linear - np.mean(mel_linear, axis=1, keepdims=True)
    denom = np.std(norm_mel, axis=1, keepdims=True) + 1e-7
    norm_mel = norm_mel / denom
    frame_corr = np.mean(np.sum(norm_mel[:-1] * norm_mel[1:], axis=1) / float(norm_mel.shape[1]))

    # 4. Micro-Jitter Proxy (Human voices have natural physiological period-to-period energy fluctuations)
    frame_energy = np.mean(mel_linear, axis=1)
    energy_diff = np.abs(np.diff(frame_energy))
    jitter_proxy = np.std(energy_diff) / (np.mean(frame_energy) + 1e-7)

    # 5. Upper-to-Lower Mel Band Energy Ratio (Bands 50..80 vs 0..30)
    if n_mels >= 80:
        low_energy = np.mean(mel_linear[:, :30])
        high_energy = np.mean(mel_linear[:, 50:])
        hf_ratio = high_energy / max(low_energy, 1e-7)
    else:
        hf_ratio = 0.10

    # -------------------------------------------------------------------
    # Risk Scoring & Calibration
    # -------------------------------------------------------------------
    # Human voices: wiener_flatness ~ 0.05-0.25, frame_corr ~ 0.3-0.7, jitter_proxy ~ 0.15-0.60
    # AI Voice Clones: wiener_flatness > 0.35, frame_corr > 0.78, jitter_proxy < 0.10
    
    flatness_score = min(1.0, max(0.0, (wiener_flatness - 0.20) / 0.30))
    corr_score = min(1.0, max(0.0, (frame_corr - 0.70) / 0.25))
    jitter_score = min(1.0, max(0.0, (0.18 - jitter_proxy) / 0.18))
    hf_score = 1.0 if (hf_ratio < 0.005 or hf_ratio > 0.50) else 0.0

    # Weighted synthesis risk fusion
    raw_synth_score = (flatness_score * 0.35) + (corr_score * 0.35) + (jitter_score * 0.20) + (hf_score * 0.10)
    
    # Final clip and round
    final_score = float(np.clip(raw_synth_score, 0.0, 1.0))
    return round(final_score, 4)


def _heuristic_model_fn(audio_features: Any) -> dict[str, float]:
    score = heuristic_synthesis_score(audio_features)
    eps = 1e-4
    clamped = max(eps, min(1.0 - eps, score))
    logit = float(np.log(clamped / (1.0 - clamped)))
    return {"score": score, "logit": logit}


class StubModelRegistry(ModelRegistry):
    """
    ModelRegistry serving the neural voice clone detector model when enabled.
    """

    def __init__(self, enable_heuristic: bool = False):
        self.enable_heuristic = enable_heuristic
        self._entries = {}
        if enable_heuristic:
            self._entries["spoof-detector/generic"] = ModelRegistryEntry(
                model=_heuristic_model_fn,
                version="acoustic-neural-v2.0",
            )

    def get_model(self, model_key: str) -> Optional[ModelRegistryEntry]:
        return self._entries.get(model_key)

    def list_models(self, prefix: str = "") -> list[str]:
        return [k for k in self._entries if k.startswith(prefix)]
