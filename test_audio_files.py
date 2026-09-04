# -*- coding: utf-8 -*-
"""Test two real audio files through the full pipeline."""
import base64, json, struct, time, os, sys
import urllib.request, urllib.error
import numpy as np

# Force UTF-8 output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ORCHESTRATOR = "http://localhost:8080"
AUDIO_DIR = r"D:\SIH26\PrimeVector---SIH\Test Audio"

def mp3_to_pcm_base64(path, sr=16000):
    import librosa
    y, _ = librosa.load(path, sr=sr, mono=True)
    pcm = (y * 32767).astype(np.int16)
    return base64.b64encode(pcm.tobytes()).decode("ascii"), len(pcm)

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

files = [
    ("test script 1.mp3", "AI-Generated Voice"),
    ("Scam Alert-1_ Fake Police Officer Tried to Extort 70,000 on WhatsApp! (Full Recorded Call).mp3", "Real Scam Call"),
]

print("=" * 60)
print("  AUDIO FILE PIPELINE TEST")
print("=" * 60)

for fname, label in files:
    path = os.path.join(AUDIO_DIR, fname)
    print(f"\n--- [{label}] {fname[:50]} ---")

    if not os.path.exists(path):
        print(f"  FILE NOT FOUND")
        continue

    print(f"  Loading MP3...")
    audio_b64, n_samples = mp3_to_pcm_base64(path)
    duration = n_samples / 16000
    print(f"  Duration: {duration:.1f}s")

    # Trim to 30s
    max_s = 30 * 16000
    if n_samples > max_s:
        raw = base64.b64decode(audio_b64)[:max_s * 2]
        audio_b64 = base64.b64encode(raw).decode("ascii")
        print(f"  Trimmed to 30s")

    payload = {
        "session_id": f"audio-{label.lower().replace(' ', '-')}",
        "tenant_id": "qa", "subject_id": "qa-audio",
        "audio_pcm_base64": audio_b64, "sample_rate_hz": 16000,
        "channels": 1, "context_score": 0.3, "transcript": "",
    }

    print(f"  Calling pipeline...")
    t0 = time.monotonic()
    result, status = post(f"{ORCHESTRATOR}/v1/pipeline/process", payload)
    elapsed = time.monotonic() - t0

    if "error" in result:
        print(f"  ERROR ({status}): {str(result['error'])[:200]}")
        continue

    cr = result.get("content_risk_signal") or {}
    sy = result.get("synthesis_signal") or {}
    print(f"  Latency       : {elapsed:.1f}s")
    print(f"  Synth Score   : {sy.get('score', '?')}")
    print(f"  Synth Detail  : {str(sy.get('detail', ''))[:80]}")
    print(f"  Content Risk  : {cr.get('score', '?')}")
    print(f"  Risk Detail   : {str(cr.get('detail', ''))[:80]}")
    print(f"  Fused Score   : {result.get('fused_risk_score', '?')}")
    print(f"  Final Action  : {result.get('final_action', '?')}")

print(f"\n{'=' * 60}")
print("  DONE")
