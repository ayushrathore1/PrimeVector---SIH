import React, { useState } from 'react';
import { FileCode, Terminal, Layers, Check, Copy } from 'lucide-react';
import CodeBlock from '../components/CodeBlock';

export default function ApiDocsPage() {
  const [activeSdkTab, setActiveSdkTab] = useState('python');

  const pythonSdkCode = `from voiceintegrity import (
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
    print(f"API returned error {e.status_code}: {e.message}. Holding transfer.")`;

  const nodeSdkCode = `import {
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

    console.log(\`Risk Score: \${response.risk_score.toFixed(2)} (Confidence: \${response.confidence.toFixed(2)})\`);
    console.log(\`Explanation: \${response.explanation}\`);

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
      console.error(\`Service unavailable: \${error.message}. Defaulting to fail-safe manual review.\`);
    } else if (error instanceof APIError) {
      console.error(\`API returned error \${error.statusCode}: \${error.message}. Holding transfer.\`);
    }
  }
}

verifyAndReleaseFundTransfer();`;

  const pipelineProcessRequestJson = `{
  "session_id": "call-sess-987654",
  "tenant_id": "bank-retail-prod",
  "subject_id": "cfo-john-doe",
  "audio_pcm_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=",
  "sample_rate_hz": 16000,
  "channels": 1,
  "transcript": "Transfer $50,000 immediately to overseas account 449112",
  "context_score": 0.65
}`;

  const pipelineProcessResponseJson = `{
  "session_id": "call-sess-987654",
  "tenant_id": "bank-retail-prod",
  "degraded": false,
  "synthesis_signal": {
    "score": 0.85,
    "confidence": 0.92,
    "available": true,
    "detail": "Acoustic spectral synthesis glitch detected"
  },
  "speaker_match_signal": {
    "score": 0.78,
    "confidence": 0.88,
    "available": true,
    "detail": "Embedding cosine mismatch against baseline"
  },
  "content_risk_signal": {
    "score": 0.90,
    "confidence": 0.95,
    "available": true,
    "detail": "Ollama LLM urgency & high-value transfer flag"
  },
  "risk_assessment": {
    "risk_score": 0.92,
    "confidence": 0.91,
    "degraded": false,
    "actions": ["RECOMMEND_SUPERVISOR_ESCALATION", "RECOMMEND_CALLBACK_VERIFICATION"],
    "explanation": "Noisy-OR fused acoustic + content score 0.92 exceeds 0.70 threshold."
  },
  "final_action": "RECOMMEND_SUPERVISOR_ESCALATION",
  "explanation": "High synthetic risk detected with voice mismatch and urgent transfer context."
}`;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">
      {/* Header */}
      <div className="pb-6 border-b border-obsidian-700">
        <div className="flex items-center gap-2">
          <FileCode className="w-6 h-6 text-forensic-amber" />
          <h1 className="font-serif text-3xl font-bold text-white">REST API & SDK Documentation</h1>
        </div>
        <p className="text-xs font-mono text-slate-400 mt-1">
          Complete endpoint references, JSON schemas, and official Python/Node SDK code snippets
        </p>
      </div>

      {/* Section 1: SDK Code Examples */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-serif text-2xl font-bold text-white">Official Client SDKs</h2>
          <div className="flex items-center gap-2 bg-obsidian-900 p-1 rounded-lg border border-obsidian-700 font-mono text-xs">
            <button
              onClick={() => setActiveSdkTab('python')}
              className={`px-3 py-1.5 rounded ${activeSdkTab === 'python'
                  ? 'bg-forensic-amber text-obsidian-950 font-bold'
                  : 'text-slate-400 hover:text-white'
                }`}
            >
              Python (voiceintegrity)
            </button>
            <button
              onClick={() => setActiveSdkTab('node')}
              className={`px-3 py-1.5 rounded ${activeSdkTab === 'node'
                  ? 'bg-forensic-amber text-obsidian-950 font-bold'
                  : 'text-slate-400 hover:text-white'
                }`}
            >
              Node.js (@voiceintegrity/sdk)
            </button>
          </div>
        </div>

        {activeSdkTab === 'python' ? (
          <CodeBlock
            code={pythonSdkCode}
            language="python"
            title="python / voiceintegrity SDK usage example"
          />
        ) : (
          <CodeBlock
            code={nodeSdkCode}
            language="typescript"
            title="Node.js / @voiceintegrity/sdk usage example"
          />
        )}
      </section>

      {/* Section 2: Core Endpoint Reference */}
      <section className="space-y-6">
        <h2 className="font-serif text-2xl font-bold text-white">Pipeline Endpoint Specifications</h2>

        <div className="rounded-xl border border-obsidian-700 bg-obsidian-900 p-6 shadow-card-glow space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-obsidian-800">
            <div className="flex items-center gap-3">
              <span className="px-2.5 py-1 rounded bg-amber-500/20 text-amber-400 border border-amber-500/40 font-mono text-xs font-bold">
                POST
              </span>
              <code className="font-mono text-sm text-white font-bold">/v1/pipeline/process</code>
            </div>
            <span className="text-xs font-mono text-slate-400">Target: Orchestrator (:8080)</span>
          </div>

          <p className="text-xs text-slate-300 font-sans leading-relaxed">
            Main pipeline endpoint. Receives transient PCM audio base64, sample rate, optional transcript, and caller context score. Triggers feature extraction, parallel signal evaluation, Noisy-OR fusion, policy checking, and alert dispatching.
          </p>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h4 className="font-mono text-xs font-semibold text-slate-300 mb-2 uppercase">Request Payload (JSON)</h4>
              <CodeBlock code={pipelineProcessRequestJson} language="json" title="Request Body" />
            </div>

            <div>
              <h4 className="font-mono text-xs font-semibold text-slate-300 mb-2 uppercase">Response Payload (JSON)</h4>
              <CodeBlock code={pipelineProcessResponseJson} language="json" title="Response Body" />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
