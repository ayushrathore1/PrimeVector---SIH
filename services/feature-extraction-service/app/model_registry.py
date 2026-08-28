import hashlib
from abc import ABC, abstractmethod
from typing import Any
import numpy as np

class ModelRegistry(ABC):
    @abstractmethod
    def get_model(self, model_name: str, version: str | None = None) -> Any: ...

class StubSpeakerEmbeddingModel:
    """Deterministic stub: hash-based so same audio -> same embedding."""
    def __call__(self, audio_array: np.ndarray) -> np.ndarray:
        seed = int(hashlib.sha256(audio_array.tobytes()).hexdigest()[:8], 16)
        return np.random.default_rng(seed=seed).random(192).astype(np.float32)

class StubModelRegistry(ModelRegistry):
    def get_model(self, model_name, version=None):
        if model_name == 'speaker_embedding':
            return StubSpeakerEmbeddingModel()
        raise ValueError(f'Unknown model: {model_name}')
