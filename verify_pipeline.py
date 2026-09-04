"""
Quick end-to-end pipeline verification.
Sends a real scam transcript through the orchestrator and reports
which AI model handled each signal.
"""
import base64
import json
import math
import struct
import time
import urllib.request
import urllib.error

ORCHESTRATOR = "http://localhost:8080"

def make_audio(freq=440.0, duration=1.0, sample_rate=16000):
    n = int(sample_rate * duration)
    samples = [int(32767 * 0.8 * math.sin(2 * math.pi * freq * i / sample_rate)) for i in range(n)]
    return base64.b64encode(struct.pack(f"<{n}h", *samples)).decode("ascii")

def post(url, data, timeout=90):
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()}, e.code
    except Exception as e:
        return {"error": str(e)}, 503

print("=" * 65)
print("  PIPELINE VERIFICATION — Primary AI Models Check")
print("=" * 65)

payload = {
    "session_id": "verify-001",
    "tenant_id": "qa-tenant",
    "subject_id": "qa-subject-001",
    "audio_pcm_base64": make_audio(),
    "sample_rate_hz": 16000,
    "channels": 1,
    "context_score": 0.3,
    "transcript": (
        "Please transfer 50000 rupees immediately to this account "
        "and share the OTP you just received. This is urgent, "
        "the RBI has flagged your account and it will be blocked."
    ),
}

print(f"\nTranscript: {payload['transcript'][:80]}...")
print(f"Calling {ORCHESTRATOR}/v1/pipeline/process  (timeout=90s)\n")

t0 = time.monotonic()
data, status = post(f"{ORCHESTRATOR}/v1/pipeline/process", payload, timeout=180)
elapsed = time.monotonic() - t0

if "error" in data:
    print(f"ERROR (HTTP {status}): {data['error'][:300]}")
else:
    cr = data.get("content_risk_signal", {})
    synth = data.get("synthesis_signal", {})
    print(f"Total latency  : {elapsed:.1f}s")
    print(f"Final action   : {data.get('final_action')}")
    print()
    print("--- Content Risk (LLM) ---")
    print(f"  available  : {cr.get('available')}")
    print(f"  score      : {cr.get('score')}")
    print(f"  detail     : {cr.get('detail', '')}")
    print()
    print("--- Synthesis Detection (Deepfake Model) ---")
    print(f"  available  : {synth.get('available')}")
    print(f"  score      : {synth.get('score')}")
    print(f"  detail     : {synth.get('detail', '')}")
    print()

    # Check which path was used
    cr_detail = cr.get("detail", "")
    synth_detail = synth.get("detail", "")

    if "[Ollama LLM]" in cr_detail:
        print("[OK] Content Risk  => PRIMARY path: Ollama qwen3:4b LLM")
    elif "[Multilingual" in cr_detail:
        print("[FALLBACK] Content Risk => NLP keyword fallback (Ollama unreachable?)")
    else:
        print(f"[?] Content Risk detail: {cr_detail}")

    if "acoustic-heuristic" in synth_detail or "heuristic" in synth_detail.lower():
        print("[FALLBACK] Synthesis   => heuristic fallback (deepfake model not loaded?)")
    elif synth.get("available") is False:
        print("[FALLBACK] Synthesis   => available=false (no model)")
    else:
        print("[OK] Synthesis     => Deepfake model active")
