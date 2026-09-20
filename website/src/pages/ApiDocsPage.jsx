import React, { useState } from 'react';
import { Shield, Server, Lock, Cpu, Layers, Terminal, Copy, Check, Sparkles, Building2, PhoneCall, Radio, Download, Key, Activity, CheckCircle2, FileText } from 'lucide-react';
import CodeBlock from '../components/CodeBlock';

export default function ApiDocsPage() {
  const [activeSdkTab, setActiveSdkTab] = useState('python');
  const [activeOrgTab, setActiveOrgTab] = useState('banking');
  const [copiedEndpoint, setCopiedEndpoint] = useState(null);

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedEndpoint(id);
    setTimeout(() => setCopiedEndpoint(null), 2000);
  };

  const pythonSdkCode = `import base64
from satyadhvani import SatyaDhvaniClient

# Initialize Enterprise SatyaDhVani Client
# Point endpoint to your deployed gateway host (e.g. http://localhost:8085 or internal VPC gateway)
client = SatyaDhvaniClient(
    api_key="sdv_live_enterprise_org_key",
    endpoint="http://localhost:8085"
)

# 1. Direct Acoustic Deepfake Classifier (DhVani Engine)
with open("incoming_telephony_chunk.wav", "rb") as f:
    audio_pcm_base64 = base64.b64encode(f.read()).decode()

detection = client.detect_spoof(
    audio_pcm_base64=audio_pcm_base64,
    sample_rate=16000
)

print(f"Verdict:        {detection.verdict}")        # 'real' (Satya) or 'fake' (ASatya)
print(f"Spoof Score:    {detection.spoof_score:.4f}") # 0.0 (Bonafide) -> 1.0 (AI Deepfake)
print(f"Confidence:     {detection.confidence:.2%}")
print(f"Inference Time: {detection.latency_ms}ms")

# 2. Complete 4-Vector End-to-End Orchestrated Verification Pipeline
pipeline_response = client.process_pipeline(
    session_id="call-sess-994102",
    tenant_id="bank-retail-prod",
    subject_id="cfo-john-doe",
    transcript="Urgent wire transfer of $150,000 to overseas account required immediately.",
    context_score=0.85,
    audio_pcm_base64=audio_pcm_base64
)

print(f"Fused Risk Score: {pipeline_response.risk_assessment.risk_score:.4f}")
print(f"Policy Action:    {pipeline_response.final_action}") # e.g. "RECOMMEND_CALLBACK_VERIFICATION"
print(f"Explanation:      {pipeline_response.explanation}")`;

  const nodeSdkCode = `import { SatyaDhvaniClient } from '@satyadhvani/sdk';
import * as fs from 'fs';

// Initialize Enterprise SatyaDhVani Client
// Point endpoint to your deployed gateway host (e.g. http://localhost:8085 or internal VPC gateway)
const client = new SatyaDhvaniClient({
  apiKey: 'sdv_live_enterprise_org_key',
  endpoint: 'http://localhost:8085'
});

// Read incoming call audio payload
const audioBuffer = fs.readFileSync('incoming_telephony_chunk.wav');
const audioBase64 = audioBuffer.toString('base64');

// Execute end-to-end multi-vector verification pipeline
const result = await client.processPipeline({
  sessionId: \`call-sess-\${Date.now()}\`,
  tenantId: 'bank-retail-prod',
  subjectId: 'user-mary-smith',
  transcript: 'I lost my debit card password and need a quick reset while traveling.',
  contextScore: 0.45,
  audioPcmBase64: audioBase64
});

console.log(\`Fused Risk Score: \${result.riskAssessment.riskScore}\`);
console.log(\`Final Policy Action: \${result.finalAction}\`);
console.log(\`Explanation: \${result.explanation}\`);`;

  const curlCode = `curl -X POST "http://localhost:8085/v1/pipeline/process" \\
  -H "X-API-Key: sdv_live_enterprise_org_key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "session_id": "call-sess-884102",
    "tenant_id": "enterprise-corp-prod",
    "subject_id": "vip-director-smith",
    "transcript": "Transfer $50,000 to new vendor account 4410-9912 immediately.",
    "context_score": 0.82,
    "sample_rate_hz": 16000,
    "channels": 1,
    "audio_pcm_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="
  }'`;

  return (
    <div className="min-h-screen bg-white text-forest selection:bg-lemongrass py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        
        {/* Executive Header Banner */}
        <div className="space-y-6 pb-10 border-b border-forest/10">
          <div className="inline-flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-forest bg-sage-1 px-4 py-1.5 rounded-full border border-forest/15">
            <Shield size={14} className="text-forest" />
            <span>Enterprise Voice Security & Anti-Impersonation Framework Reference Specification</span>
          </div>
          
          <h1 className="font-display text-4xl sm:text-6xl font-extrabold text-forest tracking-tight">
            SatyaDhVani Enterprise Integration Architecture
          </h1>
          
          <p className="text-base sm:text-lg text-forest/80 max-w-5xl leading-relaxed font-sans">
            SatyaDhVani is an enterprise-grade, real-time voice integrity verification and deepfake detection platform. Built for deployment across financial institutions, telecommunication networks, contact center environments, and high-assurance government infrastructures, SatyaDhVani defends voice communication channels against AI-generated voice cloning, neural TTS deepfakes, and social engineering fraud.
          </p>

          {/* Platform Identity & Nomenclature Breakdown */}
          <div className="bg-sage-1 border border-forest/15 rounded-2xl p-8 shadow-spade spade-cut-md space-y-6 mt-8">
            <div className="flex items-center gap-3 border-b border-forest/10 pb-4">
              <Sparkles className="text-forest" size={24} />
              <h3 className="font-display text-xl font-bold text-forest">Platform Identity & Architectural Nomenclature</h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="space-y-2">
                <div className="text-xs font-mono font-bold text-forest/60 uppercase tracking-wider">1. Vaani (Acoustic Corpus)</div>
                <div className="font-display text-lg font-extrabold text-forest">IISc Vaani Acoustic Model</div>
                <p className="text-xs text-forest/80 leading-relaxed font-sans">
                  Trained on the Indian Institute of Science (IISc) Bangalore <strong>Vaani dataset</strong>, incorporating 100+ Indian regional languages, accents, dialects, and diverse acoustic background conditions for high multi-accent generalization.
                </p>
              </div>

              <div className="space-y-2 border-t md:border-t-0 md:border-l border-forest/10 pt-4 md:pt-0 md:pl-8">
                <div className="text-xs font-mono font-bold text-forest/60 uppercase tracking-wider">2. DhVani (Audio Waveform Classifier)</div>
                <div className="font-display text-lg font-extrabold text-forest">DhVani Neural Engine</div>
                <p className="text-xs text-forest/80 leading-relaxed font-sans">
                  Deep neural architecture (ResNet-18 + Squeeze-and-Excitation + BiGRU + 8-Head Attention) evaluating audio sound waves (DhVani) across 3-channel spectrograms (Log-Mel, Delta velocity, Delta-Delta acceleration) to detect spectral phase stiffness and micro-jitter anomalies.
                </p>
              </div>

              <div className="space-y-2 border-t md:border-t-0 md:border-l border-forest/10 pt-4 md:pt-0 md:pl-8">
                <div className="text-xs font-mono font-bold text-emerald-800 uppercase tracking-wider">3. Satya (Truth Integrity Verification)</div>
                <div className="font-display text-lg font-extrabold text-emerald-950">Satya Deterministic Scoring</div>
                <p className="text-xs text-forest/80 leading-relaxed font-sans">
                  Computes a deterministic, non-random risk assessment certifying whether an inbound call audio stream is <strong>Satya (Genuine Human Voice)</strong> or <strong>ASatya (AI Deepfake / Cloned Audio)</strong>.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Global SDK Packaging & Enterprise Distribution */}
        <section className="bg-white border border-forest/10 rounded-2xl p-8 shadow-spade spade-cut-md space-y-6">
          <div className="flex items-center justify-between border-b border-forest/10 pb-4">
            <div className="flex items-center gap-3 text-forest font-display text-2xl font-bold">
              <Download className="text-forest" size={26} />
              <h2>Enterprise Software Development Kits (SDKs)</h2>
            </div>
            <span className="text-xs font-mono font-bold bg-sage-1 text-forest px-3 py-1 rounded border border-forest/10">v0.2.0 Distribution</span>
          </div>

          <p className="text-sm text-forest/80 leading-relaxed">
            SatyaDhVani provides officially maintained, production-ready SDKs for Python and Node.js/TypeScript environments. Packages are distributed via standard package managers and private enterprise registries.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-2">
            <div className="bg-sage-1 rounded-xl p-6 border border-forest/15 space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm font-bold text-forest uppercase">Python Enterprise SDK</span>
                <span className="text-[11px] font-mono bg-emerald-100 text-emerald-900 px-2.5 py-0.5 rounded font-bold">satyadhvani 0.2.0</span>
              </div>
              <CodeBlock code={`pip install satyadhvani`} language="bash" title="Pip Package Installation" />
              <div className="text-xs text-forest/70 font-mono space-y-1">
                <div>• Wheel Artifact: <code className="bg-white px-1.5 py-0.5 rounded border border-forest/10 font-bold">satyadhvani-0.2.0-py3-none-any.whl</code></div>
                <div>• Direct Repo Install: <code className="bg-white px-1.5 py-0.5 rounded border border-forest/10">pip install git+https://github.com/...#subdirectory=sdk/python</code></div>
              </div>
            </div>

            <div className="bg-sage-1 rounded-xl p-6 border border-forest/15 space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm font-bold text-forest uppercase">Node.js / TypeScript SDK</span>
                <span className="text-[11px] font-mono bg-emerald-100 text-emerald-900 px-2.5 py-0.5 rounded font-bold">@satyadhvani/sdk 0.2.0</span>
              </div>
              <CodeBlock code={`npm install @satyadhvani/sdk`} language="bash" title="npm Package Installation" />
              <div className="text-xs text-forest/70 font-mono space-y-1">
                <div>• Tarball Artifact: <code className="bg-white px-1.5 py-0.5 rounded border border-forest/10 font-bold">satyadhvani-sdk-0.2.0.tgz</code></div>
                <div>• Enterprise Registry: <code className="bg-white px-1.5 py-0.5 rounded border border-forest/10">npm publish --registry=https://npm.pkg.github.com</code></div>
              </div>
            </div>
          </div>
        </section>

        {/* SDK Integration Quickstart Code */}
        <section className="space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h2 className="font-display text-2xl font-bold text-forest">SDK Implementation Reference</h2>
              <p className="text-xs font-mono text-forest/60">Sample client initialization and pipeline execution patterns</p>
            </div>
            <div className="flex items-center gap-2 bg-sage-1 p-1 rounded-lg border border-forest/10 font-mono text-xs">
              <button
                onClick={() => setActiveSdkTab('python')}
                className={`px-4 py-2 rounded-md font-bold transition-all cursor-pointer ${
                  activeSdkTab === 'python' ? 'bg-forest text-lemongrass shadow-sm' : 'text-forest/70 hover:text-forest'
                }`}
              >
                Python SDK
              </button>
              <button
                onClick={() => setActiveSdkTab('node')}
                className={`px-4 py-2 rounded-md font-bold transition-all cursor-pointer ${
                  activeSdkTab === 'node' ? 'bg-forest text-lemongrass shadow-sm' : 'text-forest/70 hover:text-forest'
                }`}
              >
                Node.js SDK
              </button>
              <button
                onClick={() => setActiveSdkTab('curl')}
                className={`px-4 py-2 rounded-md font-bold transition-all cursor-pointer ${
                  activeSdkTab === 'curl' ? 'bg-forest text-lemongrass shadow-sm' : 'text-forest/70 hover:text-forest'
                }`}
              >
                cURL / REST
              </button>
            </div>
          </div>

          <CodeBlock
            code={activeSdkTab === 'python' ? pythonSdkCode : activeSdkTab === 'node' ? nodeSdkCode : curlCode}
            language={activeSdkTab === 'python' ? 'python' : activeSdkTab === 'node' ? 'javascript' : 'bash'}
            title={activeSdkTab === 'python' ? 'Python — SatyaDhVani Enterprise Client' : activeSdkTab === 'node' ? 'Node.js — SatyaDhVani Enterprise Client' : 'cURL REST API Integration'}
          />
        </section>

        {/* Industry-Specific Technical Integration Manuals */}
        <section className="space-y-6">
          <div className="space-y-2">
            <h2 className="font-display text-3xl font-extrabold text-forest">
              Enterprise & Sector-Specific Integration Blueprint
            </h2>
            <p className="text-sm text-forest/70">
              Architectural specifications, threat models, and policy enforcement workflows tailored by organizational vertical.
            </p>
          </div>

          {/* Vertical Selector Buttons */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs font-bold">
            <button
              onClick={() => setActiveOrgTab('banking')}
              className={`p-5 rounded-2xl border transition-all text-left flex items-start gap-3.5 cursor-pointer ${
                activeOrgTab === 'banking'
                  ? 'bg-forest text-lemongrass border-forest shadow-spade'
                  : 'bg-sage-1 text-forest border-forest/15 hover:border-forest/40'
              }`}
            >
              <Building2 size={24} className="shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-bold">Banking & Finance</div>
                <div className="text-[11px] font-normal opacity-80 mt-0.5">Core Banking (CBS), Wire Transfers, IVR Fraud</div>
              </div>
            </button>

            <button
              onClick={() => setActiveOrgTab('contact_center')}
              className={`p-5 rounded-2xl border transition-all text-left flex items-start gap-3.5 cursor-pointer ${
                activeOrgTab === 'contact_center'
                  ? 'bg-forest text-lemongrass border-forest shadow-spade'
                  : 'bg-sage-1 text-forest border-forest/15 hover:border-forest/40'
              }`}
            >
              <PhoneCall size={24} className="shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-bold">Contact Centers</div>
                <div className="text-[11px] font-normal opacity-80 mt-0.5">Genesys, Avaya, Cisco, Live Agent Widget</div>
              </div>
            </button>

            <button
              onClick={() => setActiveOrgTab('telecom')}
              className={`p-5 rounded-2xl border transition-all text-left flex items-start gap-3.5 cursor-pointer ${
                activeOrgTab === 'telecom'
                  ? 'bg-forest text-lemongrass border-forest shadow-spade'
                  : 'bg-sage-1 text-forest border-forest/15 hover:border-forest/40'
              }`}
            >
              <Radio size={24} className="shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-bold">Telecom Carriers</div>
                <div className="text-[11px] font-normal opacity-80 mt-0.5">Session Border Controller (SBC) Media Forking</div>
              </div>
            </button>

            <button
              onClick={() => setActiveOrgTab('government')}
              className={`p-5 rounded-2xl border transition-all text-left flex items-start gap-3.5 cursor-pointer ${
                activeOrgTab === 'government'
                  ? 'bg-forest text-lemongrass border-forest shadow-spade'
                  : 'bg-sage-1 text-forest border-forest/15 hover:border-forest/40'
              }`}
            >
              <Shield size={24} className="shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-bold">Government & Defense</div>
                <div className="text-[11px] font-normal opacity-80 mt-0.5">Air-Gapped K8s, Emergency Dispatch (112)</div>
              </div>
            </button>
          </div>

          {/* Detailed Vertical Specification Content Box */}
          <div className="bg-white border border-forest/10 rounded-2xl p-8 sm:p-10 shadow-spade spade-cut-md space-y-8">
            {activeOrgTab === 'banking' && (
              <div className="space-y-6">
                <div className="flex items-center gap-3 text-forest font-display text-2xl font-bold pb-4 border-b border-forest/10">
                  <Building2 className="text-forest" size={30} />
                  <h3>Tier-1 Financial Institutions & Core Banking System (CBS) Specification</h3>
                </div>

                <div className="space-y-6 text-sm text-forest/80 leading-relaxed font-sans">
                  <div>
                    <h4 className="font-bold text-forest text-base font-display mb-2">1. Target Core Banking Environments</h4>
                    <p className="mb-2">SatyaDhVani provides high-throughput integration interceptors for major Core Banking Platforms:</p>
                    <ul className="list-disc pl-6 space-y-1.5 font-sans">
                      <li><strong>Infosys Finacle</strong>: Interceptor attached to transaction authorization hooks (<code className="bg-sage-1 px-1.5 py-0.5 rounded text-xs font-mono text-forest">FI_XFER_VERIFY</code>).</li>
                      <li><strong>Temenos T24 / Transact</strong>: Pre-commit hook on fund transfer APIs (<code className="bg-sage-1 px-1.5 py-0.5 rounded text-xs font-mono text-forest">FUNDS.TRANSFER,OOB.AUTHORISE</code>).</li>
                      <li><strong>TCS BaNCS & SAP Banking</strong>: Webhook middleware attached to payment execution services.</li>
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-bold text-forest text-base font-display mb-2">2. Transaction Risk Policy Workflow</h4>
                    <div className="bg-sage-1 p-5 rounded-xl border border-forest/15 space-y-3 font-mono text-xs">
                      <div className="font-bold text-forest text-sm">Automated Out-of-Band (OOB) Callback Policy Matrix</div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                        <div className="bg-white p-3 rounded border border-forest/10">
                          <div className="text-emerald-800 font-bold">Score &lt; 0.40</div>
                          <div className="font-bold text-forest mt-1">PROCEED</div>
                          <div className="text-[11px] text-forest/70 mt-1">Normal transaction flow. Automated IVR execution granted.</div>
                        </div>
                        <div className="bg-white p-3 rounded border border-forest/10">
                          <div className="text-amber-800 font-bold">0.40 &le; Score &lt; 0.70</div>
                          <div className="font-bold text-forest mt-1">FLAG_SUSPICIOUS</div>
                          <div className="text-[11px] text-forest/70 mt-1">Prompt secondary in-app biometric push notification or OTP.</div>
                        </div>
                        <div className="bg-white p-3 rounded border border-forest/10">
                          <div className="text-red-800 font-bold">Score &ge; 0.70</div>
                          <div className="font-bold text-forest mt-1">RECOMMEND_CALLBACK</div>
                          <div className="text-[11px] text-forest/70 mt-1">Transaction held. Automated out-of-band call to registered mobile.</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-bold text-forest text-base font-display mb-2">3. Regulatory & Defense-in-Depth Compliance</h4>
                    <div className="space-y-2 text-xs font-mono bg-sage-1/60 p-4 rounded-xl border border-forest/10">
                      <div>✔ <strong>Zero Raw Audio Retention Invariant</strong>: Raw audio PCM bytes exist exclusively in transient RAM during feature extraction and are unreferenced immediately. No voice recordings are written to disk or logs.</div>
                      <div>✔ <strong>Opt-In Auto-Block Gate</strong>: Defaults to <code className="bg-white px-1.5 py-0.5 rounded border border-forest/10 font-bold text-forest">auto_block_enabled = False</code> to comply with banking regulations against unnotified automated transaction drops.</div>
                      <div>✔ <strong>RBI Cybersecurity Framework Alignment</strong>: Full compliance with RBI guidelines on anti-impersonation controls for phone banking and IVR channels.</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeOrgTab === 'contact_center' && (
              <div className="space-y-6">
                <div className="flex items-center gap-3 text-forest font-display text-2xl font-bold pb-4 border-b border-forest/10">
                  <PhoneCall className="text-forest" size={30} />
                  <h3>Enterprise Contact Centers & Call Center Architecture</h3>
                </div>

                <div className="space-y-6 text-sm text-forest/80 leading-relaxed font-sans">
                  <div>
                    <h4 className="font-bold text-forest text-base font-display mb-2">1. Supported Call Center Platforms</h4>
                    <ul className="list-disc pl-6 space-y-1.5 font-sans">
                      <li><strong>Genesys Cloud CX & Genesys Engage</strong>: Native AudioHook WebSocket integration.</li>
                      <li><strong>Avaya Aura Communication Manager</strong>: Session Manager media duplication connector.</li>
                      <li><strong>Cisco Webex Contact Center / UCCE</strong>: MediaSense / CUBE SIP trunk tap.</li>
                      <li><strong>Twilio Programmable Voice & Amazon Connect</strong>: Kinesis Video Streams / Twilio Media Streams connector.</li>
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-bold text-forest text-base font-display mb-2">2. Agent Visual Verification Assist Widget</h4>
                    <p className="mb-3">
                      SatyaDhVani streams real-time risk telemetry to the frontline customer service agent desktop:
                    </p>
                    <div className="bg-sage-1 p-5 rounded-xl border border-forest/15 space-y-3 font-mono">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-forest">SatyaDhVani Real-Time Agent Assist</span>
                        <span className="text-emerald-800 font-bold">🟢 Latency: 38ms</span>
                      </div>
                      <div className="w-full bg-white h-3.5 rounded-full overflow-hidden border border-forest/15">
                        <div className="bg-emerald-600 h-full w-[14%]"></div>
                      </div>
                      <div className="flex flex-wrap justify-between text-[11px] text-forest/80 pt-1">
                        <span>Acoustic Score: 0.04 (Normal)</span>
                        <span>Voiceprint Match: 0.92 (Enrolled Match)</span>
                        <span className="font-bold text-emerald-900">Verdict: SATYA (Human Voice)</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeOrgTab === 'telecom' && (
              <div className="space-y-6">
                <div className="flex items-center gap-3 text-forest font-display text-2xl font-bold pb-4 border-b border-forest/10">
                  <Radio className="text-forest" size={30} />
                  <h3>Telecom Operator & Carrier Network Architecture</h3>
                </div>

                <div className="space-y-6 text-sm text-forest/80 leading-relaxed font-sans">
                  <div>
                    <h4 className="font-bold text-forest text-base font-display mb-2">1. Session Border Controller (SBC) Media Tapping</h4>
                    <p className="mb-2">
                      Telecom carriers integrate SatyaDhVani at the network edge using Session Border Controllers (AudioCodes, Ribbon Communications, Oracle SBC):
                    </p>
                    <ul className="list-disc pl-6 space-y-2 font-sans">
                      <li><strong>SIP/RTP Media Forking</strong>: Inbound call RTP packets are copied and streamed to the Go-based <strong>Ingestion Gateway</strong> (<code className="bg-sage-1 px-1.5 py-0.5 rounded text-xs font-mono text-forest font-bold">services/ingestion-gateway</code>) on UDP port 8006.</li>
                      <li><strong>Zero In-Band Latency</strong>: Tapping occurs out-of-band via RTP mirroring, introducing <strong>0ms added latency</strong> to the active caller voice path.</li>
                      <li><strong>SIP Telemetry Engine</strong>: Analyzes RTP sequence gaps, packet jitter, codec anomaly scores, and caller ID spoofing indicators.</li>
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-bold text-forest text-base font-display mb-2">2. Network-Wide Voice Fraud Prevention</h4>
                    <p>
                      Detects mass automated AI robocalls, synthetic voice spamming, and vishing campaigns across 5G VoNR and 4G VoLTE carrier networks prior to call termination.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {activeOrgTab === 'government' && (
              <div className="space-y-6">
                <div className="flex items-center gap-3 text-forest font-display text-2xl font-bold pb-4 border-b border-forest/10">
                  <Shield className="text-forest" size={30} />
                  <h3>Government, Defense & Public Safety Architecture</h3>
                </div>

                <div className="space-y-6 text-sm text-forest/80 leading-relaxed font-sans">
                  <div>
                    <h4 className="font-bold text-forest text-base font-display mb-2">1. On-Premise & Air-Gapped Deployment</h4>
                    <ul className="list-disc pl-6 space-y-2 font-sans">
                      <li><strong>100% Air-Gapped Kubernetes Cluster</strong>: Zero outbound internet dependencies required. All deep learning models operate locally.</li>
                      <li><strong>Hardware Acceleration</strong>: Optimized for local NVIDIA TensorRT GPUs and Intel OpenVINO CPU clusters.</li>
                      <li><strong>Public Safety Protection</strong>: Secures national emergency dispatch hotlines (112), citizen welfare verification desks, and high-assurance executive communications against AI deepfake impersonation.</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Complete API Specification Endpoint Details */}
        <section className="space-y-6">
          <h2 className="font-display text-3xl font-extrabold text-forest">
            Core API Endpoints Specification
          </h2>

          <div className="bg-white border border-forest/10 rounded-2xl p-8 space-y-6 shadow-spade spade-cut-md">
            <div className="flex items-center justify-between pb-4 border-b border-forest/10">
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 rounded text-xs font-mono font-extrabold bg-forest text-lemongrass">POST</span>
                <code className="font-mono text-base font-bold text-forest">/v1/pipeline/process</code>
              </div>
              <span className="text-xs font-mono font-bold bg-sage-1 text-forest px-3 py-1 rounded border border-forest/10">Orchestrator Core API</span>
            </div>

            <p className="text-sm text-forest/80 leading-relaxed font-sans">
              Main multi-vector orchestration endpoint. Executes parallel feature extraction, DhVani v2 deepfake acoustic classification, cross-session voiceprint matching, NLP vishing intent analysis, and deterministic risk fusion.
            </p>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
              <div>
                <h4 className="font-mono text-xs font-bold text-forest uppercase tracking-wider mb-2">Request Body (JSON)</h4>
                <CodeBlock
                  code={`{
  "session_id": "call-sess-994102",
  "tenant_id": "bank-retail-prod",
  "subject_id": "cfo-john-doe",
  "transcript": "Urgent transfer of $120,000 required to overseas account immediately.",
  "context_score": 0.85,
  "sample_rate_hz": 16000,
  "channels": 1,
  "audio_pcm_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="
}`}
                  language="json"
                  title="Request Payload Schema"
                />
              </div>

              <div>
                <h4 className="font-mono text-xs font-bold text-forest uppercase tracking-wider mb-2">Response Output (JSON)</h4>
                <CodeBlock
                  code={`{
  "session_id": "call-sess-994102",
  "tenant_id": "bank-retail-prod",
  "degraded": false,
  "synthesis_signal": {
    "score": 0.9412,
    "confidence": 0.9600,
    "available": true,
    "detail": "[DhVani v2] AI Voice Clone Detected (Neural Pitch Stiffness Jitter=0.104)"
  },
  "speaker_match_signal": {
    "score": 0.7200,
    "confidence": 0.8800,
    "available": true,
    "detail": "Speaker embedding match score 0.72"
  },
  "content_risk_signal": {
    "score": 0.9500,
    "confidence": 0.9000,
    "available": true,
    "detail": "[Multilingual NLP] Urgent financial transfer intent detected"
  },
  "risk_assessment": {
    "call_session_id": "call-sess-994102",
    "risk_score": 0.9120,
    "confidence": 0.9500,
    "actions": ["RECOMMEND_CALLBACK_VERIFICATION", "FLAG_SUSPICIOUS"],
    "explanation": "high risk (0.91): AI synthesis detected; financial urgency intent",
    "degraded": false
  },
  "policy_decision": {
    "call_session_id": "call-sess-994102",
    "tenant_id": "bank-retail-prod",
    "risk_score": 0.9120,
    "final_action": "RECOMMEND_CALLBACK_VERIFICATION",
    "policy_version": 1
  },
  "final_action": "RECOMMEND_CALLBACK_VERIFICATION"
}`}
                  language="json"
                  title="Response Payload Schema"
                />
              </div>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
