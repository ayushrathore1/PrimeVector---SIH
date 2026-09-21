"""Quick E2E pipeline verification — checks which AI model path is active."""
import base64, json, math, struct, time, urllib.request, urllib.error

ORCHESTRATOR = "http://localhost:8080"

def make_audio(freq=440.0, dur=1.0, sr=16000):
    n = int(sr * dur)
    s = [int(32767*0.8*math.sin(2*math.pi*freq*i/sr)) for i in range(n)]
    return base64.b64encode(struct.pack(f"<{n}h", *s)).decode()

def post(url, data, timeout=120):
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()}, e.code
    except Exception as e:
        return {"error": str(e)}, 503

payload = {
    "session_id": "verify-001", "tenant_id": "qa", "subject_id": "qa-001",
    "audio_pcm_base64": make_audio(), "sample_rate_hz": 16000, "channels": 1,
    "context_score": 0.3,
    "transcript": "Transfer 50000 rupees now and share the OTP. RBI has flagged your account, it will be blocked."
}

print("=" * 60)
print("  PIPELINE VERIFICATION")
print("=" * 60)
print(f"Calling orchestrator (timeout=120s)...")

t0 = time.monotonic()
result, status = post(f"{ORCHESTRATOR}/v1/pipeline/process", payload)
elapsed = time.monotonic() - t0

if "error" in result:
    print(f"ERROR (HTTP {status}): {str(result['error'])[:200]}")
else:
    print(f"Latency: {elapsed:.1f}s | Final: {result.get('final_action')}")
    cr = result.get("content_risk_signal") or {}
    sy = result.get("synthesis_signal") or {}
    cr_d = cr.get("detail", "") if isinstance(cr, dict) else ""
    sy_d = sy.get("detail", "") if isinstance(sy, dict) else ""
    cr_s = cr.get("score", "?") if isinstance(cr, dict) else "?"
    sy_s = sy.get("score", "?") if isinstance(sy, dict) else "?"
    print(f"\nContent Risk  : score={cr_s}  detail={cr_d}")
    print(f"Synthesis     : score={sy_s}  detail={sy_d}")
    if "[Ollama LLM]" in cr_d:
        print("\n[OK] Content Risk => Ollama qwen3:1.7b LLM (PRIMARY)")
    elif "Multilingual" in cr_d:
        print("\n[FALLBACK] Content Risk => NLP keywords (Ollama failed)")
    if "heuristic" in sy_d.lower():
        print("[FALLBACK] Synthesis => Heuristic (deepfake model not loaded)")
    else:
        print("[OK] Synthesis => Deepfake model (PRIMARY)")
