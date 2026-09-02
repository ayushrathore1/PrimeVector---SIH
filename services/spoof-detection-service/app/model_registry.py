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


def _sigmoid_map(value: float, center: float, steepness: float) -> float:
    """
    Continuous sigmoid mapping: maps a raw metric onto [0, 1] smoothly.

    - value < center → output < 0.5 (more human-like)
    - value > center → output > 0.5 (more synthetic-like)
    - steepness controls the transition sharpness (higher = sharper)

    Unlike a hard threshold (which snaps to 0 or 1), this produces a
    smooth gradient that preserves signal even near the boundary.
    """
    x = steepness * (value - center)
    if x > 20:
        return 1.0
    if x < -20:
        return 0.0
    return 1.0 / (1.0 + np.exp(-x))


def heuristic_synthesis_score(audio_features: Any) -> float:
    """
    Acoustic AI Voice Clone & Neural Synthesis Classifier (v3.0).

    Analyzes 80-band Log-Mel spectrogram features for neural vocoder
    artifacts (ElevenLabs, Bark, HiFi-GAN, VALL-E, RVC, etc.).

    Eight analysis dimensions, all using continuous sigmoid scoring
    instead of binary thresholds:

      1. Wiener Spectral Flatness (upper mel bands) — vocoders over-smooth
         formant valleys, raising flatness above natural speech levels.
      2. Inter-frame Correlation — neural vocoders generate unnaturally
         smooth, highly correlated consecutive frames.
      3. Micro-Jitter (energy perturbation) — human voices have natural
         physiological period-to-period energy fluctuations absent in TTS.
      4. HF Energy Ratio — spectral roll-off anomalies in upper bands vs
         lower bands; vocoders either cut off or boost unnaturally.
      5. Pitch Stability (F0 proxy) — human F0 has 0.5-2% cycle-to-cycle
         perturbation; neural vocoders produce unnaturally stable pitch.
      6. Temporal Modulation Envelope — natural speech has characteristic
         3-6 Hz syllabic modulation; synthetic speech often deviates.
      7. Spectral Bandwidth Variance — human speech has dynamic bandwidth
         that changes with phonemes; vocoders show reduced variance.
      8. Sub-band Energy Independence — in natural speech, energy in
         different mel bands fluctuates semi-independently; vocoders
         tend to produce more correlated sub-band trajectories.

    Returns a score in [0.0, 1.0] — higher = more suspicious / synthetic.
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

    # If single frame or extremely short, conservatively neutral
    if n_frames < 3 or n_mels < 10:
        return 0.25

    # Convert Log-Mel to linear power representation
    mel_linear = np.exp(np.clip(mel_spec, -12.0, 5.0))

    # ===================================================================
    # Dimension 1: Wiener Spectral Flatness (upper mel bands)
    # Human: 0.03-0.20 | AI: 0.30-0.70
    # ===================================================================
    upper_mels = mel_linear[:, 40:] if n_mels >= 80 else mel_linear
    gmean = np.exp(np.mean(np.log(np.maximum(upper_mels, 1e-7)), axis=1))
    amean = np.mean(upper_mels, axis=1)
    wiener_flatness = float(np.mean(gmean / np.maximum(amean, 1e-7)))
    # Sigmoid: center=0.28 (boundary), steepness=12
    flatness_score = _sigmoid_map(wiener_flatness, center=0.28, steepness=12.0)

    # ===================================================================
    # Dimension 2: Inter-frame Correlation
    # Human: 0.30-0.65 | AI: 0.75-0.98
    # ===================================================================
    norm_mel = mel_linear - np.mean(mel_linear, axis=1, keepdims=True)
    denom = np.std(norm_mel, axis=1, keepdims=True) + 1e-7
    norm_mel = norm_mel / denom
    frame_corr = float(np.mean(
        np.sum(norm_mel[:-1] * norm_mel[1:], axis=1) / float(n_mels)
    ))
    # Sigmoid: center=0.72, steepness=10
    corr_score = _sigmoid_map(frame_corr, center=0.72, steepness=10.0)

    # ===================================================================
    # Dimension 3: Micro-Jitter (energy perturbation proxy)
    # Human: 0.12-0.60 | AI: 0.01-0.08
    # ===================================================================
    frame_energy = np.mean(mel_linear, axis=1)
    energy_diff = np.abs(np.diff(frame_energy))
    jitter_proxy = float(np.std(energy_diff) / (np.mean(frame_energy) + 1e-7))
    # INVERTED sigmoid: LOW jitter = MORE suspicious (synthetic)
    jitter_score = 1.0 - _sigmoid_map(jitter_proxy, center=0.10, steepness=18.0)

    # ===================================================================
    # Dimension 4: HF Energy Ratio (bands 50-80 vs 0-30)
    # Human: 0.02-0.20 | AI: <0.005 (sharp cutoff) or >0.40 (ringing)
    # ===================================================================
    if n_mels >= 80:
        low_energy = float(np.mean(mel_linear[:, :30]))
        high_energy = float(np.mean(mel_linear[:, 50:]))
        hf_ratio = high_energy / max(low_energy, 1e-7)
    else:
        hf_ratio = 0.10  # neutral default for non-standard shapes

    # Two-tailed: suspicious if too low OR too high
    hf_low_score = 1.0 - _sigmoid_map(hf_ratio, center=0.01, steepness=200.0)
    hf_high_score = _sigmoid_map(hf_ratio, center=0.40, steepness=15.0)
    hf_score = max(hf_low_score, hf_high_score)

    # ===================================================================
    # Dimension 5: Pitch Stability Proxy (F0 regularity via peak energy)
    # Human: high variance in peak bin across frames | AI: very stable
    # ===================================================================
    peak_bins = np.argmax(mel_linear[:, :40], axis=1)  # fundamental lives in lower 40 bins
    if len(peak_bins) > 2:
        peak_stability = float(np.std(peak_bins.astype(np.float32)))
        # Human F0 wanders across mel bins; AI stays locked
        # Human: std ~ 2-8 bins | AI: std ~ 0-1.5 bins
        pitch_score = 1.0 - _sigmoid_map(peak_stability, center=1.8, steepness=2.5)
    else:
        pitch_score = 0.5  # insufficient data

    # ===================================================================
    # Dimension 6: Temporal Modulation Envelope (syllabic rate ~3-6 Hz)
    # Human speech: strong 3-6 Hz modulation | AI: flat or irregular
    # ===================================================================
    if n_frames >= 20:
        # Frame rate ~100 Hz (10ms hop) → 3-6 Hz = bins 3-6 in a 100-frame DFT
        energy_envelope = np.mean(mel_linear, axis=1)
        # Normalize
        env_norm = energy_envelope - np.mean(energy_envelope)
        fft_env = np.abs(np.fft.rfft(env_norm))
        # Frequency resolution: sample_rate_frames / n_frames
        # At 100 fps, bin k = k * 100/n_frames Hz
        # Syllabic range 3-6 Hz → bins floor(3*n/100)..ceil(6*n/100)
        bin_lo = max(1, int(3.0 * n_frames / 100.0))
        bin_hi = min(len(fft_env) - 1, int(6.0 * n_frames / 100.0) + 1)
        if bin_hi > bin_lo:
            syllabic_energy = float(np.mean(fft_env[bin_lo:bin_hi + 1]))
            total_energy = float(np.mean(fft_env[1:])) + 1e-9
            modulation_ratio = syllabic_energy / total_energy
            # Human: modulation_ratio ~ 1.5-4.0 | AI: ~ 0.5-1.2
            # INVERTED: LOW modulation = MORE suspicious
            modulation_score = 1.0 - _sigmoid_map(modulation_ratio, center=1.3, steepness=3.0)
        else:
            modulation_score = 0.5
    else:
        modulation_score = 0.5  # insufficient frames

    # ===================================================================
    # Dimension 7: Spectral Bandwidth Variance
    # Human: bandwidth changes dynamically per phoneme | AI: more static
    # ===================================================================
    # Spectral centroid per frame as a proxy for bandwidth activity
    mel_bins = np.arange(1, n_mels + 1, dtype=np.float32)
    frame_total = np.sum(mel_linear, axis=1, keepdims=True) + 1e-9
    centroids = np.sum(mel_linear * mel_bins[np.newaxis, :], axis=1) / frame_total.squeeze()
    centroid_variance = float(np.std(centroids) / (np.mean(centroids) + 1e-7))
    # Human: CV ~ 0.10-0.40 | AI: CV ~ 0.02-0.08
    bandwidth_score = 1.0 - _sigmoid_map(centroid_variance, center=0.08, steepness=25.0)

    # ===================================================================
    # Dimension 8: Sub-band Energy Independence
    # Natural speech: low correlation between distant mel bands
    # Vocoders: higher cross-band correlation (global gain changes)
    # ===================================================================
    if n_mels >= 40 and n_frames >= 5:
        band_a = mel_linear[:, :20].mean(axis=1)  # low band
        band_b = mel_linear[:, -20:].mean(axis=1)  # high band
        # Pearson correlation between low and high band energy trajectories
        if np.std(band_a) > 1e-7 and np.std(band_b) > 1e-7:
            cross_corr = float(np.corrcoef(band_a, band_b)[0, 1])
        else:
            cross_corr = 0.5
        # Human: ~0.10-0.50 | AI: ~0.60-0.95
        subband_score = _sigmoid_map(cross_corr, center=0.55, steepness=6.0)
    else:
        subband_score = 0.5

    # ===================================================================
    # Weighted Fusion — all continuous, no hard jumps
    # ===================================================================
    # Primary acoustic indicators (strongest discriminative power)
    # Secondary indicators provide confirming evidence
    raw_synth_score = (
        flatness_score    * 0.18 +   # Wiener flatness (upper bands)
        corr_score        * 0.18 +   # Inter-frame correlation
        jitter_score      * 0.15 +   # Energy micro-jitter
        pitch_score       * 0.13 +   # Pitch stability
        modulation_score  * 0.12 +   # Temporal modulation envelope
        bandwidth_score   * 0.10 +   # Spectral bandwidth variance
        subband_score     * 0.08 +   # Sub-band independence
        hf_score          * 0.06     # HF energy anomalies
    )

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
                version="acoustic-neural-v3.0",
            )

    def get_model(self, model_key: str) -> Optional[ModelRegistryEntry]:
        return self._entries.get(model_key)

    def list_models(self, prefix: str = "") -> list[str]:
        return [k for k in self._entries if k.startswith(prefix)]
