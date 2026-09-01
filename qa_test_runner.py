"""
QA Test Runner — generates synthetic audio, exercises all service endpoints.
Run from repo root: python qa_test_runner.py
"""
import base64
import json
import struct
import math
import sys
import urllib.request
import urllib.error
import time

BASE = "http://localhost"

def make_sine_pcm_base64(freq_hz: float, duration_s: float = 0.5, sample_rate: int = 16000) -> str:
    """Generate 16-bit PCM sine wave, return base64-encoded bytes."""
    n_samples = int(sample_rate * duration_s)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        val = int(32767 * 0.8 * math.sin(2 * math.pi * freq_hz * t))
        samples.append(val)
    pcm_bytes = struct.pack(f"<{len(samples)}h", *samples)
    return base64.b64encode(pcm_bytes).decode("ascii")

def post_json(url, data, timeout=30):
    """POST JSON, return parsed response."""
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode("utf-8")), resp.status
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        return {"error": error_body, "status_code": e.code}, e.code

def get_json(url, timeout=10):
    """GET JSON, return parsed response."""
    req = urllib.request.Request(url)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode("utf-8")), resp.status
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        return {"error": error_body, "status_code": e.code}, e.code

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def test_result(label, data):
    print(f"\n--- {label} ---")
    print(json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data))

# ===================================================================
# TEST 2.2: Feature Extraction Service
# ===================================================================
section("TEST 2.2: Feature Extraction — Real vs Stub Detection")

audio_440 = make_sine_pcm_base64(440.0, duration_s=1.0)
audio_880 = make_sine_pcm_base64(880.0, duration_s=1.0)

print(f"Audio 440Hz base64 length: {len(audio_440)}")
print(f"Audio 880Hz base64 length: {len(audio_880)}")

# Test A: 440Hz extraction
payload_440 = {
    "request_id": "test-440",
    "tenant_id": "qa-tenant",
    "audio_bytes": audio_440,
    "sample_rate_hz": 16000,
    "channels": 1,
}
print("\nPOSTing 440Hz audio to /v1/extract...")
resp_440, status_440 = post_json(f"{BASE}:8001/v1/extract", payload_440)
test_result("440Hz Extraction Response (truncated)", {
    "status": status_440,
    "request_id": resp_440.get("request_id"),
    "log_mel_shape": f"{len(resp_440.get('log_mel', {}).get('frames', []))} frames x {len(resp_440.get('log_mel', {}).get('frames', [[]])[0])} mels" if resp_440.get('log_mel') else "MISSING",
    "speaker_embedding_len": len(resp_440.get("speaker_embedding", [])),
    "speaker_embedding_first_5": resp_440.get("speaker_embedding", [])[:5],
    "speaker_embedding_last_5": resp_440.get("speaker_embedding", [])[-5:],
    "duration_ms": resp_440.get("duration_ms"),
})

# Check log_mel is real varying data
if resp_440.get("log_mel"):
    frames = resp_440["log_mel"]["frames"]
    all_values = [v for f in frames for v in f]
    unique_values = len(set(round(v, 6) for v in all_values))
    print(f"\nlog_mel unique values: {unique_values} (out of {len(all_values)} total)")
    print(f"log_mel value range: [{min(all_values):.4f}, {max(all_values):.4f}]")
    print(f"VERDICT: {'REAL 2D array with varying floats' if unique_values > 100 else 'SUSPICIOUS — too few unique values'}")

# Test B: 880Hz extraction
payload_880 = {
    "request_id": "test-880",
    "tenant_id": "qa-tenant",
    "audio_bytes": audio_880,
    "sample_rate_hz": 16000,
    "channels": 1,
}
print("\nPOSTing 880Hz audio to /v1/extract...")
resp_880, status_880 = post_json(f"{BASE}:8001/v1/extract", payload_880)
test_result("880Hz Extraction Response (truncated)", {
    "status": status_880,
    "speaker_embedding_len": len(resp_880.get("speaker_embedding", [])),
    "speaker_embedding_first_5": resp_880.get("speaker_embedding", [])[:5],
})

# Compare embeddings — DIFFERENT inputs should produce DIFFERENT embeddings
emb_440 = resp_440.get("speaker_embedding", [])
emb_880 = resp_880.get("speaker_embedding", [])
if emb_440 and emb_880:
    diff = sum(abs(a - b) for a, b in zip(emb_440, emb_880))
    print(f"\nEmbedding L1 distance (440Hz vs 880Hz): {diff:.6f}")
    print(f"VERDICT: {'DIFFERENT embeddings (REAL model)' if diff > 0.01 else 'STUB DETECTED — embeddings are identical or near-identical for different inputs'}")

