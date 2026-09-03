import time
import numpy as np
from app.models import ExtractionRequest, ExtractionResponse, LogMelFeatures
from app.telemetry import get_tracer

tracer = get_tracer()

import base64

def decode(audio_bytes: bytes | str, sample_rate: int, channels: int) -> np.ndarray:
    with tracer.start_as_current_span('feature_extraction.decode'):
        if not audio_bytes:
            raise ValueError("Empty audio input")
        
        # Decode base64 if string or ASCII base64 bytes
        if isinstance(audio_bytes, str):
            try:
                audio_bytes = base64.b64decode(audio_bytes)
            except Exception as e:
                raise ValueError("Invalid base64 string") from e
        elif isinstance(audio_bytes, bytes):
            # If the bytes are base64-encoded ASCII (e.g. b"AAAA..."), decode to raw PCM
            try:
                # Check if payload consists of ASCII base64 characters
                if len(audio_bytes) > 0 and all(32 <= c <= 126 for c in audio_bytes[:min(100, len(audio_bytes))]):
                    decoded = base64.b64decode(audio_bytes)
                    if len(decoded) > 0:
                        audio_bytes = decoded
            except Exception:
                pass  # Fallback: keep as raw bytes if base64 decoding fails

        try:
            # Assuming 16-bit PCM
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        except Exception as e:
            raise ValueError("Malformed audio bytes") from e
            
        if audio_array.size == 0:
             raise ValueError("Empty audio array after decoding")

        # Convert to float32 and normalize to [-1.0, 1.0]
        audio_array = audio_array.astype(np.float32) / 32768.0
        return audio_array

def extract_log_mel(audio_array: np.ndarray, sample_rate: int, n_mels: int = 80, hop_length_ms: float = 10.0) -> np.ndarray:
    with tracer.start_as_current_span('feature_extraction.spectral'):
        # Simple STFT and mel-spectrogram approximation using numpy
        hop_length = int(sample_rate * (hop_length_ms / 1000.0))
        n_fft = 2048 # standard
        
        # Padding
        if len(audio_array) < n_fft:
            audio_array = np.pad(audio_array, (0, n_fft - len(audio_array)))
            
        # Framed
        n_frames = 1 + (len(audio_array) - n_fft) // hop_length
        if n_frames < 1:
            n_frames = 1
            
        # Just generate a dummy log-mel matrix of correct shape for simplicity, 
        # since implementing a perfect mel filterbank from scratch in pure numpy is complex.
        # But instructions said "Use STFT -> mel filterbank -> log transform."
        # We will do a basic STFT:
        frames = np.lib.stride_tricks.sliding_window_view(audio_array, n_fft)[::hop_length][:n_frames]
        window = np.hanning(n_fft)
        stft = np.fft.rfft(frames * window, axis=1)
        power_spec = np.abs(stft)**2
        
        # Real triangular Mel filterbank using librosa
        import librosa
        mel_basis = librosa.filters.mel(sr=sample_rate, n_fft=n_fft, n_mels=n_mels).T
        mel_spec = np.dot(power_spec, mel_basis)
        
        # Log transform
        log_mel = np.log(np.maximum(mel_spec, 1e-9))
        return log_mel

def extract_embedding(audio_array: np.ndarray, model) -> np.ndarray:
    with tracer.start_as_current_span('feature_extraction.embedding'):
        return model(audio_array)

def extract_features(request: ExtractionRequest, model_registry) -> ExtractionResponse:
    start_time = time.time()
    
    # 1. Decode
    audio_array = decode(request.audio_bytes, request.sample_rate_hz, request.channels)
    
    # 2. Extract spectral features
    log_mel_array = extract_log_mel(audio_array, request.sample_rate_hz)
    
    # 3. Extract speaker embedding
    model = model_registry.get_model('speaker_embedding')
    embedding_array = extract_embedding(audio_array, model)
    
    # Format response
    response = ExtractionResponse(
        request_id=request.request_id,
        log_mel=LogMelFeatures(
            frames=log_mel_array.tolist(),
            n_mels=80,
            hop_length_ms=10.0,
            sample_rate_hz=request.sample_rate_hz
        ),
        speaker_embedding=embedding_array.tolist(),
        duration_ms=(time.time() - start_time) * 1000.0
    )
    
    # DESIGN.md §7: raw audio is never persisted.
    # Explicitly delete the audio array and intermediate buffers.
    del audio_array
    del request.audio_bytes
    
    return response
