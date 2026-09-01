"""
Re-test content risk after Groq model fix.
Tests: scam transcript vs benign transcript via full pipeline.
"""
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

print("=" * 70)
print("  CONTENT RISK RE-TEST (after Groq model fix)")
print("=" * 70)

# Test 1: Scam transcript
scam_payload = {
    "session_id": "retest-scam-001",
    "tenant_id": "qa-tenant",
    "subject_id": "qa-subject-001",
    "audio_pcm_base64": audio,
    "sample_rate_hz": 16000,
    "channels": 1,
    "context_score": 0.3,
    "transcript": "Please transfer 50000 rupees immediately to this account and share the OTP you just received on your phone. This is urgent, the RBI has flagged your account."
}
print("\n[1] SCAM transcript:")
print(f'    "{scam_payload["transcript"]}"')
resp_scam, status_scam = post_json("http://localhost:8080/v1/pipeline/process", scam_payload, timeout=60)
cr_scam = resp_scam.get("content_risk_signal", {})
print(f"\n    HTTP Status: {status_scam}")
print(f"    content_risk_signal:")
print(f"      score:      {cr_scam.get('score', 'N/A')}")
print(f"      confidence: {cr_scam.get('confidence', 'N/A')}")
print(f"      available:  {cr_scam.get('available', 'N/A')}")
print(f"      detail:     {cr_scam.get('detail', 'N/A')}")
print(f"    risk_score:    {resp_scam.get('risk_assessment', {}).get('risk_score', 'N/A')}")
print(f"    final_action:  {resp_scam.get('final_action', 'N/A')}")
print(f"    explanation:   {resp_scam.get('explanation', 'N/A')}")

# Test 2: Benign transcript
benign_payload = {
    "session_id": "retest-benign-001",
    "tenant_id": "qa-tenant",
    "subject_id": "qa-subject-001",
    "audio_pcm_base64": audio,
    "sample_rate_hz": 16000,
    "channels": 1,
    "context_score": 0.1,
    "transcript": "Are we still meeting for lunch tomorrow at the usual place? I was thinking we could try the new restaurant."
}
print(f'\n[2] BENIGN transcript:')
print(f'    "{benign_payload["transcript"]}"')
resp_benign, status_benign = post_json("http://localhost:8080/v1/pipeline/process", benign_payload, timeout=60)
cr_benign = resp_benign.get("content_risk_signal", {})
print(f"\n    HTTP Status: {status_benign}")
print(f"    content_risk_signal:")
print(f"      score:      {cr_benign.get('score', 'N/A')}")
print(f"      confidence: {cr_benign.get('confidence', 'N/A')}")
print(f"      available:  {cr_benign.get('available', 'N/A')}")
print(f"      detail:     {cr_benign.get('detail', 'N/A')}")
print(f"    risk_score:    {resp_benign.get('risk_assessment', {}).get('risk_score', 'N/A')}")
print(f"    final_action:  {resp_benign.get('final_action', 'N/A')}")

# Verdict
print("\n" + "=" * 70)
print("  VERDICT")
print("=" * 70)

scam_avail = cr_scam.get("available", False)
benign_avail = cr_benign.get("available", False)

if not scam_avail and not benign_avail:
    detail = cr_scam.get("detail", "")
    if "404" in detail:
        print("  STILL BROKEN: Groq still returning 404. Model may need different name.")
    else:
        print(f"  STILL BROKEN: content_risk available=false. Detail: {detail}")
elif scam_avail and benign_avail:
    scam_score = cr_scam.get("score", 0)
    benign_score = cr_benign.get("score", 0)
    print(f"  Content risk scores: scam={scam_score:.3f}, benign={benign_score:.3f}")
    if scam_score > benign_score + 0.2:
        print(f"  PASS: Scam score ({scam_score:.3f}) significantly higher than benign ({benign_score:.3f})")
        print("  Content risk is WORKING and discriminating!")
    elif scam_score > benign_score:
        print(f"  PARTIAL: Scam ({scam_score:.3f}) > benign ({benign_score:.3f}) but margin is small")
    else:
        print(f"  CONCERN: Scam ({scam_score:.3f}) NOT higher than benign ({benign_score:.3f})")
else:
    print(f"  MIXED: scam available={scam_avail}, benign available={benign_avail}")
