import numpy as np
from typing import Any

def cosine_distance(v1: np.ndarray, v2: np.ndarray) -> float:
    """Returns distance in [0, 2]. 0 = identical, higher = more different."""
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 1.0
    return float(1.0 - (np.dot(v1, v2) / (norm1 * norm2)))


def compute_speaker_match_signal(
    live_embedding: list[float],
    enrolled_embeddings: list[list[float]],
) -> dict[str, Any]:
    """
    Compares live_embedding against all enrolled_embeddings for a voiceprint.

    Returns a RiskSignal dictionary shape (score, confidence, available, detail):
    - score: minimum cosine distance (0.0 = identical, 1.0+ = mismatch)
    - confidence: 0.95 when enrolled embeddings present, 0.0 when missing
    - available: True if enrolled embeddings exist, False otherwise
    """
    if not live_embedding or not enrolled_embeddings:
        return {
            "score": 0.5,
            "confidence": 0.0,
            "available": False,
            "detail": "No enrolled voiceprint on file",
        }

    live_arr = np.array(live_embedding, dtype=np.float32)
    distances = [
        cosine_distance(live_arr, np.array(e, dtype=np.float32))
        for e in enrolled_embeddings
    ]
    min_dist = float(min(distances))
    # Clamp score to [0.0, 1.0]
    score = max(0.0, min(1.0, min_dist))

    return {
        "score": score,
        "confidence": 0.95,
        "available": True,
        "detail": f"speaker distance={score:.4f} across {len(enrolled_embeddings)} enrolled sessions",
    }
