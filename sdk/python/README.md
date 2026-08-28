# Voice Integrity Python SDK (`voiceintegrity.v1`)

Thin client SDK for the Voice Integrity & Impersonation Prevention platform (`voiceintegrity.v1`), generated from `proto/risk_assessment.proto`.

- Direct 1:1 mapping to protocol definitions.
- No hidden retries. Failures bubble up immediately for integrator-managed retry/fallback strategies.
- API Key header authentication (`X-API-Key`).

## Installation

```bash
pip install voiceintegrity
```

## Integration Example

### Synchronous Risk Check Before Releasing a Fund Transfer

```python
from voiceintegrity import (
    VoiceIntegrityClient,
    RiskAssessmentRequest,
    RiskSignal,
    EnrollmentStatus,
    RecommendedAction,
    APIError,
    ConnectionError,
)

# 1. Initialize client with base URL and API key
client = VoiceIntegrityClient(
    base_url="https://api.voiceintegrity.bank.internal",
    api_key="sec_key_live_12345",
    timeout=2.0,
)

# 2. Construct the assessment request from live call & transaction signals
request = RiskAssessmentRequest(
    call_session_id="call-sess-987654",
    tenant_id="bank-retail-prod",
    synthesis_signal=RiskSignal(
        score=0.85,
        confidence=0.92,
        available=True,
        detail="Acoustic synthesis artifacts detected in high-frequency band",
    ),
    speaker_match_signal=RiskSignal(
        score=0.78,
        confidence=0.88,
        available=True,
        detail="Voice embedding vector mismatch against enrolled CFO baseline",
    ),
    contextual_signal=RiskSignal(
        score=0.60,
        confidence=1.0,
        available=True,
        detail="High-value wire transfer request ($250,000) to new overseas beneficiary",
    ),
    enrollment_status=EnrollmentStatus.ENROLLED,
)

# 3. Call Assess and branch on recommended actions
try:
    response = client.assess(request)

    print(f"Risk Score: {response.risk_score:.2f} (Confidence: {response.confidence:.2f})")
    print(f"Explanation: {response.explanation}")

    if RecommendedAction.BLOCK_PENDING_VERIFICATION in response.actions:
        print("ACTION: Transaction blocked pending manual fraud investigation.")
    elif RecommendedAction.RECOMMEND_SUPERVISOR_ESCALATION in response.actions:
        print("ACTION: Transaction held; escalating to fraud supervisor.")
    elif RecommendedAction.RECOMMEND_CALLBACK_VERIFICATION in response.actions:
        print("ACTION: Halting transfer. Initiating out-of-band callback to account owner.")
    elif RecommendedAction.RECOMMEND_MFA_STEP_UP in response.actions:
        print("ACTION: Prompting user for biometric MFA verification.")
    elif RecommendedAction.PROCEED in response.actions:
        print("ACTION: Integrity verified. Releasing fund transfer.")

except ConnectionError as e:
    # Fail safe: do not release funds if verification service cannot be reached
    print(f"Service unavailable: {e}. Defaulting to fail-safe manual review.")
except APIError as e:
    print(f"API returned error {e.status_code}: {e.message}. Holding transfer.")
```
