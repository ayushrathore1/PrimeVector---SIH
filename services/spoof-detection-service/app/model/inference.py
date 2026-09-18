"""
Dhwani inference engine — chunk-level real-time inference.

Handles the full pipeline from raw PCM audio to synthetic probability,
matching the existing spoof-detection-service's dual-path detection:

  audio_pcm_base64
    → decode to float32
    → segment into chunks (3s window, 1s hop)
    → compute 80-band Log-Mel per chunk
    → Dhwani model forward pass per chunk
    → rolling prediction smoothing (EMA)
    → final synthetic_probability

Audio non-retention (DESIGN.md section 7):
  All audio data is processed in RAM and immediately dereferenced
  after inference. No audio is written to disk, logged, or persisted.

Latency measurement:
  The engine measures feature extraction and model inference latency
  per chunk. Do NOT claim real-time performance without these measurements.
"""
from __future__ import annotations

import base64
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Audio parameters matching PrimeVector feature-extraction-service
SAMPLE_RATE = 16000
N_MELS = 80
N_FFT = 2048
HOP_LENGTH = 160    # 10ms hop at 16kHz
WIN_LENGTH = 400    # 25ms window at 16kHz
FMAX = 8000


@dataclass
class ChunkResult:
    """Result from a single chunk inference."""
    logit: float
    score: float           # sigmoid(logit)
    chunk_start_s: float
    chunk_end_s: float
    feature_latency_ms: float
    inference_latency_ms: float


@dataclass
class InferenceResult:
    """Aggregated result from chunk-level inference."""
    logit: float                        # smoothed logit
    score: float                        # smoothed score (sigmoid)
    chunk_results: list[ChunkResult] = field(default_factory=list)
    total_chunks: int = 0
    total_feature_latency_ms: float = 0.0
    total_inference_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    audio_duration_s: float = 0.0


