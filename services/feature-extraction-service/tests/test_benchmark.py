import os
import sys
import numpy as np
import pytest
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from extraction import extract_features
from models import ExtractionRequest
from model_registry import StubModelRegistry

def test_p99_latency_under_80ms():
    registry = StubModelRegistry()
    durations = []
    
    # Pre-warm
    dummy_req = ExtractionRequest(
        request_id="0", 
        tenant_id="t", 
        audio_bytes=np.zeros(16000, dtype=np.int16).tobytes()
    )
    extract_features(dummy_req, registry)
    
    for i in range(100):
        audio_bytes = np.random.randint(-100, 100, 16000, dtype=np.int16).tobytes()
        req = ExtractionRequest(
            request_id=str(i),
            tenant_id="t1",
            audio_bytes=audio_bytes
        )
        
        start = time.time()
        extract_features(req, registry)
        end = time.time()
        
        durations.append((end - start) * 1000.0)
        
    p99 = np.percentile(durations, 99)
    assert p99 < 80.0, f"p99 latency ({p99:.2f}ms) exceeds 80ms budget"
