"""
Voice Clone Detection Model Trainer
====================================
Trains a binary classifier (Human vs. Synthetic/Deepfake voice) using
acoustic features extracted from log-mel spectrograms.

Dataset: D:\Voice Data\voice-data\human-nonhuman
  - human/     : 1001 real human voice MP3s
  - nonhuman/  : 1000 synthetic/deepfake voice MP3s
  - possible/  : 87 ambiguous samples (used as extra test data)

Optional: WaveFake dataset samples for additional synthetic voice diversity.

Features extracted (48 total):
  - 8 sub-band energy statistics (mean, std) = 16
  - Spectral contrast (mean, std, max) = 3
  - Dynamic range (mean, std) = 2
  - Delta energy (mean, std) = 2
  - Delta-delta energy (mean, std) = 2
  - HF ratio (mean, std) = 2
  - Upper band variance = 1
  - Low-band pitch jitter = 1
  - Temporal autocorrelation (lag 1, 3, 5) = 3
  - Overall statistics (mean, std, skew, kurtosis) = 4
  - Band correlation (4 pairs) = 4
  - Modulation spectrum features = 3
  - Spectral flatness analogue = 1
  - Onset strength stats = 2
  - Frame energy envelope stats = 2

Output: app/trained_spoof_detector.joblib
  Contains: { 'model': GradientBoostingClassifier, 'scaler': StandardScaler, 'feature_names': list, 'version': str }
"""

import os
import sys
import time
import warnings
import numpy as np
import librosa
import joblib
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ============================================================
# Configuration
# ============================================================
DATASET_ROOT = r"D:\Voice Data\voice-data\human-nonhuman"
WAVEFAKE_ROOT = r"D:\Voice Data\wavefake"  # Optional - will be used if present
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "app", "trained_spoof_detector.joblib")

SAMPLE_RATE = 16000
DURATION = 4.0      # Load up to 4 seconds per clip
N_MELS = 80
N_FFT = 2048
HOP_LENGTH = 160    # 10ms hop at 16kHz
TEST_SPLIT = 0.20
RANDOM_SEED = 42

# ============================================================
# Feature Extraction
# ============================================================

