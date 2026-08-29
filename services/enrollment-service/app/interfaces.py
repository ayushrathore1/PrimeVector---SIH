"""
Abstract interfaces for the enrollment service's external dependencies.

These exist so the enrollment domain logic (enrollment.py) never couples to
a specific liveness-detection model, speaker-embedding model, or storage
backend. Each has a stub implementation for wiring and testing; production
implementations are provided by separate packages / services.

Design note (DESIGN.md §4.3): models are served via a versioned Model
Registry, never hardcoded into a service. The ModelRegistry ABC here
captures that contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Liveness checker
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LivenessResult:
    """Outcome of a liveness/anti-replay check on a capture session."""
    passed: bool
    confidence: float   # 0.0–1.0
    detail: str         # human-readable reason, for audit


class LivenessChecker(ABC):
    """
    Determines whether a capture session is a live human utterance
    (not replayed / synthesised).

    The actual model is a separate ticket — this interface exists so the
    enrollment control flow is fully wired: a failed liveness check
    rejects the session and does NOT count toward the 3-session
    requirement.
    """

    @abstractmethod
    def check(self, audio_embedding: list[float],
              challenge_phrase: str) -> LivenessResult:
        """
        Check liveness for the given audio embedding against the expected
        challenge phrase.

        Parameters
        ----------
        audio_embedding : list[float]
            The embedding vector extracted from the audio (NOT raw audio).
        challenge_phrase : str
            The server-generated challenge phrase the subject was asked
            to repeat.

        Returns
        -------
        LivenessResult
            Whether the session passes liveness, with confidence and detail.
        """
        ...


class StubLivenessChecker(LivenessChecker):
    """
    Stub that always passes liveness. Used for integration wiring and
    testing. Replace with a real implementation when the liveness-model
    ticket lands.
    """

    def __init__(self, *, force_fail: bool = False):
        self._force_fail = force_fail

    def check(self, audio_embedding: list[float],
              challenge_phrase: str) -> LivenessResult:
        if self._force_fail:
            return LivenessResult(
                passed=False,
                confidence=0.95,
                detail="stub: forced failure for testing",
            )
        return LivenessResult(
            passed=True,
            confidence=0.99,
            detail="stub: liveness check passed (stub implementation)",
        )


# ---------------------------------------------------------------------------
# Speaker-embedding model
# ---------------------------------------------------------------------------

@runtime_checkable
class SpeakerEmbeddingModel(Protocol):
    """
    Protocol for a speaker-embedding model. Takes raw audio bytes,
    returns an embedding vector. Raw audio must NEVER be stored — only
    the returned embedding is persisted (DESIGN.md §4.2, §7).
    """

    def extract_embedding(self, audio_bytes: bytes) -> list[float]:
        ...


class StubSpeakerEmbeddingModel:
    """
    Stub that returns a deterministic fake embedding. Only for tests.
    Production code uses ResemblyzerSpeakerEmbeddingModel.
    """

    def extract_embedding(self, audio_bytes: bytes) -> list[float]:
        # Deterministic 192-dim embedding derived from audio length,
        # so tests can verify the embedding was produced from input.
        dim = 192
        seed = len(audio_bytes) % 256
        return [float((seed + i) % 256) / 255.0 for i in range(dim)]


class ResemblyzerSpeakerEmbeddingModel:
    """
    Real speaker-embedding model using Resemblyzer (loaded ONCE).

    Produces real 256-dim speaker-verification embeddings from the
    pretrained GE2E model, sliced to 192 dims to match the
    feature-extraction-service contract.

    Raw audio is decoded from PCM bytes in-memory, used for embedding
    extraction, and immediately discarded — NEVER persisted
    (DESIGN.md §7).
    """

    def __init__(self):
        import numpy as np
        from resemblyzer import VoiceEncoder
        self._encoder = VoiceEncoder()
        self._np = np

    def extract_embedding(self, audio_bytes: bytes) -> list[float]:
        # Decode 16-bit PCM to float32 [-1.0, 1.0]
        audio_array = self._np.frombuffer(audio_bytes, dtype=self._np.int16)
        audio_float = audio_array.astype(self._np.float32) / 32768.0
        # Resemblyzer produces a real 256-dim GE2E embedding
        embedding = self._encoder.embed_utterance(audio_float)
        # Slice to 192 dims to match feature-extraction-service contract
        result = embedding[:192].astype(self._np.float32).tolist()
        # DESIGN.md §7: discard audio immediately
        del audio_array, audio_float
        return result


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

class ModelRegistry(ABC):
    """
    Versioned model registry (DESIGN.md §4.3). Every model (spoof
    detector, speaker-embedding model) is served via a versioned entry,
    never hardcoded into a service.
    """

    @abstractmethod
    def get_speaker_embedding_model(
        self, version: str | None = None,
    ) -> SpeakerEmbeddingModel:
        ...


class StubModelRegistry(ModelRegistry):
    """Stub registry that always returns StubSpeakerEmbeddingModel. For tests only."""

    def get_speaker_embedding_model(
        self, version: str | None = None,
    ) -> SpeakerEmbeddingModel:
        return StubSpeakerEmbeddingModel()


class RealModelRegistry(ModelRegistry):
    """
    Production registry that returns a real Resemblyzer speaker-embedding
    model, loaded ONCE at startup. Uses the same pretrained GE2E model as
    feature-extraction-service so enrolled voiceprints and live embeddings
    occupy the same vector space (critical for cosine comparison).
    """

    def __init__(self):
        # Load once; Resemblyzer model download happens here.
        self._model = ResemblyzerSpeakerEmbeddingModel()

    def get_speaker_embedding_model(
        self, version: str | None = None,
    ) -> SpeakerEmbeddingModel:
        return self._model


# ---------------------------------------------------------------------------
# Voiceprint store
# ---------------------------------------------------------------------------

class VoiceprintStore(ABC):
    """
    Abstract storage backend for voiceprints, capture sessions, and
    audit log entries. In-memory implementation in store.py; production
    would use a database with encryption at rest (DESIGN.md §4.9).

    Type annotations use Any to avoid circular imports with models.py.
    Concrete implementations (store.py) import and use the actual types.
    """

    @abstractmethod
    def save_voiceprint(self, voiceprint: Any) -> None: ...

    @abstractmethod
    def get_voiceprint(
        self, tenant_id: str, subject_id: str,
    ) -> Any: ...

    @abstractmethod
    def save_session(self, session: Any) -> None: ...

    @abstractmethod
    def get_sessions(
        self, tenant_id: str, subject_id: str,
    ) -> list: ...

    @abstractmethod
    def save_audit_entry(self, entry: Any) -> None: ...

    @abstractmethod
    def get_audit_log(
        self, tenant_id: str, subject_id: str,
    ) -> list: ...