# Test C: Determinism — same input twice
print("\nPOSTing 440Hz audio AGAIN for determinism check...")
resp_440b, _ = post_json(f"{BASE}:8001/v1/extract", payload_440)
emb_440b = resp_440b.get("speaker_embedding", [])
if emb_440 and emb_440b:
    diff_same = sum(abs(a - b) for a, b in zip(emb_440, emb_440b))
    print(f"Embedding L1 distance (440Hz run1 vs run2): {diff_same:.6f}")
    print(f"VERDICT: {'DETERMINISTIC' if diff_same < 0.001 else 'NON-DETERMINISTIC — same input produced different embeddings'}")

# ===================================================================
# TEST 2.3: Spoof Detection Service
# ===================================================================
section("TEST 2.3: Spoof Detection — Real Varying Scores")

# Use log_mel from 440Hz extraction, flattened
if resp_440.get("log_mel"):
    flat_440 = [v for f in resp_440["log_mel"]["frames"] for v in f]
    spoof_payload_440 = {
        "call_session_id": "test-spoof-440",
        "tenant_id": "qa-tenant",
        "audio_features": flat_440,
    }
    print(f"\nPOSTing 440Hz features ({len(flat_440)} values) to /v1/detect...")
    spoof_resp_440, spoof_status_440 = post_json(f"{BASE}:8002/v1/detect", spoof_payload_440)
    test_result("Spoof Detection — 440Hz", spoof_resp_440)

    # Low-variance input (uniform)
    uniform_features = [0.5] * len(flat_440)
    spoof_payload_uniform = {
        "call_session_id": "test-spoof-uniform",
        "tenant_id": "qa-tenant",
        "audio_features": uniform_features,
    }
    print(f"\nPOSTing UNIFORM features to /v1/detect...")
    spoof_resp_uniform, _ = post_json(f"{BASE}:8002/v1/detect", spoof_payload_uniform)
    test_result("Spoof Detection — Uniform (low variance)", spoof_resp_uniform)

    score_440 = spoof_resp_440.get("score", -1)
    score_uniform = spoof_resp_uniform.get("score", -1)
    print(f"\nScore comparison: 440Hz={score_440:.4f}, Uniform={score_uniform:.4f}")
    print(f"VERDICT: {'Scores VARY meaningfully' if abs(score_440 - score_uniform) > 0.05 else 'SUSPICIOUS — scores too similar for very different inputs'}")
    print(f"Available flag: {spoof_resp_440.get('available')}")

# ===================================================================
# TEST 2.5: Content Risk (via orchestrator endpoint check)
# ===================================================================
section("TEST 2.5: Content Risk — Groq LLM Transcript Analysis")

# The content risk is embedded in the orchestrator pipeline, not a standalone endpoint.
# We need to test it through the orchestrator. But first, let's check if there's a direct endpoint.
# Based on code review: content_risk.py is a module in the orchestrator, called from main.py pipeline.
# No standalone HTTP endpoint — tested via full pipeline.

print("Content-risk is embedded in orchestrator pipeline (no standalone endpoint).")
print("Will be tested via full pipeline in Test 2.8.")

# ===================================================================
# TEST 2.6: Risk Fusion Engine — Noisy-OR behavior
# ===================================================================
section("TEST 2.6: Risk Fusion Engine — Noisy-OR Fusion")

# Test (a): All signals low
fusion_a = {
    "call_session_id": "test-fusion-a",
    "tenant_id": "qa-tenant",
    "synthesis_signal": {"score": 0.1, "confidence": 0.9, "available": True, "detail": "low"},
    "speaker_match_signal": {"score": 0.05, "confidence": 0.95, "available": True, "detail": "low"},
    "contextual_signal": {"score": 0.1, "confidence": 1.0, "available": True, "detail": "low"},
    "content_risk_signal": {"score": 0.1, "confidence": 0.85, "available": True, "detail": "low"},
}
print("\n(a) All signals LOW:")
resp_a, _ = post_json(f"{BASE}:8000/v1/assess", fusion_a)
test_result("Fusion (a) — all low", resp_a)

# Test (b): content_risk high, everything else low
fusion_b = {
    "call_session_id": "test-fusion-b",
    "tenant_id": "qa-tenant",
    "synthesis_signal": {"score": 0.1, "confidence": 0.9, "available": True, "detail": "low"},
    "speaker_match_signal": {"score": 0.05, "confidence": 0.95, "available": True, "detail": "low"},
    "contextual_signal": {"score": 0.1, "confidence": 1.0, "available": True, "detail": "low"},
    "content_risk_signal": {"score": 0.9, "confidence": 0.85, "available": True, "detail": "scam detected"},
}
print("\n(b) content_risk HIGH (0.9), others low:")
resp_b, _ = post_json(f"{BASE}:8000/v1/assess", fusion_b)
test_result("Fusion (b) — content_risk high", resp_b)

