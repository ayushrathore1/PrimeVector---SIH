import React from 'react';
import { motion } from 'framer-motion';
import {
  ShieldAlert, Zap, Cpu, ArrowRight, Terminal, Lock, Brain,
  Layers, Mic, FileAudio, Clock, CheckCircle, Activity,
  Sliders, ShieldCheck, Database, Landmark, Radio, PhoneCall, Building2, Server,
  Sparkles, Eye, Waves
} from 'lucide-react';
import { EmeraldHorizonBackground } from '@designcodeio/threeui';
import CodeBlock from '../components/CodeBlock';
import TeamSection from '../components/TeamSection';

export default function HomePage({ setActiveTab }) {

  return (
    <div className="relative min-h-screen bg-white text-forest selection:bg-lemongrass selection:text-forest overflow-hidden">

      {/* ── Spade Decorative Edge Ruler Ticks ────────────────────────── */}
      <div className="absolute top-4 bottom-0 flex w-4.5 flex-col space-y-7 overflow-y-clip left-2 max-lg:hidden pointer-events-none" aria-hidden="true">
        {[...Array(35)].map((_, i) => (
          <div key={i} className={`h-px bg-forest/20 shrink-0 ${i % 5 === 0 ? 'w-4.5 bg-forest/40' : 'w-2.5'}`} />
        ))}
      </div>
      <div className="absolute top-4 bottom-0 flex w-4.5 flex-col space-y-7 overflow-y-clip right-2 items-end max-lg:hidden pointer-events-none" aria-hidden="true">
        {[...Array(35)].map((_, i) => (
          <div key={i} className={`h-px bg-forest/20 shrink-0 ${i % 5 === 0 ? 'w-4.5 bg-forest/40' : 'w-2.5'}`} />
        ))}
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-24 space-y-24">

        {/* ── 3D WEBGL HERO SECTION (Powered by ThreeUI) ────────────────────────── */}
        <section className="relative">
          <div className="relative rounded-3xl p-6 sm:p-12 lg:p-16 border border-forest/15 shadow-2xl text-center overflow-hidden bg-[#0A1309] min-h-[580px] sm:min-h-[640px] flex flex-col justify-between">

            {/* ── Dedicated 3D Horizon WebGL Background Canvas Layer ── */}
            <div className="absolute inset-0 z-0 pointer-events-auto">
              <EmeraldHorizonBackground
                speed={0.85}
                waveScale={1.1}
                variation={1.2}
                glow={1.4}
                vignette={0.8}
                className="w-full h-full opacity-90"
              />
            </div>

            {/* Radial Vignette & Atmospheric Overlay */}
            <div className="absolute inset-0 bg-gradient-to-b from-[#0A1309]/50 via-transparent to-[#0A1309]/90 pointer-events-none z-1" />

            {/* Top Bar: 3D Horizon Indicator */}
            <div className="relative z-10 flex items-center justify-between gap-3 pb-6 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#C5FF34] shadow-[0_0_8px_#C5FF34] animate-ping" />
                <span className="font-mono text-xs font-bold text-[#C5FF34] uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles size={13} />
                  <span>3D Acoustic Horizon Engine</span>
                </span>
              </div>

              <div className="hidden sm:flex items-center gap-2 px-3.5 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/15 text-[11px] font-mono text-white/80">
                <span className="w-1.5 h-1.5 rounded-full bg-[#C5FF34]" />
                <span>Real-Time WebGL 2.0 Shader</span>
              </div>
            </div>

            {/* Center Hero Content */}
            <div className="relative z-10 max-w-4xl mx-auto my-auto py-8 space-y-7">

              {/* Sub-badge */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-[#C5FF34] text-xs font-mono font-bold"
              >
                <span>Team PrimeVector Presents · Smart India Hackathon</span>
              </motion.div>

              {/* Main Display Headline */}
              <motion.h1
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="font-display text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight text-white leading-[1.08]"
              >
                <span>SatyaDh</span><span className="text-[#C5FF34]">V</span><span>ani 2</span>
                <span className="block text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white/90 mt-2">
                  Voice Integrity & Anti-Impersonation Firewall
                </span>
              </motion.h1>

              {/* Subtitle */}
              <motion.p
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="text-base sm:text-lg text-white/80 max-w-2xl mx-auto leading-relaxed font-normal"
              >
                Zero-trust real-time voice defense in sub-50ms — fusing <strong className="text-white">Acoustic Forensics</strong>, <strong className="text-white">Voiceprints</strong>, <strong className="text-white">Vishing NLP</strong>, and <strong className="text-white">SIP Call Telemetry</strong> to protect every financial authorization.
              </motion.p>

              {/* Action Buttons */}
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
                className="flex flex-wrap items-center justify-center gap-4 pt-2"
              >
                <button
                  onClick={() => setActiveTab('detect')}
                  className="group inline-flex items-center gap-2.5 bg-[#C5FF34] text-[#0B150A] hover:bg-[#B5EF24] font-mono font-bold text-sm sm:text-base px-8 py-4 rounded-full shadow-lg transition-all transform hover:scale-[1.02] cursor-pointer"
                >
                  <Mic size={18} />
                  <span>Launch Live Detector</span>
                  <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                </button>

                <button
                  onClick={() => setActiveTab('docs')}
                  className="inline-flex items-center gap-2 bg-white/15 text-white hover:bg-white/25 backdrop-blur-md border border-white/25 font-mono font-bold text-sm sm:text-base px-7 py-4 rounded-full shadow-sm transition-all"
                >
                  <Terminal size={17} />
                  <span>API Documentation</span>
                </button>
              </motion.div>

            </div>

            {/* Bottom 3D Stat Bar */}
            <div className="relative z-10 pt-6 border-t border-white/10 grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-3xl mx-auto w-full">
              <div className="p-3 bg-white/10 backdrop-blur-md rounded-xl border border-white/15 text-center">
                <span className="font-display font-black text-2xl text-[#C5FF34] block">&lt;50ms</span>
                <span className="text-xs font-mono text-white/70 block mt-0.5">P99 Enrichment Latency</span>
              </div>
              <div className="p-3 bg-white/10 backdrop-blur-md rounded-xl border border-white/15 text-center">
                <span className="font-display font-black text-2xl text-[#C5FF34] block">~6M</span>
                <span className="text-xs font-mono text-white/70 block mt-0.5">Neural Model Params</span>
              </div>
              <div className="p-3 bg-white/10 backdrop-blur-md rounded-xl border border-white/15 text-center">
                <span className="font-display font-black text-2xl text-[#C5FF34] block">0 Bytes</span>
                <span className="text-xs font-mono text-white/70 block mt-0.5">Audio Retained on Disk</span>
              </div>
            </div>

          </div>
        </section>

        {/* ── ENTERPRISE INTEGRATION ARCHITECTURE (Prototype Stage Showcase) ────────────────────────── */}
        <section className="space-y-6 pt-2 pb-2">
          <div className="text-center space-y-1.5">
            <span className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-sage-1 border border-forest/15 text-[11px] font-mono font-bold uppercase tracking-widest text-forest">
              <ShieldCheck size={13} className="text-emerald-700" />
              PROTOTYPE STAGE • ENTERPRISE INTEGRATION READY
            </span>
            <p className="text-xs text-forest/80 font-sans max-w-xl mx-auto font-medium">
              Engineered for seamless integration into enterprise Session Border Controllers (SBC), IVR Gateways & Core Banking Networks
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4 items-center">
            {[
              { name: 'CORE BANKING APIS', subtitle: 'Finacle & T24 Middleware', icon: Landmark },
              { name: 'IVR VOICE FIREWALL', subtitle: 'Interactive Voice Response', icon: ShieldCheck },
              { name: 'EDGE SBC GATEWAYS', subtitle: 'AudioCodes & Ribbon SBC', icon: Radio },
              { name: 'SIP / RTP TELEMETRY', subtitle: 'VoIP Packet Interceptors', icon: PhoneCall },
              { name: 'CONTACT CENTER ASSIST', subtitle: 'Real-Time Agent Desktop', icon: Building2 },
              { name: 'MOBILE EDGE SDK', subtitle: 'Android Mic Capture Client', icon: Server },
            ].map((target, idx) => {
              const Icon = target.icon;
              return (
                <div
                  key={idx}
                  className="bg-white border border-forest/15 hover:border-forest/40 rounded-xl p-3.5 flex flex-col items-center justify-center text-center shadow-2xs hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 group cursor-default"
                >
                  <div className="w-8 h-8 rounded-lg bg-sage-1 group-hover:bg-forest group-hover:text-lemongrass text-forest flex items-center justify-center transition-colors mb-1.5">
                    <Icon size={16} />
                  </div>
                  <span className="font-display font-extrabold text-[11px] tracking-wide text-forest leading-snug">
                    {target.name}
                  </span>
                  <span className="text-[10px] font-mono text-forest/60 leading-tight mt-0.5 font-medium">
                    {target.subtitle}
                  </span>
                </div>
              );
            })}
          </div>
        </section>

        {/* ── LOGO CLOUD (Spade Social Proof) ────────────────────────── */}
        <section className="space-y-8">
          <p className="text-center text-xs font-mono font-semibold uppercase tracking-widest text-forest/60">
            Securing voice interactions for category-defining platforms & enterprise security systems
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-6 items-center opacity-70 grayscale hover:grayscale-0 transition-all">
            {['CITIZENS', 'CARDLESS', 'CASH APP', 'MOTIVE', 'VECTOR', 'FINTECH HQ'].map((logo, idx) => (
              <div key={idx} className="h-12 bg-sage-1 rounded-lg border border-forest/10 flex items-center justify-center p-3 font-display font-extrabold tracking-wider text-forest text-sm shadow-sm">
                {logo}
              </div>
            ))}
          </div>
        </section>

        {/* ── SPADE FEATURE SHOWCASE (2-Column Alternating Layout) ────────────────────────── */}
        <section className="space-y-16">

          {/* Feature 1: Risk & Authorization */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-5 space-y-4">
              <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold text-forest uppercase tracking-wider">
                <Lock size={15} className="text-forest" />
                <span>Risk & Authorization</span>
              </div>
              <h2 className="font-display text-3xl sm:text-4xl font-extrabold text-forest leading-tight">
                Make every voice authorization smarter
              </h2>
              <p className="text-forest/80 text-base leading-relaxed">
                Return enriched voice authenticity verification in under 50 milliseconds — empowering fraud and risk teams to block synthetic voice attacks in real time during sensitive IVR operations and high-value transfers.
              </p>
              <div className="pt-2">
                <button
                  onClick={() => setActiveTab('detect')}
                  className="inline-flex items-center gap-2 bg-white text-forest hover:bg-lemongrass border border-forest/20 hover:border-forest font-semibold text-sm px-5 py-2.5 rounded-md shadow-sm transition-all"
                >
                  <span>Test Risk API</span>
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>

            <div className="lg:col-span-7 bg-sage-1 border border-forest/10 rounded-2xl p-6 sm:p-8 spade-cut-md space-y-4">
              <div className="flex items-center justify-between border-b border-forest/10 pb-3">
                <div className="flex items-center gap-2 font-mono text-xs font-semibold text-forest">
                  <Activity size={14} className="text-emerald-600" />
                  <span>REAL-TIME STREAM VERDICT</span>
                </div>
                <span className="bg-emerald-100 text-emerald-800 text-[11px] font-mono font-bold px-2 py-0.5 rounded">
                  AUTHENTIC HUMAN
                </span>
              </div>

              <div className="space-y-3 font-mono text-xs text-forest/80">
                <div className="flex justify-between py-1 border-b border-forest/5">
                  <span className="text-forest/60">Input Sample Rate</span>
                  <span className="font-bold text-forest">16,000 Hz PCM</span>
                </div>
                <div className="flex justify-between py-1 border-b border-forest/5">
                  <span className="text-forest/60">Spectral Consistency Score</span>
                  <span className="font-bold text-forest">0.984 (Clean Formants)</span>
                </div>
                <div className="flex justify-between py-1 border-b border-forest/5">
                  <span className="text-forest/60">Synthetic Logit Score</span>
                  <span className="font-bold text-emerald-600">-3.421 (Low Risk)</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-forest/60">P99 Inference Latency</span>
                  <span className="font-bold text-forest font-mono">38.4 ms</span>
                </div>
              </div>
            </div>
          </div>

          {/* Feature 2: Dark Forest Feature Card (Analytics & Metering) */}
          <div className="bg-forest text-white rounded-2xl p-8 sm:p-12 spade-cut-md relative overflow-hidden shadow-spade-lg">
            <div className="absolute inset-0 bg-grid-spade opacity-10 pointer-events-none" />

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
              <div className="lg:col-span-6 space-y-4">
                <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold text-lemongrass uppercase tracking-wider">
                  <Database size={15} />
                  <span>Enterprise API & Metering</span>
                </div>
                <h2 className="font-display text-3xl sm:text-4xl font-extrabold text-white leading-tight">
                  Build voice security on solid infrastructure
                </h2>
                <p className="text-white/80 text-base leading-relaxed">
                  Generate organisation-level API keys, enforce configurable rate limits, and track usage per detection request with transparent pay-as-you-go billing.
                </p>
                <div className="pt-4 flex flex-wrap gap-4">
                  <button
                    onClick={() => setActiveTab('pricing')}
                    className="inline-flex items-center gap-2 bg-lemongrass text-forest hover:bg-lemongrass-hover font-semibold text-sm px-6 py-3 rounded-md shadow-sm transition-all"
                  >
                    <span>View Pay-As-You-Go Tiers</span>
                    <ArrowRight size={15} />
                  </button>
                  <button
                    onClick={() => setActiveTab('docs')}
                    className="inline-flex items-center gap-2 bg-transparent text-white border border-white/20 hover:bg-white/10 font-semibold text-sm px-6 py-3 rounded-md transition-all"
                  >
                    <span>Developer Documentation</span>
                  </button>
                </div>
              </div>

              <div className="lg:col-span-6 bg-white/5 border border-white/10 rounded-xl p-6 space-y-4 font-mono text-xs">
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                  <span className="text-lemongrass font-bold">API Metering Status</span>
                  <span className="text-white/60">Tenant ID: org_prime_882</span>
                </div>
                <div className="space-y-2 text-white/80">
                  <div className="flex justify-between">
                    <span>Monthly Quota</span>
                    <span className="text-lemongrass font-bold">10,000 / 100,000</span>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                    <div className="bg-lemongrass h-full rounded-full" style={{ width: '10%' }} />
                  </div>
                  <div className="flex justify-between text-[11px] text-white/60 pt-1">
                    <span>Rate Limit: 100 req/sec</span>
                    <span>Cost per 1k: $1.50</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </section>

        {/* ── DHWANI 2 ARCHITECTURE SPECIFICATIONS ────────────────────────── */}
        <section className="space-y-8">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-widest text-forest">
              Neural Engine Architecture
            </span>
            <h2 className="font-display text-3xl font-extrabold text-forest">
              Engineered specifically for acoustic spoofing
            </h2>
            <p className="text-forest/70 text-sm">
              Dhwani 2 combines residual squeeze-and-excitation layers with bi-directional recurrent units for low-latency acoustic classification.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                icon: Brain,
                title: 'Model Topology',
                desc: 'ResNet-SE + BiGRU + Multi-Head Attention neural pipeline.',
                metric: '~6M Params',
              },
              {
                icon: Clock,
                title: 'Ultra-Low Latency',
                desc: 'Sub-50ms execution on CPU/GPU standard microservices.',
                metric: '<50ms P99',
              },
              {
                icon: ShieldCheck,
                title: 'Multi-Lingual Detection',
                desc: 'Trained on Hindi, English, Marathi & Gujarati with ARTPARK-IISc Vaani dataset.',
                metric: '4 Languages',
              },
              {
                icon: Lock,
                title: 'Zero Retention',
                desc: 'Transient RAM inference dereferenced immediately after scoring.',
                metric: '0 Bytes Disk',
              },
            ].map((item, idx) => (
              <div key={idx} className="bg-sage-1 border border-forest/10 rounded-xl p-6 space-y-3 spade-cut-sm hover:border-forest/30 transition-colors">
                <div className="w-10 h-10 rounded-lg bg-forest text-lemongrass flex items-center justify-center font-bold">
                  <item.icon size={20} />
                </div>
                <div className="text-xs font-mono font-bold text-forest uppercase tracking-wider">{item.metric}</div>
                <h4 className="font-display text-lg font-bold text-forest">{item.title}</h4>
                <p className="text-xs text-forest/70 leading-relaxed font-normal">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── CODE API EXAMPLE ────────────────────────── */}
        <section className="bg-sage-1 border border-forest/10 rounded-2xl p-8 sm:p-12 spade-cut-md space-y-6">
          <div className="max-w-2xl">
            <span className="text-xs font-mono font-semibold uppercase tracking-widest text-forest">
              Developer Quickstart
            </span>
            <h2 className="font-display text-3xl font-extrabold text-forest mt-1">
              Integrate voice detection in minutes
            </h2>
            <p className="text-forest/80 text-sm mt-2">
              Pass audio base64 or audio binary streams to the REST endpoint and receive immediate detection analytics.
            </p>
          </div>

          <CodeBlock
            code={`curl -X POST https://api.primevector.dev/v1/detect \\
  -H "X-API-Key: pv_live_your_org_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "audio_pcm_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
    "sample_rate": 16000
  }'

# Response Payload (<50ms):
{
  "verdict": "real",
  "spoof_score": 0.0421,
  "confidence": 0.9579,
  "raw_logit": -2.8512,
  "latency_ms": 36.8,
  "model_version": "Dhwani-v2.0"
}`}
            language="bash"
            title="cURL Request — Real vs Fake Voice Verification"
          />

          <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
            <div className="flex items-center gap-2 text-xs font-mono text-forest/70">
              <CheckCircle size={15} className="text-emerald-600" />
              <span>Includes Python, Node.js & Go SDK examples</span>
            </div>
            <button
              onClick={() => setActiveTab('docs')}
              className="inline-flex items-center gap-2 bg-forest text-lemongrass hover:bg-forest-hover font-semibold text-xs px-5 py-2.5 rounded-md shadow-sm transition-all"
            >
              <span>Explore Full API Documentation</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </section>

        {/* ── CORE TEAM MEMBERS ────────────────────────── */}
        <TeamSection />

        {/* ── BOTTOM CTA BANNER ────────────────────────── */}
        <section className="bg-forest text-white rounded-2xl p-10 sm:p-16 spade-cut-lg text-center space-y-6 relative overflow-hidden shadow-spade-lg">
          <div className="absolute inset-0 bg-grid-spade opacity-10 pointer-events-none" />

          <div className="relative z-10 max-w-2xl mx-auto space-y-4">
            <h2 className="font-display text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
              Add voice authenticity to every stream
            </h2>
            <p className="text-white/80 text-base sm:text-lg font-normal">
              Get instant API keys and start testing SatyaDhVani 2 voice deepfake detection today.
            </p>
            <div className="pt-4 flex flex-wrap justify-center gap-4">
              <button
                onClick={() => setActiveTab('detect')}
                className="inline-flex items-center gap-2.5 bg-lemongrass text-forest hover:bg-lemongrass-hover font-bold text-sm sm:text-base px-8 py-4 rounded-md shadow-md transition-all transform hover:scale-[0.98]"
              >
                <Mic size={18} />
                <span>Launch Live Detector</span>
              </button>

              <button
                onClick={() => setActiveTab('pricing')}
                className="inline-flex items-center gap-2 bg-white/10 text-white border border-white/20 hover:bg-white/20 font-semibold text-sm sm:text-base px-7 py-4 rounded-md transition-all"
              >
                <span>Get API Credentials</span>
              </button>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
