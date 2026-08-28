# Voice Integrity Node.js SDK (`@voiceintegrity/sdk`)

Thin client SDK for the Voice Integrity & Impersonation Prevention platform (`voiceintegrity.v1`), generated from `proto/risk_assessment.proto`.

- Direct 1:1 mapping to protocol definitions.
- No hidden retries. Failures bubble up immediately for integrator-managed retry/fallback strategies.
- API Key header authentication (`X-API-Key`).

## Installation

```bash
npm install @voiceintegrity/sdk
```

## Integration Example

### Synchronous Risk Check Before Releasing a Fund Transfer

```typescript
import {
  VoiceIntegrityClient,
  RiskAssessmentRequest,
  EnrollmentStatus,
  RecommendedAction,
  APIError,
  ConnectionError,
} from "@voiceintegrity/sdk";

// 1. Initialize client with base URL and API key
const client = new VoiceIntegrityClient({
  baseUrl: "https://api.voiceintegrity.bank.internal",
  apiKey: "sec_key_live_12345",
  timeoutMs: 2000,
});

// 2. Construct the assessment request from live call & transaction signals
const request: RiskAssessmentRequest = {
  call_session_id: "call-sess-987654",
  tenant_id: "bank-retail-prod",
  synthesis_signal: {
    score: 0.85,
    confidence: 0.92,
    available: true,
    detail: "Acoustic synthesis artifacts detected in high-frequency band",
  },
  speaker_match_signal: {
    score: 0.78,
    confidence: 0.88,
    available: true,
    detail: "Voice embedding vector mismatch against enrolled CFO baseline",
  },
  contextual_signal: {
    score: 0.60,
    confidence: 1.0,
    available: true,
    detail: "High-value wire transfer request ($250,000) to new overseas beneficiary",
  },
  enrollment_status: EnrollmentStatus.ENROLLED,
};

// 3. Call Assess and branch on recommended actions
async function verifyAndReleaseFundTransfer() {
  try {
    const response = await client.assess(request);

    console.log(`Risk Score: ${response.risk_score.toFixed(2)} (Confidence: ${response.confidence.toFixed(2)})`);
    console.log(`Explanation: ${response.explanation}`);

    if (response.actions.includes(RecommendedAction.BLOCK_PENDING_VERIFICATION)) {
      console.log("ACTION: Transaction blocked pending manual fraud investigation.");
    } else if (response.actions.includes(RecommendedAction.RECOMMEND_SUPERVISOR_ESCALATION)) {
      console.log("ACTION: Transaction held; escalating to fraud supervisor.");
    } else if (response.actions.includes(RecommendedAction.RECOMMEND_CALLBACK_VERIFICATION)) {
      console.log("ACTION: Halting transfer. Initiating out-of-band callback to account owner.");
    } else if (response.actions.includes(RecommendedAction.RECOMMEND_MFA_STEP_UP)) {
      console.log("ACTION: Prompting user for biometric MFA verification.");
    } else if (response.actions.includes(RecommendedAction.PROCEED)) {
      console.log("ACTION: Integrity verified. Releasing fund transfer.");
    }
  } catch (error) {
    if (error instanceof ConnectionError) {
      // Fail safe: do not release funds if verification service cannot be reached
      console.error(`Service unavailable: ${error.message}. Defaulting to fail-safe manual review.`);
    } else if (error instanceof APIError) {
      console.error(`API returned error ${error.statusCode}: ${error.message}. Holding transfer.`);
    } else {
      console.error("Unexpected error during assessment:", error);
    }
  }
}

verifyAndReleaseFundTransfer();
```