score_a = resp_a.get("risk_score", -1)
score_b = resp_b.get("risk_score", -1)
print(f"\nScore (a)={score_a:.4f} vs Score (b)={score_b:.4f}")
print(f"VERDICT: {'content_risk IS wired into fusion — score increased' if score_b > score_a + 0.1 else 'BROKEN — content_risk not affecting fusion score'}")

# Test (c): content_risk unavailable
fusion_c = {
    "call_session_id": "test-fusion-c",
    "tenant_id": "qa-tenant",
    "synthesis_signal": {"score": 0.1, "confidence": 0.9, "available": True, "detail": "low"},
    "speaker_match_signal": {"score": 0.05, "confidence": 0.95, "available": True, "detail": "low"},
    "contextual_signal": {"score": 0.1, "confidence": 1.0, "available": True, "detail": "low"},
    "content_risk_signal": {"score": 0.0, "confidence": 0.0, "available": False, "detail": "unavailable"},
}
print("\n(c) content_risk available=false:")
resp_c, _ = post_json(f"{BASE}:8000/v1/assess", fusion_c)
test_result("Fusion (c) — content_risk unavailable", resp_c)

# Test (d): All signals high
fusion_d = {
    "call_session_id": "test-fusion-d",
    "tenant_id": "qa-tenant",
    "synthesis_signal": {"score": 0.9, "confidence": 0.9, "available": True, "detail": "high"},
    "speaker_match_signal": {"score": 0.85, "confidence": 0.95, "available": True, "detail": "high"},
    "contextual_signal": {"score": 0.8, "confidence": 1.0, "available": True, "detail": "high"},
    "content_risk_signal": {"score": 0.9, "confidence": 0.85, "available": True, "detail": "scam"},
}
print("\n(d) All signals HIGH:")
resp_d, _ = post_json(f"{BASE}:8000/v1/assess", fusion_d)
test_result("Fusion (d) — all high", resp_d)

# ===================================================================
# TEST 2.8: Full Pipeline Through Orchestrator
# ===================================================================
section("TEST 2.8: Full End-to-End Pipeline — Orchestrator")

pipeline_payload = {
    "session_id": "qa-e2e-001",
    "tenant_id": "qa-tenant",
    "subject_id": "qa-subject-001",
    "audio_pcm_base64": audio_440,
    "sample_rate_hz": 16000,
    "channels": 1,
    "context_score": 0.3,
    "transcript": "Please transfer 50000 rupees immediately and share the OTP you just received"
}
print("\nPOSTing full pipeline request with scam transcript...")
resp_pipeline, pipeline_status = post_json(f"{BASE}:8080/v1/pipeline/process", pipeline_payload, timeout=60)
test_result("Full Pipeline Response", resp_pipeline)
print(f"\nHTTP Status: {pipeline_status}")

# Check no raw audio in response
resp_str = json.dumps(resp_pipeline)
has_audio = "audio_pcm_base64" in resp_str or "audio_bytes" in resp_str
print(f"Raw audio in response: {'YES — PRIVACY VIOLATION' if has_audio else 'NO — clean (privacy check passed)'}")

# Now test with benign transcript
pipeline_benign = {
    "session_id": "qa-e2e-002",
    "tenant_id": "qa-tenant",
    "subject_id": "qa-subject-001",
    "audio_pcm_base64": audio_440,
    "sample_rate_hz": 16000,
    "channels": 1,
    "context_score": 0.1,
    "transcript": "Are we still meeting for lunch tomorrow?"
}
print("\nPOSTing full pipeline request with BENIGN transcript...")
resp_benign, _ = post_json(f"{BASE}:8080/v1/pipeline/process", pipeline_benign, timeout=60)
test_result("Benign Pipeline Response (summary)", {
    "risk_score": resp_benign.get("risk_assessment", {}).get("risk_score") if resp_benign.get("risk_assessment") else None,
    "final_action": resp_benign.get("final_action"),
    "content_risk_signal": resp_benign.get("content_risk_signal"),
    "degraded": resp_benign.get("degraded"),
})

# Compare content risk scores
scam_content = resp_pipeline.get("content_risk_signal", {})
benign_content = resp_benign.get("content_risk_signal", {})
if scam_content and benign_content:
    print(f"\nContent risk: scam={scam_content.get('score', 'N/A')}, benign={benign_content.get('score', 'N/A')}")

print("\n" + "="*70)
print("  ALL TESTS COMPLETE")
print("="*70)