def extract_features_from_audio(audio_path: str) -> np.ndarray | None:
    """
    Load an audio file and extract 48 acoustic features from its
    log-mel spectrogram. Returns None if the file cannot be processed.
    """
    try:
        y, sr = librosa.load(audio_path, sr=SAMPLE_RATE, duration=DURATION, mono=True)

        # Skip very short/silent clips
        if len(y) < SAMPLE_RATE * 0.3:  # less than 0.3s
            return None
        if np.max(np.abs(y)) < 0.005:  # near silence
            return None

        # Compute log-mel spectrogram (same as feature-extraction-service)
        mel_spec = librosa.feature.melspectrogram(
            y=y, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH,
            n_mels=N_MELS, fmax=8000
        )
        log_mel = np.log(np.maximum(mel_spec, 1e-9))  # (80, T)
        log_mel_T = log_mel.T  # (T, 80) — same layout as pipeline

        n_frames, n_mels = log_mel_T.shape
        if n_frames < 5:
            return None

        features = []

        # ---- 1. Sub-band Energy Statistics (16 features) ----
        # Divide 80 mel bins into 8 sub-bands of 10 each
        for i in range(8):
            band = log_mel_T[:, i*10:(i+1)*10]
            features.append(float(np.mean(band)))
            features.append(float(np.std(band)))

        # ---- 2. Spectral Contrast (3 features) ----
        contrast_per_frame = np.max(log_mel_T, axis=1) - np.min(log_mel_T, axis=1)
        features.append(float(np.mean(contrast_per_frame)))
        features.append(float(np.std(contrast_per_frame)))
        features.append(float(np.max(contrast_per_frame)))

        # ---- 3. Dynamic Range (2 features) ----
        dynamic_range = np.ptp(log_mel_T, axis=0)  # per-band peak-to-peak
        features.append(float(np.mean(dynamic_range)))
        features.append(float(np.std(dynamic_range)))

        # ---- 4. Delta Energy (2 features) ----
        delta = np.diff(log_mel_T, axis=0)
        delta_energy = np.mean(np.abs(delta), axis=1)
        features.append(float(np.mean(delta_energy)))
        features.append(float(np.std(delta_energy)))

        # ---- 5. Delta-Delta Energy (2 features) ----
        if n_frames > 3:
            delta2 = np.diff(delta, axis=0)
            delta2_energy = np.mean(np.abs(delta2), axis=1)
            features.append(float(np.mean(delta2_energy)))
            features.append(float(np.std(delta2_energy)))
        else:
            features.extend([0.0, 0.0])

        # ---- 6. HF Ratio (2 features) ----
        lower_mel = log_mel_T[:, :40]
        upper_mel = log_mel_T[:, 40:]
        hf_ratios = np.mean(upper_mel, axis=1) / (np.mean(lower_mel, axis=1) + 1e-7)
        features.append(float(np.mean(hf_ratios)))
        features.append(float(np.std(hf_ratios)))

        # ---- 7. Upper Band Temporal Variance (1 feature) ----
        upper_std_per_frame = np.std(log_mel_T[:, 40:], axis=1)
        features.append(float(np.mean(upper_std_per_frame)))

        # ---- 8. Low-Band Pitch Jitter (1 feature) ----
        if n_frames > 1:
            low_band_diff = np.diff(log_mel_T[:, :15], axis=0)
            features.append(float(np.std(low_band_diff)))
        else:
            features.append(0.0)

        # ---- 9. Temporal Autocorrelation (3 features) ----
        frame_energy = np.mean(log_mel_T, axis=1)
        frame_energy_centered = frame_energy - np.mean(frame_energy)
        norm = np.sum(frame_energy_centered ** 2)
        for lag in [1, 3, 5]:
            if n_frames > lag and norm > 1e-10:
                ac = np.sum(frame_energy_centered[lag:] * frame_energy_centered[:-lag]) / norm
                features.append(float(ac))
            else:
                features.append(0.0)

        # ---- 10. Overall Statistics (4 features) ----
        from scipy.stats import skew, kurtosis
        flat_mel = log_mel_T.flatten()
        features.append(float(np.mean(flat_mel)))
        features.append(float(np.std(flat_mel)))
        features.append(float(skew(flat_mel)))
        features.append(float(kurtosis(flat_mel)))

        # ---- 11. Band Correlation (4 features) ----
        # Correlation between adjacent sub-band pairs
        for i in range(0, 8, 2):
            band_a = np.mean(log_mel_T[:, i*10:(i+1)*10], axis=1)
            band_b = np.mean(log_mel_T[:, (i+1)*10:(i+2)*10], axis=1)
            if np.std(band_a) > 1e-7 and np.std(band_b) > 1e-7:
                corr = np.corrcoef(band_a, band_b)[0, 1]
                features.append(float(corr) if not np.isnan(corr) else 0.0)
            else:
                features.append(0.0)

        # ---- 12. Modulation Spectrum Features (3 features) ----
        # Modulation spectrum = FFT of the temporal energy envelope
        if n_frames >= 8:
            mod_spec = np.abs(np.fft.rfft(frame_energy_centered))
            # Low modulation (speech rhythm ~2-8 Hz)
            features.append(float(np.mean(mod_spec[:len(mod_spec)//3])))
            # Mid modulation
            features.append(float(np.mean(mod_spec[len(mod_spec)//3:2*len(mod_spec)//3])))
            # High modulation
            features.append(float(np.mean(mod_spec[2*len(mod_spec)//3:])))
        else:
            features.extend([0.0, 0.0, 0.0])

        # ---- 13. Spectral Flatness Analogue (1 feature) ----
        geo_mean = np.exp(np.mean(log_mel_T))
        arith_mean = np.mean(np.exp(log_mel_T))
        spectral_flatness = geo_mean / (arith_mean + 1e-10)
        features.append(float(spectral_flatness))

        # ---- 14. Onset Strength Stats (2 features) ----
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP_LENGTH)
        features.append(float(np.mean(onset_env)))
        features.append(float(np.std(onset_env)))

        # ---- 15. Frame Energy Envelope Stats (2 features) ----
        rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]
        features.append(float(np.mean(rms)))
        features.append(float(np.std(rms)))

        feature_vec = np.array(features, dtype=np.float64)

        # Sanity: replace any NaN/Inf
        feature_vec = np.nan_to_num(feature_vec, nan=0.0, posinf=1e6, neginf=-1e6)

        return feature_vec

    except Exception as e:
        return None


def _process_file(args):
    """Worker function for parallel feature extraction."""
    filepath, label = args
    feats = extract_features_from_audio(filepath)
    if feats is not None:
        return (feats, label, filepath)
    return None


# ============================================================
# Dataset Loading
# ============================================================

def load_dataset():
    """Load audio file paths and labels from the dataset directory."""
    human_dir = os.path.join(DATASET_ROOT, "human")
    nonhuman_dir = os.path.join(DATASET_ROOT, "nonhuman")
    possible_dir = os.path.join(DATASET_ROOT, "possible")

    samples = []

    # Human = label 0
    if os.path.isdir(human_dir):
        for f in os.listdir(human_dir):
            if f.lower().endswith(('.mp3', '.wav', '.flac', '.ogg')):
                samples.append((os.path.join(human_dir, f), 0))

    # NonHuman = label 1
    if os.path.isdir(nonhuman_dir):
        for f in os.listdir(nonhuman_dir):
            if f.lower().endswith(('.mp3', '.wav', '.flac', '.ogg')):
                samples.append((os.path.join(nonhuman_dir, f), 1))

    # WaveFake additional synthetic samples = label 1
    if os.path.isdir(WAVEFAKE_ROOT):
        wavefake_count = 0
        for root, dirs, files in os.walk(WAVEFAKE_ROOT):
            for f in files:
                if f.lower().endswith(('.wav', '.mp3', '.flac')):
                    samples.append((os.path.join(root, f), 1))
                    wavefake_count += 1
        if wavefake_count > 0:
            print(f"  ✓ Added {wavefake_count} WaveFake synthetic samples")

    # Possible (ambiguous) — we'll add them as a separate test set later
    possible_samples = []
    if os.path.isdir(possible_dir):
        for f in os.listdir(possible_dir):
            if f.lower().endswith(('.mp3', '.wav', '.flac', '.ogg')):
                possible_samples.append(os.path.join(possible_dir, f))

    return samples, possible_samples


# ============================================================
# Main Training Pipeline
# ============================================================

def main():
    print("=" * 70)
    print("  PRIME VECTOR — Voice Clone Detection Model Trainer")
    print("  Training on: Human vs. Synthetic/Deepfake Voice")
    print("=" * 70)
    print()

    t0 = time.time()

    # 1. Load dataset
    print("[1/5] Loading dataset...")
    samples, possible_files = load_dataset()
    n_human = sum(1 for _, l in samples if l == 0)
    n_synth = sum(1 for _, l in samples if l == 1)
    print(f"  ✓ Human samples:    {n_human}")
    print(f"  ✓ Synthetic samples: {n_synth}")
    print(f"  ✓ Possible/ambiguous: {len(possible_files)}")
    print()

    # 2. Extract features (parallel)
    print("[2/5] Extracting acoustic features (this may take a few minutes)...")
    X_list = []
    y_list = []
    failed = 0

    # Use multiprocessing for speed
    n_workers = min(os.cpu_count() or 4, 8)
    print(f"  Using {n_workers} parallel workers...")

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {executor.submit(_process_file, s): s for s in samples}
        done_count = 0
        for future in as_completed(futures):
            done_count += 1
            result = future.result()
            if result is not None:
                feats, label, _ = result
                X_list.append(feats)
                y_list.append(label)
            else:
                failed += 1

            if done_count % 200 == 0 or done_count == len(samples):
                pct = 100.0 * done_count / len(samples)
                print(f"  Progress: {done_count}/{len(samples)} ({pct:.1f}%) — "
                      f"extracted: {len(X_list)}, failed: {failed}")

    X = np.array(X_list)
    y = np.array(y_list)
    print(f"\n  ✓ Feature extraction complete: {X.shape[0]} samples × {X.shape[1]} features")
    print(f"  ✗ Failed/skipped: {failed}")
    print()

    # 3. Train/Test Split
    print("[3/5] Splitting dataset...")
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SPLIT, random_state=RANDOM_SEED, stratify=y
    )
    print(f"  ✓ Training set: {X_train.shape[0]} samples")
    print(f"  ✓ Test set:     {X_test.shape[0]} samples")

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print()

    # 4. Train Classifier Ensemble
    print("[4/5] Training classifier ensemble...")
    from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, VotingClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        confusion_matrix, classification_report, roc_auc_score
    )

    # Random Forest — robust and highly discriminative
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )

    # Extra Trees — randomized tree splits for variance reduction
    et = ExtraTreesClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )

    # MLP Neural Net — non-linear decision surface
    mlp = MLPClassifier(
        hidden_layer_sizes=(64, 32),
        max_iter=300,
        random_state=RANDOM_SEED,
        early_stopping=True,
    )

    # Soft voting ensemble
    ensemble = VotingClassifier(
        estimators=[('rf', rf), ('et', et), ('mlp', mlp)],
        voting='soft',
    )

    t_train_start = time.time()
    ensemble.fit(X_train_scaled, y_train)
    t_train_end = time.time()
    print(f"  ✓ Training completed in {t_train_end - t_train_start:.1f}s")

    # Evaluate
    y_pred = ensemble.predict(X_test_scaled)
    y_proba = ensemble.predict_proba(X_test_scaled)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred)

    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║     MODEL EVALUATION RESULTS         ║")
    print("  ╠══════════════════════════════════════╣")
    print(f"  ║  Accuracy:   {acc*100:6.2f}%                ║")
    print(f"  ║  Precision:  {prec*100:6.2f}%                ║")
    print(f"  ║  Recall:     {rec*100:6.2f}%                ║")
    print(f"  ║  F1 Score:   {f1*100:6.2f}%                ║")
    print(f"  ║  AUC-ROC:    {auc:6.4f}                 ║")
    print("  ╚══════════════════════════════════════╝")
    print()
    print("  Confusion Matrix:")
    print(f"    {'':>12} Predicted")
    print(f"    {'':>12} Human  Synth")
    print(f"    Actual Human  [{cm[0][0]:4d}   {cm[0][1]:4d}]")
    print(f"    Actual Synth  [{cm[1][0]:4d}   {cm[1][1]:4d}]")
    print()
    print("  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Human", "Synthetic"]))

    # Feature importance
    print("  Top 10 Most Important Features:")
    # Use RF's feature importances
    rf_model = ensemble.named_estimators_['rf']
    feature_names = _get_feature_names()
    importances = rf_model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    for rank, idx in enumerate(sorted_idx[:10], 1):
        name = feature_names[idx] if idx < len(feature_names) else f"feature_{idx}"
        print(f"    {rank:2d}. {name:30s} — importance: {importances[idx]:.4f}")
    print()

    # 5. Save model
    print("[5/5] Saving trained model...")
    model_package = {
        'model': ensemble,
        'scaler': scaler,
        'feature_names': feature_names,
        'version': 'ml-ensemble-v1.0',
        'n_features': X.shape[1],
        'metrics': {
            'accuracy': float(acc),
            'precision': float(prec),
            'recall': float(rec),
            'f1': float(f1),
            'auc_roc': float(auc),
        },
        'training_samples': int(X_train.shape[0]),
        'test_samples': int(X_test.shape[0]),
    }
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    joblib.dump(model_package, OUTPUT_PATH, compress=3)
    file_size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    print(f"  ✓ Model saved to: {OUTPUT_PATH}")
    print(f"  ✓ File size: {file_size_mb:.1f} MB")

    # Evaluate on "possible" samples if available
    if possible_files:
        print()
        print("[BONUS] Evaluating on 'possible/ambiguous' samples...")
        possible_results = []
        for pf in possible_files:
            feats = extract_features_from_audio(pf)
            if feats is not None:
                feats_scaled = scaler.transform(feats.reshape(1, -1))
                proba = ensemble.predict_proba(feats_scaled)[0, 1]
                pred = "SYNTHETIC" if proba > 0.5 else "HUMAN"
                possible_results.append((os.path.basename(pf), proba, pred))

        if possible_results:
            n_pred_human = sum(1 for _, _, p in possible_results if p == "HUMAN")
            n_pred_synth = sum(1 for _, _, p in possible_results if p == "SYNTHETIC")
            print(f"  Predicted Human: {n_pred_human}, Predicted Synthetic: {n_pred_synth}")
            avg_score = np.mean([r[1] for r in possible_results])
            print(f"  Average synthesis probability: {avg_score:.4f}")

    total_time = time.time() - t0
    print()
    print("=" * 70)
    print(f"  ✓ TRAINING COMPLETE — Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"  ✓ Model ready for deployment at: {OUTPUT_PATH}")
    print("=" * 70)


def _get_feature_names():
    """Return human-readable feature names (must match extract_features_from_audio order)."""
    names = []
    # Sub-band stats
    for i in range(8):
        names.append(f"subband_{i}_mean")
        names.append(f"subband_{i}_std")
    # Spectral contrast
    names.extend(["spectral_contrast_mean", "spectral_contrast_std", "spectral_contrast_max"])
    # Dynamic range
    names.extend(["dynamic_range_mean", "dynamic_range_std"])
    # Delta energy
    names.extend(["delta_energy_mean", "delta_energy_std"])
    # Delta-delta energy
    names.extend(["delta2_energy_mean", "delta2_energy_std"])
    # HF ratio
    names.extend(["hf_ratio_mean", "hf_ratio_std"])
    # Upper band variance
    names.append("upper_band_variance")
    # Pitch jitter
    names.append("pitch_jitter")
    # Autocorrelation
    names.extend(["autocorr_lag1", "autocorr_lag3", "autocorr_lag5"])
    # Overall stats
    names.extend(["overall_mean", "overall_std", "overall_skew", "overall_kurtosis"])
    # Band correlations
    for i in range(4):
        names.append(f"band_corr_{i*2}_{i*2+1}")
    # Modulation spectrum
    names.extend(["mod_spec_low", "mod_spec_mid", "mod_spec_high"])
    # Spectral flatness
    names.append("spectral_flatness")
    # Onset strength
    names.extend(["onset_mean", "onset_std"])
    # RMS energy
    names.extend(["rms_mean", "rms_std"])
    return names


if __name__ == "__main__":
    main()
