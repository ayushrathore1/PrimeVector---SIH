#!/usr/bin/env python3
"""
SatyaDhVani v2 — Voice Deepfake Detection Demo
=============================================

Test the trained SatyaDhVani v2 model with any WAV/MP3 audio file.
Scores audio as bonafide (real human) vs spoof (AI-generated).

Usage:
    python demo_dhwani.py path/to/audio.wav
    python demo_dhwani.py path/to/audio.mp3
    python demo_dhwani.py --record 5          # Record 5s from mic

Requirements:
    pip install torch librosa soundfile numpy
"""

import sys
import os
import argparse
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Add the service model directory to path so we can reuse the exact architecture
sys.path.insert(0, os.path.join(PROJECT_ROOT, "services", "spoof-detection-service", "app"))


def load_model(checkpoint_path=None):
    """Load the SatyaDhVani v2 model using the official loader."""
    from model.satyadhvani_baseline import load_satyadhvani_baseline

    if checkpoint_path is None:
        candidates = [
            os.path.join(PROJECT_ROOT, "services", "spoof-detection-service", "app", "satyadhvani_baseline_v2.pt"),
            os.path.join(PROJECT_ROOT, "services", "spoof-detection-service", "app", "dhwani_baseline_v2.pt"),
            os.path.join(PROJECT_ROOT, "ml", "dhwani", "checkpoints", "satyadhvani_baseline_v2.pt"),
            os.path.join(PROJECT_ROOT, "ml", "dhwani", "checkpoints", "dhwani_baseline_v2.pt"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                checkpoint_path = c
                break

    if not checkpoint_path or not os.path.isfile(checkpoint_path):
        print(f"ERROR: Model not found at {checkpoint_path}")
        print("Download it from Colab or run the training notebook first.")
        sys.exit(1)

    print(f"Loading model: {checkpoint_path}")
    model, version, metrics, param_count, mem_mb = load_satyadhvani_baseline(
        checkpoint_path, device="cpu"
    )

    print(f"  Version:      {version}")
    print(f"  Parameters:   {param_count:,}")
    print(f"  Memory:       {mem_mb:.1f} MB")
    if metrics:
        print(f"  Accuracy:     {metrics.get('accuracy', 0):.1%}")
        print(f"  F1:           {metrics.get('f1', 0):.1%}")

    import torch
    ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    config = ckpt.get("config", {})

    return model, config


def extract_features(audio_path, config):
    """Extract 3-channel features (Log-Mel + Delta + Delta²) from audio."""
    import librosa

    sr = config.get("sample_rate", 16000)
    n_mels = config.get("n_mels", 80)
    n_fft = config.get("n_fft", 2048)
    hop_length = config.get("hop_length", 160)
    win_length = config.get("win_length", 400)
    max_duration = config.get("max_duration_s", 4.0)
    n_channels = config.get("n_channels", 3)

    # Load audio
    y, _ = librosa.load(audio_path, sr=sr, mono=True)
    duration = len(y) / sr
    print(f"  Duration:     {duration:.2f}s")
    print(f"  Sample rate:  {sr} Hz")

    # Truncate/pad to max_duration
    max_samples = int(max_duration * sr)
    if len(y) > max_samples:
        y = y[:max_samples]
    elif len(y) < max_samples:
        y = np.pad(y, (0, max_samples - len(y)))

    # Log-mel spectrogram
    mel = librosa.feature.melspectrogram(
        y=y, sr=sr, n_fft=n_fft, hop_length=hop_length,
        win_length=win_length, n_mels=n_mels,
    )
    log_mel = librosa.power_to_db(mel, ref=np.max)

    if n_channels == 3:
        delta = librosa.feature.delta(log_mel)
        delta2 = librosa.feature.delta(log_mel, order=2)
        features = np.stack([log_mel, delta, delta2], axis=0)
    else:
        features = log_mel[np.newaxis, ...]

    # Per-utterance per-channel normalization
    for ch in range(features.shape[0]):
        mean = features[ch].mean()
        std = features[ch].std() + 1e-8
        features[ch] = (features[ch] - mean) / std

    return features


def predict(model, features):
    """Run inference and return score + confidence."""
    import torch

    with torch.no_grad():
        x = torch.FloatTensor(features).unsqueeze(0)
        logit = model(x).squeeze().item()
        score = 1.0 / (1.0 + np.exp(-logit))
        confidence = abs(score - 0.5) * 2.0

    return score, confidence, logit


def record_audio(duration_s, sr=16000):
    """Record audio from microphone."""
    try:
        import sounddevice as sd
    except ImportError:
        print("Install sounddevice: pip install sounddevice")
        sys.exit(1)

    print(f"\n🎙 Recording {duration_s}s of audio... Speak now!")
    audio = sd.rec(int(duration_s * sr), samplerate=sr, channels=1, dtype="float32")
    sd.wait()
    print("Recording complete.")

    import soundfile as sf
    temp_path = os.path.join(PROJECT_ROOT, "_temp_recording.wav")
    sf.write(temp_path, audio.flatten(), sr)
    return temp_path


def main():
    parser = argparse.ArgumentParser(
        description="Dhwani v2 — Voice Deepfake Detection Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo_dhwani.py real_voice.wav
  python demo_dhwani.py ai_generated.mp3
  python demo_dhwani.py --record 5
  python demo_dhwani.py ml/dhwani/notebooks/spoof_generated/sarvam/hi/a328f9e98c5f.wav
        """,
    )
    parser.add_argument("audio_file", nargs="?", help="Path to audio file (WAV/MP3)")
    parser.add_argument("--record", type=int, metavar="SECONDS",
                        help="Record from microphone for N seconds")
    parser.add_argument("--checkpoint", type=str, default=None,
                        help="Path to model checkpoint (.pt)")
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="Spoof detection threshold (default: 0.5)")
    args = parser.parse_args()

    if not args.audio_file and not args.record:
        parser.print_help()
        sys.exit(1)

    print("=" * 60)
    print("  SatyaDhVani v2 — Voice Deepfake Detection")
    print("=" * 60)

    model, config = load_model(args.checkpoint)

    if args.record:
        audio_path = record_audio(args.record)
        cleanup = True
    else:
        audio_path = args.audio_file
        cleanup = False

    if not os.path.isfile(audio_path):
        print(f"ERROR: File not found: {audio_path}")
        sys.exit(1)

    print(f"\nAnalyzing: {os.path.basename(audio_path)}")

    features = extract_features(audio_path, config)
    print(f"  Features:     {features.shape} (ch, mels, frames)")

    score, confidence, logit = predict(model, features)

    is_spoof = score > args.threshold
    label = "🚨 SPOOF (AI-Generated)" if is_spoof else "✅ BONAFIDE (Real Human)"

    print("\n" + "=" * 60)
    print(f"  RESULT: {label}")
    print("=" * 60)
    print(f"  Spoof Score:  {score:.4f}  (0=real, 1=fake)")
    print(f"  Confidence:   {confidence:.4f}")
    print(f"  Raw Logit:    {logit:.4f}")
    print(f"  Threshold:    {args.threshold}")
    print("=" * 60)

    if is_spoof:
        print("\n  ⚠️  The audio is likely AI-generated or synthesized.")
    else:
        print("\n  The audio appears to be genuine human speech.")

    if cleanup and os.path.isfile(audio_path):
        os.remove(audio_path)

    return 0 if not is_spoof else 1


if __name__ == "__main__":
    sys.exit(main())
