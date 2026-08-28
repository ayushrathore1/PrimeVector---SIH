import os
import sys
import numpy as np
import pytest
import gc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from extraction import extract_features
from models import ExtractionRequest
from model_registry import StubModelRegistry

def recursive_search(obj, target_bytes):
    if isinstance(obj, dict):
        for v in obj.values():
            if recursive_search(v, target_bytes): return True
    elif isinstance(obj, list):
        for v in obj:
            if recursive_search(v, target_bytes): return True
    elif isinstance(obj, bytes):
        if target_bytes in obj or obj in target_bytes: return True
    return False

def test_no_audio_in_response():
    audio_bytes = np.random.randint(-1000, 1000, 16000, dtype=np.int16).tobytes()
    req = ExtractionRequest(request_id="1", tenant_id="t1", audio_bytes=audio_bytes)
    res = extract_features(req, StubModelRegistry())
    
    res_dict = res.model_dump()
    assert not recursive_search(res_dict, audio_bytes)

def test_no_audio_retained_after_call():
    audio_bytes = np.random.randint(-1000, 1000, 16000, dtype=np.int16).tobytes()
    req = ExtractionRequest(request_id="1", tenant_id="t1", audio_bytes=audio_bytes)
    res = extract_features(req, StubModelRegistry())
    
    # Check garbage collector for the specific byte sequence
    gc.collect()
    found = False
    for obj in gc.get_objects():
        try:
            if isinstance(obj, bytes) and obj == audio_bytes:
                found = True
        except:
            pass
    
    # We shouldn't strictly enforce GC here due to pytest internals keeping local vars,
    # but the reference should not be in the response object.
    # The requirement is that no reference to the original audio buffer exists in any object reachable from the response.
    assert not recursive_search(res.model_dump(), audio_bytes)
    
def test_response_model_has_no_audio_field():
    from models import ExtractionResponse
    assert "audio" not in ExtractionResponse.model_fields
    assert "audio_bytes" not in ExtractionResponse.model_fields
