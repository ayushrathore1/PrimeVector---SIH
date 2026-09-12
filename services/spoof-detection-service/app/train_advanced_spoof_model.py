"""
Train High-Precision Voice Clone vs Real Human Voice Classifier.

Downloads clean real human vs ElevenLabs synthetic voice dataset (<1 GB, ~250MB)
from Hugging Face (garystafford/deepfake-audio-detection), extracts 48 acoustic
features, and trains an Ensemble Classifier (ExtraTrees + RandomForest + GradientBoosting + MLP).

Saves model package to trained_spoof_detector.joblib.
"""
import io
import os
import sys
import json
import time
import urllib.request
import numpy as np
import scipy.stats
import librosa
import joblib

from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(APP_DIR, "dataset_cache")
MODEL_OUT_PATH = os.path.join(APP_DIR, "trained_spoof_detector.joblib")
HF_DATASET_API = "https://huggingface.co/api/datasets/garystafford/deepfake-audio-detection"
HF_BASE_URL = "https://huggingface.co/datasets/garystafford/deepfake-audio-detection/resolve/main/"


def extract_48_features_from_audio(y: np.ndarray, sr: int = 16000) -> np.ndarray:
    """
    Extract 48 statistical acoustic features from a 16kHz audio array.
    Identical to model_registry._extract_48_features_from_logmel.
    """
    if len(y) < 1600:
        y = np.pad(y, (0, 1600 - len(y)))
    
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=1024, hop_length=256, n_mels=80)
    log_mel = np.log(mel.T + 1e-6) # (frames, 80)
    
    from scipy.stats import skew, kurtosis
    n_frames, n_mels = log_mel.shape
    features = []

    # 1. Sub-band Energy Statistics (16)
    for i in range(8):
        band = log_mel[:, i*10:(i+1)*10]
        features.append(float(np.mean(band)))
        features.append(float(np.std(band)))

    # 2. Spectral Contrast (3)
    contrast_per_frame = np.max(log_mel, axis=1) - np.min(log_mel, axis=1)
    features.append(float(np.mean(contrast_per_frame)))
    features.append(float(np.std(contrast_per_frame)))
    features.append(float(np.max(contrast_per_frame)))

    # 3. Dynamic Range (2)
    dynamic_range = np.ptp(log_mel, axis=0)
    features.append(float(np.mean(dynamic_range)))
    features.append(float(np.std(dynamic_range)))

    # 4. Delta Energy (2)
    delta = np.diff(log_mel, axis=0)
    delta_energy = np.mean(np.abs(delta), axis=1)
    features.append(float(np.mean(delta_energy)))
    features.append(float(np.std(delta_energy)))

    # 5. Delta-Delta Energy (2)
    if n_frames > 3:
        delta2 = np.diff(delta, axis=0)
        delta2_energy = np.mean(np.abs(delta2), axis=1)
        features.append(float(np.mean(delta2_energy)))
        features.append(float(np.std(delta2_energy)))
    else:
        features.extend([0.0, 0.0])

    # 6. HF Ratio (2)
    lower_mel = log_mel[:, :40]
    upper_mel = log_mel[:, 40:]
    hf_ratios = np.mean(upper_mel, axis=1) / (np.mean(lower_mel, axis=1) + 1e-7)
    features.append(float(np.mean(hf_ratios)))
    features.append(float(np.std(hf_ratios)))

    # 7. Upper Band Variance (1)
    upper_std_per_frame = np.std(log_mel[:, 40:], axis=1)
    features.append(float(np.mean(upper_std_per_frame)))

    # 8. Low-Band Pitch Jitter (1)
    if n_frames > 1:
        low_band_diff = np.diff(log_mel[:, :15], axis=0)
        features.append(float(np.std(low_band_diff)))
    else:
        features.append(0.0)

    # 9. Temporal Autocorrelation (3)
    frame_energy = np.mean(log_mel, axis=1)
    frame_energy_centered = frame_energy - np.mean(frame_energy)
    norm = np.sum(frame_energy_centered ** 2)
    for lag in [1, 3, 5]:
        if n_frames > lag and norm > 1e-10:
            ac = np.sum(frame_energy_centered[lag:] * frame_energy_centered[:-lag]) / norm
            features.append(float(ac))
        else:
            features.append(0.0)

    # 10. Overall Statistics (4)
    flat_mel = log_mel.flatten()
    features.append(float(np.mean(flat_mel)))
    features.append(float(np.std(flat_mel)))
    features.append(float(skew(flat_mel)))
    features.append(float(kurtosis(flat_mel)))

    # 11. Band Correlation (4)
    for i in range(0, 8, 2):
        band_a = np.mean(log_mel[:, i*10:(i+1)*10], axis=1)
        band_b = np.mean(log_mel[:, (i+1)*10:(i+2)*10], axis=1)
        if np.std(band_a) > 1e-7 and np.std(band_b) > 1e-7:
            corr = np.corrcoef(band_a, band_b)[0, 1]
            features.append(float(corr) if not np.isnan(corr) else 0.0)
        else:
            features.append(0.0)

    # 12. Modulation Spectrum (3)
    if n_frames >= 8:
        mod_spec = np.abs(np.fft.rfft(frame_energy_centered))
        third = len(mod_spec) // 3
        features.append(float(np.mean(mod_spec[:third])))
        features.append(float(np.mean(mod_spec[third:2*third])))
        features.append(float(np.mean(mod_spec[2*third:])))
    else:
        features.extend([0.0, 0.0, 0.0])

    # 13. Spectral Flatness (1)
    geo_mean = np.exp(np.mean(log_mel))
    arith_mean = np.mean(np.exp(log_mel))
    features.append(float(geo_mean / (arith_mean + 1e-10)))

    # 14. Onset Strength (2)
    onset_approx = np.maximum(0, np.diff(np.mean(log_mel, axis=1)))
    features.append(float(np.mean(onset_approx)) if len(onset_approx) > 0 else 0.0)
    features.append(float(np.std(onset_approx)) if len(onset_approx) > 0 else 0.0)

    # 15. RMS Energy (2)
    mel_power = np.exp(log_mel)
    rms_per_frame = np.sqrt(np.mean(mel_power, axis=1))
    features.append(float(np.mean(rms_per_frame)))
    features.append(float(np.std(rms_per_frame)))

    arr_feat = np.array(features, dtype=np.float64)
    return np.nan_to_num(arr_feat, nan=0.0, posinf=1e6, neginf=-1e6)


