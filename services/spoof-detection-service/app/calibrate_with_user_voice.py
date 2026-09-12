"""
Fine-tune and calibrate spoof detection ensemble using user's real mic recording (Recording.m4a).
Slices 35s recording into 3s windows + augmentations (label 0: Real Human Voice)
and re-trains the ensemble inside Docker.
"""
import av
import os
import sys
import time
import joblib
import numpy as np
import librosa
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
from sklearn.model_selection import train_test_split

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(APP_DIR, "dataset_cache")
USER_REC_PATH = r"C:\Users\goura\Documents\Sound Recordings\Recording.m4a"
MODEL_OUT_PATH = os.path.join(APP_DIR, "trained_spoof_detector.joblib")

from train_advanced_spoof_model import extract_48_features_from_audio


def decode_m4a(path):
    container = av.open(path)
    resampler = av.AudioResampler(format='flt', layout='mono', rate=16000)
    chunks = []
    for f in container.decode(audio=0):
        for rf in resampler.resample(f):
            chunks.append(rf.to_ndarray().flatten())
    for rf in resampler.resample(None):
        chunks.append(rf.to_ndarray().flatten())
    return np.concatenate(chunks)


def main():
    print("[+] Loading user voice recording:", USER_REC_PATH)
    audio = decode_m4a(USER_REC_PATH)
    sr = 16000
    duration = len(audio) / sr
    print(f"[+] Loaded {duration:.2f}s of user real voice audio.")

    # Slice into 3.0s segments with 1.0s hop
    win_samples = 3 * sr
    hop_samples = 1 * sr
    user_feats = []
    
    for start in range(0, len(audio) - win_samples, hop_samples):
        segment = audio[start : start + win_samples]
        
        # Base feature
        f1 = extract_48_features_from_audio(segment, sr)
        user_feats.append(f1)
        
        # Augmentation 1: slight white noise
        f2 = extract_48_features_from_audio(segment + np.random.randn(len(segment)) * 0.003, sr)
        user_feats.append(f2)
        
        # Augmentation 2: gain variation
        f3 = extract_48_features_from_audio(segment * 1.2, sr)
        user_feats.append(f3)

        # Augmentation 3: lower gain
        f4 = extract_48_features_from_audio(segment * 0.8, sr)
        user_feats.append(f4)

    X_user = np.array(user_feats, dtype=np.float64)
    y_user = np.zeros(len(X_user), dtype=np.int64) # Label 0 = Real Human Voice
    print(f"[+] Created {len(X_user)} real human microphone feature vectors from user recording.")

    # Load existing dataset
    X_path = os.path.join(CACHE_DIR, "X.npy")
    y_path = os.path.join(CACHE_DIR, "y.npy")
    
    X_orig = np.load(X_path)
    y_orig = np.load(y_path)

    # Combine datasets
    X_combined = np.vstack([X_orig, X_user])
    y_combined = np.concatenate([y_orig, y_user])
    
    print(f"[+] Combined Dataset Size: {len(X_combined)} samples (Real Human: {np.sum(y_combined==0)}, AI Cloned: {np.sum(y_combined==1)})")
    
    # Update cache
    np.save(X_path, X_combined)
    np.save(y_path, y_combined)

    # Fit Model
    print("[+] Training Multi-Model Ensemble with calibrated user voice data...")
    X_train, X_test, y_train, y_test = train_test_split(X_combined, y_combined, test_size=0.2, random_state=42, stratify=y_combined)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    et = ExtraTreesClassifier(n_estimators=150, max_depth=15, min_samples_split=4, random_state=42)
    rf = RandomForestClassifier(n_estimators=150, max_depth=15, min_samples_split=4, random_state=42)
    gb = GradientBoostingClassifier(n_estimators=120, learning_rate=0.08, random_state=42)
    mlp = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=350, random_state=42)
    
    ensemble = VotingClassifier(
        estimators=[('et', et), ('rf', rf), ('gb', gb), ('mlp', mlp)],
        voting='soft'
    )
    
    ensemble.fit(X_train_scaled, y_train)
    
    y_pred = ensemble.predict(X_test_scaled)
    y_proba = ensemble.predict_proba(X_test_scaled)[:, 1]
    
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    
    print("=" * 60)
    print(f"CALIBRATED MODEL METRICS:")
    print(f"  * Accuracy: {acc * 100:.2f}%")
    print(f"  * AUC-ROC:  {auc:.4f}")
    print(classification_report(y_test, y_pred, target_names=["Real Human", "AI Voice Clone"]))
    print("=" * 60)

    # Verify score on full user recording
    feat_full = extract_48_features_from_audio(audio, sr)
    feat_full_scaled = scaler.transform(feat_full.reshape(1, -1))
    prob_full = ensemble.predict_proba(feat_full_scaled)[0]
    print(f"NEW USER VOICE EVALUATION:")
    print(f"   Real Human Prob: {prob_full[0]*100:.2f}% | Synthesis/Clone Prob: {prob_full[1]*100:.2f}%")
    
    # Save model package
    package = {
        'model': ensemble,
        'scaler': scaler,
        'version': 'ml-ensemble-v8.0-calibrated',
        'trained_at': time.strftime("%Y-%m-%d %H:%M:%S"),
        'metrics': {
            'accuracy': float(acc),
            'auc_roc': float(auc),
            'user_real_prob': float(prob_full[0]),
            'num_samples': int(len(X_combined))
        }
    }
    
    joblib.dump(package, MODEL_OUT_PATH)
    print(f"[+] Saved calibrated model package to: {MODEL_OUT_PATH}")

if __name__ == "__main__":
    main()
