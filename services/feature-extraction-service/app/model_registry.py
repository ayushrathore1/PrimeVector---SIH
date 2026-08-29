import hashlib
from abc import ABC, abstractmethod
from typing import Any
import numpy as np

from resemblyzer import VoiceEncoder

class ModelRegistry(ABC):
    @abstractmethod
    def get_model(self, model_name: str, version: str | None = None) -> Any: ...

class RealSpeakerEmbeddingModel:
    """Real speaker embedding model using Resemblyzer (loaded ONCE at startup)."""
    def __init__(self):
        self.encoder = VoiceEncoder()

    def __call__(self, audio_array: np.ndarray) -> np.ndarray:
        # Resemblyzer produces real 256-dim vector; slice to 192 to match schema contract
        embedding = self.encoder.embed_utterance(audio_array)
        return embedding[:192].astype(np.float32)

class StubModelRegistry(ModelRegistry):
    def __init__(self):
        # Loaded ONCE at service startup
        self._speaker_model = RealSpeakerEmbeddingModel()

    def get_model(self, model_name, version=None):
        if model_name == 'speaker_embedding':
            return self._speaker_model
        raise ValueError(f'Unknown model: {model_name}')

