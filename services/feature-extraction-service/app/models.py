from pydantic import BaseModel
from typing import List

class ExtractionRequest(BaseModel):
    request_id: str
    tenant_id: str
    audio_bytes: bytes  # base64 in JSON
    sample_rate_hz: int = 16000
    channels: int = 1

class LogMelFeatures(BaseModel):
    frames: List[List[float]]
    n_mels: int = 80
    hop_length_ms: float = 10.0
    sample_rate_hz: int = 16000

class ExtractionResponse(BaseModel):
    request_id: str
    log_mel: LogMelFeatures
    speaker_embedding: List[float]
    duration_ms: float
    # DESIGN.md §7: raw audio is never persisted, so no audio_bytes here.
