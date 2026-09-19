import React from 'react';
import { motion } from 'framer-motion';
import {
  ShieldAlert, Zap, Cpu, ArrowRight, Terminal, Lock, Brain,
  Layers, Mic, FileAudio, Clock, CheckCircle, Sparkles, Activity,
  Sliders, ShieldCheck, Database
} from 'lucide-react';
import CodeBlock from '../components/CodeBlock';

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

        {/* ── HERO SECTION (Spade Style Cut-Corner Block) ────────────────────────── */}
        <section className="relative">
          <div className="relative rounded-2xl p-8 sm:p-14 lg:p-20 spade-cut-md border border-forest/10 shadow-spade text-center overflow-hidden">

            {/* Hero background image */}
            <img
              src="/assets/hero_bg.png"
              alt=""
              aria-hidden="true"
              className="absolute inset-0 w-full h-full object-cover"
            />
            {/* Slight overlay for text readability */}
            <div className="absolute inset-0 bg-white/30 backdrop-blur-[1px]" />

            <div className="relative z-10 max-w-4xl mx-auto space-y-8">

              {/* Badge */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white border border-forest/15 shadow-sm text-forest font-mono text-xs font-semibold"
              >
                <Sparkles size={14} className="text-forest" />
                <span>4-VECTOR FIREWALL · DHVANI 2 + VOICEPRINT + VISHING NLP + SIP TELEMETRY</span>
              </motion.div>

              {/* Main Display Headline */}
              <motion.h1
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="font-display text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-forest leading-[1.08]"
              >
                <span className="text-forest/60 text-2xl sm:text-3xl lg:text-4xl font-bold block mb-2">PrimeVector Multi-Vector Platform</span>
                <span className="relative inline-block">
                  <span className="relative z-10">SatyaDh</span><span className="relative z-10 text-forest">V</span><span className="relative z-10">ani 2 & Anti-Impersonation</span>
                  <span className="absolute bottom-1 left-0 right-0 h-3 sm:h-4 bg-lemongrass/40 -z-0 rounded-sm" />
                </span>
              </motion.h1>

              {/* Subtitle */}
              <motion.p
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="text-base sm:text-xl text-forest/80 max-w-2xl mx-auto leading-relaxed font-normal"
              >
                Enterprise real-time voice integrity & anti-impersonation firewall — fusing <strong>Acoustic Forensics</strong>, <strong>Speaker Voiceprints</strong>, <strong>Conversational Vishing NLP</strong>, and <strong>SIP Call Telemetry</strong> in sub-50ms.
              </motion.p>

              {/* CTAs */}
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
                className="flex flex-wrap items-center justify-center gap-4 pt-2"
              >
                <button
                  onClick={() => setActiveTab('detect')}
                  className="group inline-flex items-center gap-2.5 bg-forest text-lemongrass hover:bg-forest-hover font-semibold text-sm sm:text-base px-8 py-4 rounded-md shadow-spade-lg transition-all transform hover:scale-[0.98] cursor-pointer"
                >
                  <Mic size={18} />
                  <span>Try Live Detector</span>
                  <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                </button>

                <button
                  onClick={() => setActiveTab('docs')}
                  className="inline-flex items-center gap-2 bg-white text-forest hover:bg-sage-2 border border-forest/20 font-semibold text-sm sm:text-base px-7 py-4 rounded-md shadow-sm transition-all hover:border-forest/40"
                >
                  <Terminal size={17} className="text-forest" />
                  <span>API Documentation</span>
                </button>
              </motion.div>

              {/* Stat Card Badge (Spade style) */}
              <div className="pt-6 inline-flex items-center gap-4 bg-white/90 border border-forest/15 px-5 py-3 rounded-lg shadow-sm">
                <div className="flex items-center gap-2 border-r border-forest/15 pr-4">
                  <span className="font-display font-extrabold text-2xl text-forest">&lt;50ms</span>
                  <span className="text-xs text-forest/70 text-left leading-tight font-medium">P99 enrichment<br />latency</span>
                </div>
                <div className="flex items-center gap-2 border-r border-forest/15 pr-4">
                  <span className="font-display font-extrabold text-2xl text-forest">~6M</span>
                  <span className="text-xs text-forest/70 text-left leading-tight font-medium">Model<br />parameters</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-display font-extrabold text-2xl text-forest">0 Bytes</span>
                  <span className="text-xs text-forest/70 text-left leading-tight font-medium">Audio retained<br />on disk</span>
                </div>
              </div>

            </div>
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

        {/* ── BOTTOM CTA BANNER ────────────────────────── */}
        <section className="bg-forest text-white rounded-2xl p-10 sm:p-16 spade-cut-lg text-center space-y-6 relative overflow-hidden shadow-spade-lg">
          <div className="absolute inset-0 bg-grid-spade opacity-10 pointer-events-none" />

          <div className="relative z-10 max-w-2xl mx-auto space-y-4">
            <h2 className="font-display text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
              Add voice authenticity to every stream
            </h2>
            <p className="text-white/80 text-base sm:text-lg font-normal">
              Get instant API keys and start testing DhVani 2 voice deepfake detection today.
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
