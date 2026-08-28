import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from extraction import decode, extract_log_mel, extract_embedding, extract_features
from models import ExtractionRequest
from model_registry import StubModelRegistry

def test_decode_valid_pcm():
    # 1 second of 16kHz mono silence
    silence = np.zeros(16000, dtype=np.int16).tobytes()
    decoded = decode(silence, 16000, 1)
    assert decoded.shape == (16000,)
    assert decoded.dtype == np.float32

def test_decode_malformed_audio():
    # random non-PCM bytes that cannot form a valid int16 array
    # e.g., 3 bytes long
    bad_bytes = b'\x00\x01\x02'
    with pytest.raises(ValueError, match="Malformed audio bytes|Empty audio array"):
        decode(bad_bytes, 16000, 1)

def test_decode_empty_input():
    with pytest.raises(ValueError, match="Empty audio input"):
        decode(b'', 16000, 1)

def test_decode_sub_100ms_chunk():
    # 50ms of audio (800 samples)
    chunk = np.zeros(800, dtype=np.int16).tobytes()
    decoded = decode(chunk, 16000, 1)
    assert decoded.shape == (800,)

def test_log_mel_output_shape():
    audio = np.random.rand(16000).astype(np.float32)
    log_mel = extract_log_mel(audio, 16000, n_mels=80)
    assert log_mel.shape[1] == 80

def test_embedding_output_shape():
    audio = np.random.rand(16000).astype(np.float32)
    registry = StubModelRegistry()
    model = registry.get_model('speaker_embedding')
    emb = extract_embedding(audio, model)
    assert emb.shape == (192,)

def test_embedding_deterministic():
    audio1 = np.ones(16000).astype(np.float32)
    audio2 = np.ones(16000).astype(np.float32)
    registry = StubModelRegistry()
    model = registry.get_model('speaker_embedding')
    emb1 = extract_embedding(audio1, model)
    emb2 = extract_embedding(audio2, model)
    np.testing.assert_array_almost_equal(emb1, emb2)
