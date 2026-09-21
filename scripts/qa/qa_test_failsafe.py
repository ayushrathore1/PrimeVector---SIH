"""Test 2.7: Fail-safe behavior under dependency outage."""
import base64, json, math, struct, urllib.request, urllib.error

def make_sine_pcm_base64(freq_hz, duration_s=1.0, sample_rate=16000):
    n_samples = int(sample_rate * duration_s)
    samples = [int(32767 * 0.8 * math.sin(2 * math.pi * freq_hz * i / sample_rate)) for i in range(n_samples)]
    return base64.b64encode(struct.pack(f"<{len(samples)}h", *samples)).decode("ascii")

def post_json(url, data, timeout=30):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode("utf-8")), resp.status
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode("utf-8"), "status_code": e.code}, e.code

audio = make_sine_pcm_base64(440.0, duration_s=1.0)
payload = {
    "session_id": "qa-failsafe-002",
    "tenant_id": "qa-tenant",
    "subject_id": "qa-subject-001",
    "audio_pcm_base64": audio,
    "sample_rate_hz": 16000,
    "channels": 1,
    "context_score": 0.3,
    "transcript": "Please transfer money now"
}

print("=== TEST 2.7: Fail-safe with spoof-detection-service DOWN ===")
print(f"Sending pipeline request with real audio (spoof-detection-service is stopped)...")
resp, status = post_json("http://localhost:8080/v1/pipeline/process", payload, timeout=60)
print(f"\nHTTP Status: {status}")
print(f"degraded: {resp.get('degraded')}")
print(f"final_action: {resp.get('final_action')}")
print(f"explanation: {resp.get('explanation')}")

synthesis = resp.get('synthesis_signal')
print(f"\nsynthesis_signal: {json.dumps(synthesis, indent=2) if synthesis else 'None'}")

risk = resp.get('risk_assessment')
if risk:
    print(f"\nrisk_assessment.risk_score: {risk.get('risk_score')}")
    print(f"risk_assessment.degraded: {risk.get('degraded')}")
    print(f"risk_assessment.actions: {risk.get('actions')}")
    print(f"risk_assessment.explanation: {risk.get('explanation')}")
else:
    print(f"\nrisk_assessment: None")

print(f"\n=== VERDICT ===")
if resp.get('degraded') == True and resp.get('final_action') == 'RECOMMEND_CALLBACK_VERIFICATION':
    print("PASS: Pipeline returned degraded=true with RECOMMEND_CALLBACK_VERIFICATION")
elif resp.get('degraded') == True:
    print(f"PARTIAL PASS: degraded=true but final_action={resp.get('final_action')}")
elif resp.get('degraded') == False and resp.get('risk_assessment', {}).get('risk_score', 1.0) < 0.3:
    print("CRITICAL FAIL: Pipeline returned non-degraded LOW risk with service down — FAIL OPEN!")
else:
    print(f"CHECK: degraded={resp.get('degraded')}, final_action={resp.get('final_action')}")
