"""
Fit Ensemble Classifier inside Docker container using sklearn 1.9.0.
"""
import os
import sys
import time
import joblib
import numpy as np

from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(APP_DIR, "dataset_cache")
MODEL_OUT_PATH = os.path.join(APP_DIR, "trained_spoof_detector.joblib")

def main():
    X_path = os.path.join(CACHE_DIR, "X.npy")
    y_path = os.path.join(CACHE_DIR, "y.npy")
    
    if not os.path.exists(X_path) or not os.path.exists(y_path):
        print(f"Error: {X_path} or {y_path} not found.")
        sys.exit(1)
        
    X = np.load(X_path)
    y = np.load(y_path)
    print(f"Loaded X shape: {X.shape}, y shape: {y.shape}")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("Fitting Multi-Model Ensemble in Docker (sklearn 1.9.0)...")
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
    print(f"DOCKER MODEL METRICS:")
    print(f"  * Accuracy: {acc * 100:.2f}%")
    print(f"  * AUC-ROC:  {auc:.4f}")
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Real Human", "AI Voice Clone"]))
    print("=" * 60)
    
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
    print(f"Saved trained joblib artifact to: {MODEL_OUT_PATH}")

if __name__ == "__main__":
    main()