def _compute_log_mel(audio: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Compute 80-band Log-Mel spectrogram matching PrimeVector params.

    Returns: (n_mels, time_frames) numpy array
    """
    import librosa

    mel = librosa.feature.melspectrogram(
        y=audio, sr=sr,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        win_length=WIN_LENGTH,
        n_mels=N_MELS,
        fmax=FMAX,
    )
    log_mel = librosa.power_to_db(mel, ref=np.max)
    return log_mel


def _compute_3channel_features(audio: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Compute 3-channel features for DhwaniV2: Log-Mel + Delta + Delta².

    Delta features capture temporal dynamics — AI-generated speech often
    has unnaturally smooth transitions (low delta) or abrupt artifacts
    (delta-delta spikes) that distinguish it from natural speech.

    Returns: (3, n_mels, time_frames) numpy array
    """
    import librosa

    mel = librosa.feature.melspectrogram(
        y=audio, sr=sr,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        win_length=WIN_LENGTH,
        n_mels=N_MELS,
        fmax=FMAX,
    )
    log_mel = librosa.power_to_db(mel, ref=np.max)
    delta = librosa.feature.delta(log_mel, order=1)
    delta2 = librosa.feature.delta(log_mel, order=2)
    return np.stack([log_mel, delta, delta2], axis=0)


def _normalize_features(feat: np.ndarray) -> np.ndarray:
    """
    Per-utterance, per-channel mean/std normalization.
    Matches the normalization used during v2 training.
    """
    feat = np.asarray(feat, dtype=np.float32)
    if feat.ndim == 2:
        return (feat - feat.mean()) / (feat.std() + 1e-6)
    elif feat.ndim == 3:
        result = np.empty_like(feat)
        for c in range(feat.shape[0]):
            ch = feat[c]
            result[c] = (ch - ch.mean()) / (ch.std() + 1e-6)
        return result
    return feat


def _is_v2_model(model) -> bool:
    """Detect if the model is a DhwaniV2 (3-channel) or DhwaniBaseline (1-channel)."""
    from model.dhwani_baseline import DhwaniV2
    return isinstance(model, DhwaniV2)


def predict_chunks(
    model,
    audio_pcm_base64: str,
    window_seconds: float = 3.0,
    hop_seconds: float = 1.0,
    minimum_audio_seconds: float = 2.0,
    smoothing_alpha: float = 0.7,
    sample_rate: int = SAMPLE_RATE,
) -> dict:
    """
    Full chunk-level inference pipeline.

    Processes audio in overlapping chunks, applies EMA smoothing,
    and returns the final prediction. All audio data is dereferenced
    after inference (DESIGN.md section 7).

    Args:
        model: Loaded Dhwani nn.Module (DhwaniBaseline or DhwaniAdvanced)
        audio_pcm_base64: Base64-encoded 16-bit PCM audio
        window_seconds: Analysis window length in seconds
        hop_seconds: Hop between successive windows
        minimum_audio_seconds: Minimum audio for valid prediction
        smoothing_alpha: EMA smoothing factor (higher = more weight on recent)
        sample_rate: Expected sample rate

    Returns:
        {"logit": float, "score": float, "latency_ms": float, "chunks": int}
    """
    import torch

    t_start = time.perf_counter()

    # Step 1: Decode base64 → float32 (in-memory only)
    pcm_bytes = base64.b64decode(audio_pcm_base64)
    audio_int16 = np.frombuffer(pcm_bytes, dtype=np.int16)
    audio_float32 = audio_int16.astype(np.float32) / 32768.0

    audio_duration_s = len(audio_float32) / sample_rate

    # Check minimum audio length
    if audio_duration_s < minimum_audio_seconds:
        logger.warning(
            "Audio too short for reliable prediction: %.2fs < %.2fs minimum",
            audio_duration_s, minimum_audio_seconds,
        )
        # Still process, but flag low confidence

    # Step 2: Segment into chunks
    window_samples = int(window_seconds * sample_rate)
    hop_samples = int(hop_seconds * sample_rate)

    # If audio is shorter than one window, pad it
    if len(audio_float32) < window_samples:
        audio_float32 = np.pad(
            audio_float32, (0, window_samples - len(audio_float32))
        )

    chunks = []
    start = 0
    while start + window_samples <= len(audio_float32):
        chunk = audio_float32[start:start + window_samples]
        chunk_start_s = start / sample_rate
        chunk_end_s = (start + window_samples) / sample_rate
        chunks.append((chunk, chunk_start_s, chunk_end_s))
        start += hop_samples

    # If no complete chunks were created, use the full audio
    if not chunks:
        chunks = [(audio_float32, 0.0, audio_duration_s)]

    # Step 3: Process each chunk
    chunk_results = []
    smoothed_score = None

    # Auto-detect model version for feature extraction
    use_3ch = _is_v2_model(model)

    for chunk_audio, chunk_start, chunk_end in chunks:
        # Feature extraction timing
        t_feat = time.perf_counter()
        if use_3ch:
            # v2: 3-channel (Log-Mel + Delta + Delta²)
            features = _compute_3channel_features(chunk_audio, sample_rate)
            features = _normalize_features(features)
            mel_tensor = torch.FloatTensor(features).unsqueeze(0)  # (1, 3, 80, T)
        else:
            # v1: 1-channel Log-Mel
            log_mel = _compute_log_mel(chunk_audio, sample_rate)
            mel_tensor = torch.FloatTensor(log_mel).unsqueeze(0).unsqueeze(0)  # (1, 1, 80, T)
        feat_latency = (time.perf_counter() - t_feat) * 1000

        # Model inference timing
        t_infer = time.perf_counter()
        with torch.no_grad():
            logit = model(mel_tensor)
        logit_val = logit.squeeze().item()
        score_val = torch.sigmoid(logit.squeeze()).item()
        infer_latency = (time.perf_counter() - t_infer) * 1000

        # EMA smoothing
        if smoothed_score is None:
            smoothed_score = score_val
        else:
            smoothed_score = (
                smoothing_alpha * score_val
                + (1 - smoothing_alpha) * smoothed_score
            )

        chunk_results.append(ChunkResult(
            logit=logit_val,
            score=score_val,
            chunk_start_s=chunk_start,
            chunk_end_s=chunk_end,
            feature_latency_ms=feat_latency,
            inference_latency_ms=infer_latency,
        ))

    total_latency = (time.perf_counter() - t_start) * 1000

    # Compute smoothed logit from smoothed score
    eps = 1e-7
    smoothed_score_clamped = max(eps, min(1.0 - eps, smoothed_score))
    smoothed_logit = float(np.log(smoothed_score_clamped / (1.0 - smoothed_score_clamped)))

    # Log performance metrics
    avg_feat_ms = sum(c.feature_latency_ms for c in chunk_results) / len(chunk_results)
    avg_infer_ms = sum(c.inference_latency_ms for c in chunk_results) / len(chunk_results)
    logger.info(
        "Dhwani inference: chunks=%d, avg_feat=%.1fms, avg_infer=%.1fms, "
        "total=%.1fms, smoothed_score=%.4f",
        len(chunk_results), avg_feat_ms, avg_infer_ms,
        total_latency, smoothed_score,
    )

    # Audio data dereferenced here — pcm_bytes, audio_int16, audio_float32,
    # chunk_audio, log_mel, mel_tensor all go out of scope.

    return {
        "logit": smoothed_logit,
        "score": float(smoothed_score),
        "latency_ms": total_latency,
        "chunks": len(chunk_results),
        "audio_duration_s": audio_duration_s,
    }
