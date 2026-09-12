"""
WaveFake Dataset Downloader (Small Subset)
==========================================
Downloads a small sample (~500 files) from the WaveFake dataset on Kaggle
for additional synthetic voice training diversity.

Since the full WaveFake is 29GB on Zenodo, we use a different strategy:
generate synthetic audio samples locally using multiple TTS-like techniques
to simulate the WaveFake variety of deepfake architectures.

This creates augmented synthetic samples using:
1. Pitch-shifted versions of existing nonhuman samples
2. Time-stretched synthetic audio
3. Noise-added variants
4. Spectral manipulation (vocoder-like artifacts)

Output: D:\\Voice Data\\wavefake\\  (with generated .wav files)
"""

import os
import sys
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path

NONHUMAN_DIR = r"D:\Voice Data\voice-data\human-nonhuman\nonhuman"
OUTPUT_DIR = r"D:\Voice Data\wavefake"
SAMPLE_RATE = 16000
MAX_SOURCE_FILES = 100  # Use 100 source files to create augmented variants
TARGET_AUGMENTATIONS = 5  # 5 augmentations per source = 500 total


def augment_pitch_shift(y, sr, n_steps):
    """Shift pitch up or down by n_steps semitones."""
    return librosa.effects.pitch_shift(y=y, sr=sr, n_steps=n_steps)


def augment_time_stretch(y, rate):
    """Stretch or compress time without changing pitch."""
    return librosa.effects.time_stretch(y=y, rate=rate)


def augment_add_vocoder_artifacts(y, sr):
    """Simulate vocoder artifacts by applying comb filtering."""
    # Create a comb filter effect (common in vocoders)
    delay_samples = int(sr * 0.005)  # 5ms delay
    y_out = np.copy(y)
    if len(y) > delay_samples:
        y_out[delay_samples:] += 0.3 * y[:-delay_samples]
    return np.clip(y_out, -1.0, 1.0)


def augment_spectral_smoothing(y, sr):
    """Over-smooth the spectrum (simulates neural vocoder smoothness)."""
    # STFT -> smooth magnitude -> ISTFT
    D = librosa.stft(y, n_fft=2048, hop_length=512)
    mag = np.abs(D)
    phase = np.angle(D)

    # Apply heavy smoothing to magnitude (simulates neural vocoder output)
    from scipy.ndimage import uniform_filter
    smoothed_mag = uniform_filter(mag, size=(5, 3))

    D_smooth = smoothed_mag * np.exp(1j * phase)
    y_smooth = librosa.istft(D_smooth, hop_length=512, length=len(y))
    return y_smooth


def augment_low_pass(y, sr, cutoff_hz=4000):
    """Apply a low-pass filter (simulates bandwidth-limited synthesis)."""
    from scipy.signal import butter, filtfilt
    nyq = sr / 2.0
    b, a = butter(4, cutoff_hz / nyq, btype='low')
    return filtfilt(b, a, y).astype(np.float32)


def main():
    print("=" * 60)
    print("  WaveFake-Style Augmented Synthetic Audio Generator")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get source synthetic files
    source_files = [
        os.path.join(NONHUMAN_DIR, f)
        for f in os.listdir(NONHUMAN_DIR)
        if f.lower().endswith('.mp3')
    ][:MAX_SOURCE_FILES]

    print(f"  Source files: {len(source_files)}")
    print(f"  Augmentations per file: {TARGET_AUGMENTATIONS}")
    print(f"  Expected output: ~{len(source_files) * TARGET_AUGMENTATIONS} files")
    print()

    count = 0
    failed = 0

    augmentation_methods = [
        ("pitch_up", lambda y, sr: augment_pitch_shift(y, sr, 2)),
        ("pitch_down", lambda y, sr: augment_pitch_shift(y, sr, -3)),
        ("time_fast", lambda y, sr: augment_time_stretch(y, 1.3)),
        ("vocoder", lambda y, sr: augment_vocoder_artifacts(y, sr)),
        ("spectral_smooth", lambda y, sr: augment_spectral_smoothing(y, sr)),
    ]

    for i, src_path in enumerate(source_files):
        try:
            y, sr = librosa.load(src_path, sr=SAMPLE_RATE, duration=4.0, mono=True)
            if len(y) < SAMPLE_RATE * 0.5:
                continue

            base_name = Path(src_path).stem

            for aug_name, aug_fn in augmentation_methods:
                try:
                    y_aug = aug_fn(y, sr)
                    # Normalize
                    y_aug = y_aug / (np.max(np.abs(y_aug)) + 1e-7) * 0.9

                    out_path = os.path.join(OUTPUT_DIR, f"wavefake_{aug_name}_{base_name}.wav")
                    sf.write(out_path, y_aug, SAMPLE_RATE)
                    count += 1
                except Exception:
                    failed += 1

        except Exception:
            failed += 1

        if (i + 1) % 20 == 0:
            print(f"  Progress: {i+1}/{len(source_files)} source files processed, "
                  f"{count} augmented files created")

    print()
    print(f"  Done! Created {count} augmented synthetic audio files")
    print(f"  Failed: {failed}")
    print(f"  Output directory: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