def fetch_dataset_file_list():
    """Fetch file list from HuggingFace dataset repository."""
    print("[+] Querying Hugging Face for clean audio deepfake dataset...")
    req = urllib.request.Request(HF_DATASET_API, headers={"User-Agent": "Mozilla/5.0"})
    res = json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
    files = [f["rfilename"] for f in res.get("siblings", [])]
    
    real_files = [f for f in files if f.startswith("real/") and f.endswith(".flac")]
    fake_files = [f for f in files if f.startswith("fake/") and f.endswith(".flac")]
    
    print(f"[+] Found {len(real_files)} real human voice files and {len(fake_files)} AI cloned voice files.")
    return real_files, fake_files


def download_single_file(rfilename, label):
    local_filename = rfilename.replace("/", "_")
    local_path = os.path.join(CACHE_DIR, local_filename)
    
    if not os.path.exists(local_path):
        url = HF_BASE_URL + rfilename
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=10).read()
            with open(local_path, "wb") as f:
                f.write(data)
        except Exception as e:
            return []

    try:
        audio, sr = librosa.load(local_path, sr=16000)
        feat = extract_48_features_from_audio(audio, sr=16000)
        
        # Data augmentation for robust mic noise / pitch resilience
        noise = np.random.randn(len(audio)) * 0.005
        feat_noisy = extract_48_features_from_audio(audio + noise, sr=16000)
        return [(feat, label), (feat_noisy, label)]
    except Exception:
        return []


def download_and_extract_features(file_list, label, max_count=600):
    """Download audio files in parallel, extract 48 acoustic features."""
    from concurrent.futures import ThreadPoolExecutor
    os.makedirs(CACHE_DIR, exist_ok=True)
    X, y = [], []
    selected_files = file_list[:max_count]
    print(f"[+] Processing {len(selected_files)} samples in parallel for label={label} ({'AI Synthetic' if label==1 else 'Real Human'})...")
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(download_single_file, fn, label) for fn in selected_files]
        done_count = 0
        for fut in futures:
            res = fut.result()
            for feat, lbl in res:
                X.append(feat)
                y.append(lbl)
            done_count += 1
            if done_count % 100 == 0 or done_count == len(selected_files):
                print(f"  Processed {done_count}/{len(selected_files)} files...")

    return X, y


def main():
    print("=" * 70)
    print("PrimeVector - Voice Clone vs Real Voice Model Training")
    print("=" * 70)
    
    real_files, fake_files = fetch_dataset_file_list()
    
    # Extract features for real and fake samples (600 real, 600 fake -> 2400 total with augmentation)
    X_real, y_real = download_and_extract_features(real_files, label=0, max_count=600)
    X_fake, y_fake = download_and_extract_features(fake_files, label=1, max_count=600)
    
    X = np.array(X_real + X_fake, dtype=np.float64)
    y = np.array(y_real + y_fake, dtype=np.int64)
    
    print(f"\nTotal Dataset Size: {len(X)} samples (Real Human: {np.sum(y==0)}, AI Cloned: {np.sum(y==1)})")
    
    # Train / Test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("\nTraining Multi-Model Ensemble Classifier...")
    et = ExtraTreesClassifier(n_estimators=150, max_depth=15, min_samples_split=4, random_state=42)
    rf = RandomForestClassifier(n_estimators=150, max_depth=15, min_samples_split=4, random_state=42)
    gb = GradientBoostingClassifier(n_estimators=120, learning_rate=0.08, random_state=42)
    mlp = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=350, random_state=42)
    
    ensemble = VotingClassifier(
        estimators=[('et', et), ('rf', rf), ('gb', gb), ('mlp', mlp)],
        voting='soft'
    )
    
    ensemble.fit(X_train_scaled, y_train)
    
    # Evaluation
    y_pred = ensemble.predict(X_test_scaled)
    y_proba = ensemble.predict_proba(X_test_scaled)[:, 1]
    
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    
    print("\n" + "=" * 70)
    print(f"MODEL EVALUATION METRICS:")
    print(f"  * Test Accuracy: {acc * 100:.2f}%")
    print(f"  * AUC-ROC Score: {auc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Real Human", "AI Voice Clone"]))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("=" * 70)
    
    # Save model package
    package = {
        'model': ensemble,
        'scaler': scaler,
        'version': 'ml-ensemble-v7.0',
        'trained_at': time.strftime("%Y-%m-%d %H:%M:%S"),
        'metrics': {
            'accuracy': float(acc),
            'auc_roc': float(auc),
            'num_samples': int(len(X))
        }
    }
    
    joblib.dump(package, MODEL_OUT_PATH)
    print(f"Trained model saved to: {MODEL_OUT_PATH} (Size: {os.path.getsize(MODEL_OUT_PATH) / 1024 / 1024:.2f} MB)")
    print("Training Complete!")


if __name__ == "__main__":
    main()
