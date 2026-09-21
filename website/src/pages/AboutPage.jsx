import React from 'react';
import { motion } from 'framer-motion';
import { Brain, Cpu, Database, Shield, Globe, Layers, Sparkles, AlertTriangle, ArrowUpRight, Radio, PhoneCall, Building2, Lock, CheckCircle2, Server, Workflow, FileText, Activity } from 'lucide-react';
import TeamSection from '../components/TeamSection';

export default function AboutPage() {
  const layersDetail = [
    {
      step: 'LAYER 1',
      name: 'Media Ingestion & SIP Telemetry Gateway',
      service: 'services/ingestion-gateway (Go / Port 8006)',
      what: 'Ingests high-throughput live audio streams from Session Border Controllers (SBCs), PBX hardware, and mobile banking applications over UDP/RTP, while capturing network SIP telemetry.',
      why: 'Inbound telephony and VoIP channels cannot be modified to inject security headers without adding latency. Ingestion must occur out-of-band via RTP media mirroring so the active voice path experiences exactly 0ms added delay.',
      how: 'The Go-based gateway listens on UDP port 8006, receiving mirrored RTP packets. It buffers raw PCM chunks into 3-second sliding windows, extracts packet jitter, RTP sequence loss, and codec anomaly indicators, and passes raw PCM in volatile RAM to the Orchestrator.',
      featureTitle: 'Key Technical Features of Layer 1:',
      features: [
        'Zero In-Band Voice Latency: Out-of-band RTP media mirroring guarantees zero impact on active call quality.',
        'High-Throughput Go UDP Server: Capable of concurrently handling 10,000+ live call media streams.',
        'Network Telemetry Extraction: Computes RTP jitter (ms), packet loss %, and caller ID spoof probability.'
      ]
    },
    {
      step: 'LAYER 2',
      name: 'Multi-Vector Acoustic, Voiceprint & Behavioral Analysis Engine',
      service: 'services/spoof-detection-service (PyTorch / Port 8002), feature-extraction-service (Port 8001), enrollment-service (Port 8003)',
      what: 'Processes audio frames across four parallel analytical vectors to evaluate acoustic deepfake probability, voiceprint identity match, speech prosody microvariations, and conversation intent.',
      why: 'Single-feature detection is vulnerable to novel AI synthesis methods. A hybrid deepfake detection system must combine spectral phase analysis, speaker verification, prosodic rhythm tracking, and NLP intent analysis.',
      how: 'Audio is converted into 3-channel spectrograms (Log-Mel + Delta Velocity + Delta-Delta Acceleration). The DhVani v2 ResNet-SE + BiGRU + 8-Head Attention neural network scores acoustic phase stiffness. Concurrently, Resemblyzer extracts 256-dim speaker embeddings to compare against enrolled voiceprints, while NLP models evaluate transcript urgency.',
      featureTitle: 'Key Technical Features of Layer 2:',
      features: [
        'DhVani v2 Neural Architecture: 6.0M params combining Squeeze-and-Excitation ResNet-18, BiGRU, and 8-Head Self-Attention.',
        '3-Channel Spectrogram Stack: Log-Mel (spectral content) + Delta (velocity) + Delta-Delta (acceleration) to expose neural synthesis phase stiffness.',
        'IISc Vaani Dataset Generalization: Trained on IISc Bangalore Vaani corpus for robustness across 100+ Indian regional accents.',
        'Multi-Session Voiceprint Enrollment: Requires ≥3 capture sessions on distinct UTC calendar days to prevent single-sample voiceprint poisoning.'
      ]
    },
    {
      step: 'LAYER 3',
      name: 'Deterministic Risk Fusion Engine',
      service: 'services/risk-fusion-engine (FastAPI / Port 8000)',
      what: 'Fuses acoustic synthesis probability, speaker match score, SIP telemetry risk, and conversation content risk into a single, unified impersonation risk score.',
      why: 'Raw signals from individual analytical vectors can be noisy or incomplete. Regulator-audited compliance requires a deterministic mathematical fusion algorithm that produces the exact same score for identical inputs.',
      how: 'Applies a deterministic Noisy-OR probability combination model: Risk Score S = 1 - ∏(1 - s_i * c_i), where s_i represents individual vector scores and c_i represents vector confidence. The output is strictly deterministic with zero wall-clock or random dependence.',
      featureTitle: 'Key Technical Features of Layer 3:',
      features: [
        'Deterministic Fusion Scoring: Same inputs produce the exact same risk assessment (regulator compliance requirement).',
        'Noisy-OR Multi-Signal Math: Mathematically combines independent risk probabilities without assuming mutual exclusivity.',
        'Degraded Signal Resiliency: If a downstream service is offline, the signal is marked available=False and factored conservatively.'
      ]
    },
    {
      step: 'LAYER 4',
      name: 'Policy Threshold & Compliance Liability Engine',
      service: 'services/policy-threshold-engine (FastAPI / Port 8004)',
      what: 'Applies per-tenant configurable risk threshold rules to determine the final policy action (e.g. PROCEED, FLAG_SUSPICIOUS, RECOMMEND_CALLBACK_VERIFICATION).',
      why: 'Risk fusion calculates probability, but enterprise liability requires business logic to decide what action to take. Policy evaluation must be decoupled from scoring so banks can adjust risk tolerances dynamically.',
      how: 'The service receives the RiskAssessmentResponse, looks up the tenant policy configuration, checks thresholds, and outputs the final action. It enforces strict compliance invariants and logs immutable audit records.',
      featureTitle: 'Key Technical Features of Layer 4:',
      features: [
        'Zero Raw Audio Retention Invariant: Raw audio PCM bytes exist strictly in volatile RAM during inference and are unreferenced immediately. Zero audio is stored to disk.',
        'Opt-in Auto-Block Gate: auto_block_enabled defaults to False for every tenant, preventing unnotified transaction drops.',
        'Immutable Audit Trail: Logs SHA-256 hashed actor identities and UTC timestamps for compliance review.'
      ]
    },
    {
      step: 'LAYER 5',
      name: 'Multi-Channel Alerting & Enterprise API / SDK Layer',
      service: 'services/alerting-service (Port 8005), services/orchestrator (Port 8085), SDKs (Python, Node)',
      what: 'Dispatches real-time policy decisions and risk alerts to contact center agent desktops, core banking webhooks, and enterprise APIs.',
      why: 'Security intelligence is only valuable if delivered immediately to the operational decision-makers (frontline call center agents, automated IVR systems, or risk officers).',
      how: 'Dispatches async alerts over WebSockets, webhooks, and REST/gRPC endpoints. Provides enterprise SDKs for Python (satyadhvani) and Node.js (@satyadhvani/sdk).',
      featureTitle: 'Key Technical Features of Layer 5:',
      features: [
        'Real-Time WebSocket Feed: Streams live call risk updates to agent visual assist desktop widgets in sub-50ms.',
        'Enterprise SDKs: Official satyadhvani Python wheel and @satyadhvani/sdk Node.js npm packages.',
        'Multi-Channel Alerting: Supports WebSockets, HTTP Webhooks, Email, SMS, and Slack notifications.'
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-white text-forest selection:bg-lemongrass py-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        
        {/* Header */}
        <div className="space-y-4 pb-8 border-b border-forest/10">
          <div className="inline-flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-forest bg-sage-1 px-4 py-1.5 rounded-full border border-forest/15">
            <Brain size={14} className="text-forest" />
            <span>SatyaDhVani 5-Layer End-to-End System Architecture</span>
          </div>
          <h1 className="font-display text-4xl sm:text-5xl font-extrabold text-forest tracking-tight">
            Comprehensive System Architecture & Technical Specifications
          </h1>
          <p className="text-base text-forest/80 font-normal leading-relaxed max-w-4xl">
            SatyaDhVani is a multi-layered, real-time voice integrity verification framework engineered to protect financial institutions, telecommunication carriers, and enterprise communication networks against AI-generated voice cloning, synthetic deepfakes, and social engineering fraud.
          </p>

          {/* Name Origin Breakdown */}
          <div className="bg-sage-1 border border-forest/15 rounded-2xl p-8 shadow-spade spade-cut-md space-y-4 mt-6">
            <div className="flex items-center gap-2 font-display text-lg font-bold text-forest border-b border-forest/10 pb-3">
              <Sparkles size={20} className="text-forest" />
              <h3>The Etymology & Meaning Behind SatyaDhVani</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
              <div className="space-y-1">
                <span className="text-xs font-mono font-bold text-forest/60 uppercase">1. Vaani (The Foundation)</span>
                <h4 className="font-display font-bold text-forest text-base">IISc Vaani Corpus</h4>
                <p className="text-xs text-forest/70 font-sans leading-relaxed">
                  Trained on the Indian Institute of Science (IISc) Bangalore <strong>Vaani dataset</strong>, encompassing 100+ Indian regional languages, accents, and real-world acoustic environments.
                </p>
              </div>

              <div className="space-y-1 border-t md:border-t-0 md:border-l border-forest/10 pt-3 md:pt-0 md:pl-6">
                <span className="text-xs font-mono font-bold text-forest/60 uppercase">2. DhVani (Audio Waveform)</span>
                <h4 className="font-display font-bold text-forest text-base">DhVani Signal Processing</h4>
                <p className="text-xs text-forest/70 font-sans leading-relaxed">
                  Specialized neural classifier testing incoming audio sound waves (DhVani) for spectral phase stiffness, neural pitch jitter, and synthetic vocoder artifacts.
                </p>
              </div>

              <div className="space-y-1 border-t md:border-t-0 md:border-l border-forest/10 pt-3 md:pt-0 md:pl-6">
                <span className="text-xs font-mono font-bold text-emerald-800 uppercase">3. Satya (Truth Verdict)</span>
                <h4 className="font-display font-bold text-emerald-950 text-base">Satya (Truth Verification)</h4>
                <p className="text-xs text-forest/70 font-sans leading-relaxed">
                  Computes a non-random, deterministic risk score certifying whether an inbound audio stream is <strong>Satya (Genuine Human Voice)</strong> or <strong>ASatya (AI Deepfake)</strong>.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Deep Dive: 5-Layer End-to-End Architecture */}
        <section className="space-y-10">
          <div className="space-y-2">
            <h2 className="font-display text-3xl font-extrabold text-forest flex items-center gap-3">
              <Workflow className="text-forest" size={28} />
              Comprehensive 5-Layer Architectural Breakdown
            </h2>
            <p className="text-sm text-forest/70 max-w-3xl">
              An in-depth explanation of what each layer does, why it exists, how it works, and its specialized enterprise features.
            </p>
          </div>

          <div className="space-y-12">
            {layersDetail.map((layer, index) => (
              <div key={layer.step} className="bg-sage-1 border border-forest/15 rounded-2xl p-8 space-y-6 shadow-spade spade-cut-md">
                {/* Layer Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-forest/10">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-bold px-3 py-1 rounded bg-forest text-lemongrass">{layer.step}</span>
                    <h3 className="font-display text-2xl font-extrabold text-forest">{layer.name}</h3>
                  </div>
                  <span className="font-mono text-xs font-bold bg-white text-forest px-3 py-1 rounded border border-forest/15">{layer.service}</span>
                </div>

                {/* 3 Core Questions: What, Why, How */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
                  <div className="bg-white p-5 rounded-xl border border-forest/10 space-y-2">
                    <div className="flex items-center gap-2 font-mono text-xs font-bold text-forest uppercase">
                      <Activity size={14} className="text-forest" />
                      <span>What It Does</span>
                    </div>
                    <p className="text-xs text-forest/80 font-sans leading-relaxed">{layer.what}</p>
                  </div>

                  <div className="bg-white p-5 rounded-xl border border-forest/10 space-y-2">
                    <div className="flex items-center gap-2 font-mono text-xs font-bold text-forest uppercase">
                      <Shield size={14} className="text-emerald-700" />
                      <span>Why It Exists</span>
                    </div>
                    <p className="text-xs text-forest/80 font-sans leading-relaxed">{layer.why}</p>
                  </div>

                  <div className="bg-white p-5 rounded-xl border border-forest/10 space-y-2">
                    <div className="flex items-center gap-2 font-mono text-xs font-bold text-forest uppercase">
                      <Cpu size={14} className="text-forest" />
                      <span>How It Works</span>
                    </div>
                    <p className="text-xs text-forest/80 font-sans leading-relaxed">{layer.how}</p>
                  </div>
                </div>

                {/* Specialized Layer Features Box */}
                <div className="bg-white p-5 rounded-xl border border-forest/15 space-y-3">
                  <h4 className="font-mono text-xs font-bold text-forest uppercase tracking-wider">{layer.featureTitle}</h4>
                  <ul className="space-y-2 text-xs font-sans text-forest/80">
                    {layer.features.map((feat, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <CheckCircle2 size={14} className="text-emerald-700 shrink-0 mt-0.5" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Technical Model Card Section */}
        <section className="bg-sage-1 border border-forest/15 rounded-2xl p-8 spade-cut-md space-y-6 shadow-spade">
          <div className="flex items-center gap-3 border-b border-forest/10 pb-4">
            <div className="w-10 h-10 rounded-xl bg-forest text-lemongrass flex items-center justify-center font-bold shadow-sm">
              <Sparkles size={20} />
            </div>
            <div>
              <h2 className="font-display text-2xl font-extrabold text-forest">DhVani v2 Technical Model Card</h2>
              <p className="text-xs font-mono text-forest/70">ResNet-SE + BiGRU + 8-Head Multi-Head Attention Architecture</p>
            </div>
          </div>

          <div className="bg-white border border-forest/10 rounded-xl overflow-hidden shadow-sm">
            <table className="w-full text-xs font-mono">
              <tbody className="divide-y divide-forest/5">
                {[
                  ['Model Name', 'DhVani Voice Deepfake Detector v2.0'],
                  ['Training Corpus', 'IISc Bangalore Vaani Dataset (100+ Indian regional languages & accents)'],
                  ['Target Task', 'Binary Deepfake Classifier (Satya/Bonafide vs. ASatya/Spoof)'],
                  ['Model Topology', 'Squeeze-and-Excitation ResNet-18 + 2-layer BiGRU + 8-head Multi-Head Attention'],
                  ['Parameter Count', '~6.0 Million Parameters (upgraded from v1 ~1.2M)'],
                  ['Input Features', '16kHz mono PCM → 3-channel Spectrogram Stack (Log-Mel + Delta Velocity + Delta-Delta Acceleration)'],
                  ['Feature Specs', 'n_mels=80, n_fft=2048, hop_length=160 (10ms), win_length=400 (25ms)'],
                  ['Output Verdict', 'Synthetic probability [0.0 = Real Human, 1.0 = AI Deepfake]'],
                  ['P99 Inference Latency', '<50ms per 3-second audio chunk on CPU'],
                  ['Loss Function', 'Focal Loss (mines hard synthetic examples, alpha=0.25, gamma=2.0)'],
                  ['Regularization & Aug', 'SpecAugment + Online Noise/Telephone/Reverb + Mixup (alpha=0.2) + Label Smoothing (0.05)'],
                  ['Framework & Runtime', 'PyTorch 2.x + Colab T4 GPU Training / CPU Inference Engine'],
                ].map(([key, val]) => (
                  <tr key={key} className="hover:bg-sage-1/50 transition-colors">
                    <td className="py-3 px-5 text-forest/70 font-bold whitespace-nowrap w-56">{key}</td>
                    <td className="py-3 px-5 text-forest font-semibold">{val}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Architecture Comparison: v1 vs v2 */}
        <section className="bg-sage-1 border border-forest/10 rounded-2xl p-8 spade-cut-md space-y-4 shadow-spade">
          <h2 className="font-display text-2xl font-extrabold text-forest flex items-center gap-2">
            <ArrowUpRight size={20} className="text-emerald-700" />
            Architectural Evolution: v1 vs v2
          </h2>
          <div className="bg-white border border-forest/10 rounded-xl overflow-hidden shadow-sm">
            <table className="w-full text-xs font-mono">
              <thead>
                <tr className="bg-forest text-lemongrass">
                  <th className="py-3.5 px-5 text-left font-bold">Component</th>
                  <th className="py-3.5 px-5 text-left font-bold">DhVani v1</th>
                  <th className="py-3.5 px-5 text-left font-bold">DhVani v2</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-forest/5 text-forest">
                {[
                  ['Backbone Architecture', '4-block vanilla CNN', 'ResNet-18 with Squeeze-and-Excitation (SE) blocks'],
                  ['Temporal Modeling', 'None (global avg pool)', '2-layer Bidirectional GRU (BiGRU)'],
                  ['Attention Mechanism', 'None', '8-head Multi-Head Self-Attention'],
                  ['Input Feature Representation', '1-channel Log-Mel', '3-channel: Log-Mel + Delta (velocity) + Delta-Delta (acceleration)'],
                  ['Parameters', '~1.2 Million', '~6.0 Million'],
                  ['Loss Function', 'BCEWithLogitsLoss', 'Focal Loss (mines hard examples)'],
                  ['Data Augmentation', 'Eval-time only', 'Online SpecAugment + Telephone Filter + Reverb + Mixup'],
                  ['Generalization Dataset', 'FLEURS fallback', 'IISc Vaani Dataset (100+ Indian regional languages)'],
                ].map(([comp, v1, v2]) => (
                  <tr key={comp} className="hover:bg-sage-1/50 transition-colors">
                    <td className="py-3 px-5 font-bold text-forest/70">{comp}</td>
                    <td className="py-3 px-5 text-forest/60">{v1}</td>
                    <td className="py-3 px-5 font-semibold text-emerald-800">{v2}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Enterprise Security Invariants & Compliance Commitments */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-sage-1 border border-forest/15 rounded-2xl p-6 spade-cut-sm space-y-3">
            <Shield size={22} className="text-emerald-700" />
            <h4 className="font-display text-lg font-bold text-forest">Zero Raw Audio Retention Invariant</h4>
            <p className="text-xs text-forest/80 leading-relaxed font-sans">
              Raw audio PCM bytes exist solely in volatile RAM memory during forward pass feature extraction. Inputs are dereferenced immediately after scoring — zero audio files or recordings are written to disk, databases, or persistent caches.
            </p>
          </div>

          <div className="bg-sage-1 border border-forest/15 rounded-2xl p-6 spade-cut-sm space-y-3">
            <Globe size={22} className="text-forest" />
            <h4 className="font-display text-lg font-bold text-forest">Fail-Safe Design Invariant (Never Fails Open)</h4>
            <p className="text-xs text-forest/80 leading-relaxed font-sans">
              Missing signals, network timeouts, or downstream service outages always result in conservative recommendations (<code className="bg-white px-1.5 py-0.5 rounded border border-forest/10 font-mono text-[11px] font-bold">RECOMMEND_CALLBACK_VERIFICATION</code>). The system never treats missing data as risk score 0.0.
            </p>
          </div>
        </section>

        {/* Core Engineering & Research Team */}
        <TeamSection />

      </div>
    </div>
  );
}
