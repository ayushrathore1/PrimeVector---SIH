import React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, Activity, Lock, Cpu, ArrowRight, Zap, CheckCircle2, AlertCircle, Layers, Radio, Sparkles } from 'lucide-react';
import PipelineVisual from '../components/PipelineVisual';

export default function HomePage({ setActiveTab }) {
  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative pt-12 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="absolute inset-0 grid-background opacity-40 pointer-events-none"></div>

        <div className="relative z-10 max-w-4xl mx-auto text-center space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-obsidian-850 border border-forensic-amber/30 text-forensic-amber font-mono text-xs shadow-amber-glow"
          >
            <Sparkles size={14} className="text-forensic-amber" />
            <span>REAL-TIME VOICE INTEGRITY & IMPERSONATION PREVENTION</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="font-serif text-4xl sm:text-6xl font-bold tracking-tight text-white leading-[1.15]"
          >
            Acoustic proof of authenticity for live voice communications.
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-lg sm:text-xl text-slate-300 max-w-3xl mx-auto font-sans leading-relaxed"
          >
            Combines Resemblyzer speaker verification, acoustic spectral heuristic analysis, and Groq LLM transcript scam scanning into a single audited Noisy-OR risk score in under 60ms.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-wrap items-center justify-center gap-4 pt-4"
          >
            <button
              onClick={() => setActiveTab('demo')}
              className="flex items-center gap-2.5 px-6 py-3 rounded-lg bg-amber-gradient text-obsidian-950 font-mono font-bold text-sm hover:opacity-95 transition-all shadow-amber-glow"
            >
              <Radio size={16} /> Launch Live Demo Stream
            </button>

            <button
              onClick={() => setActiveTab('status')}
              className="flex items-center gap-2.5 px-6 py-3 rounded-lg bg-obsidian-850 border border-obsidian-700 text-slate-200 font-mono text-sm hover:border-forensic-amber/50 hover:bg-obsidian-800 transition-all"
            >
              <Activity size={16} className="text-forensic-amber" /> Inspect System Status (8/8)
            </button>
          </motion.div>
        </div>

        {/* 3 Core Invariants Banner */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto mt-16 pt-8 border-t border-obsidian-800">
          <div className="p-5 rounded-lg bg-obsidian-900 border border-obsidian-800">
            <div className="flex items-center gap-3 mb-2">
              <Lock className="w-5 h-5 text-emerald-400" />
              <h4 className="font-mono text-sm font-bold text-white">1. Fail-Safe Guarantee</h4>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              Missing data or service outage never passes silently (score never defaults to 0.0). The system gracefully degrades to <code className="text-amber-400">RECOMMEND_CALLBACK_VERIFICATION</code>.
            </p>
          </div>

          <div className="p-5 rounded-lg bg-obsidian-900 border border-obsidian-800">
            <div className="flex items-center gap-3 mb-2">
              <Cpu className="w-5 h-5 text-forensic-amber" />
              <h4 className="font-mono text-sm font-bold text-white">2. Zero Audio Retention</h4>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              Raw audio exists strictly in transient RAM during feature extraction. Audio bytes are never written to disk, databases, or log files.
            </p>
          </div>

          <div className="p-5 rounded-lg bg-obsidian-900 border border-obsidian-800">
            <div className="flex items-center gap-3 mb-2">
              <Zap className="w-5 h-5 text-cyan-400" />
              <h4 className="font-mono text-sm font-bold text-white">3. Opt-In Auto-Block</h4>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              <code className="text-cyan-400">auto_block_enabled</code> defaults to False per tenant. The platform surfaces audited recommendations and never unilaterally halts calls without policy opt-in.
            </p>
          </div>
        </div>
      </section>

      {/* Section 2: Interactive Pipeline Visualizer */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-4">
          <span className="font-mono text-xs font-semibold text-forensic-amber uppercase tracking-widest">
            3-Signal Evidence Architecture
          </span>
          <h2 className="font-serif text-3xl font-bold text-white mt-1">
            How evidence signals fuse into a single risk score
          </h2>
          <p className="text-sm text-slate-400 font-sans mt-2">
            No single signal can falsely block a call. Evidence signals combine using a Noisy-OR formulation so high-risk indicators are never diluted by clean secondary signals.
          </p>
        </div>

        <PipelineVisual />
      </section>

      {/* Section 3: How It Works Scroll-Triggered Steps */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 my-16">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <span className="font-mono text-xs font-semibold text-forensic-amber uppercase tracking-widest">
            Pipeline Mechanics
          </span>
          <h2 className="font-serif text-3xl font-bold text-white mt-1">
            End-to-End Ingestion to Alert Dispatch
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="p-5 rounded-xl bg-obsidian-900 border border-obsidian-700 relative"
          >
            <div className="w-8 h-8 rounded bg-obsidian-800 border border-forensic-amber/40 text-forensic-amber font-mono font-bold flex items-center justify-center mb-3">
              01
            </div>
            <h4 className="font-serif text-base font-bold text-white mb-2">Ingress & Stream Extraction</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              gRPC edge gateway streams audio chunks to <code className="text-slate-300">feature-extraction-service</code>. Converts 16kHz PCM to 80-band Log-Mel spectrogram and 256-D Resemblyzer embedding in RAM.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="p-5 rounded-xl bg-obsidian-900 border border-obsidian-700 relative"
          >
            <div className="w-8 h-8 rounded bg-obsidian-800 border border-cyan-400/40 text-cyan-400 font-mono font-bold flex items-center justify-center mb-3">
              02
            </div>
            <h4 className="font-serif text-base font-bold text-white mb-2">Parallel Signal Evaluation</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Parallel execution pings <code className="text-slate-300">spoof-detection-service</code> (acoustic score), <code className="text-slate-300">enrollment-service</code> (voiceprint match), and Groq LLM scam scanning.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="p-5 rounded-xl bg-obsidian-900 border border-obsidian-700 relative"
          >
            <div className="w-8 h-8 rounded bg-obsidian-800 border border-purple-400/40 text-purple-400 font-mono font-bold flex items-center justify-center mb-3">
              03
            </div>
            <h4 className="font-serif text-base font-bold text-white mb-2">Noisy-OR Risk Fusion</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              <code className="text-slate-300">risk-fusion-engine</code> fuses signals into P(suspicious) and applies caller context multiplier (0.85x–1.35x), producing single bounded score [0.0 - 1.0].
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="p-5 rounded-xl bg-obsidian-900 border border-obsidian-700 relative"
          >
            <div className="w-8 h-8 rounded bg-obsidian-800 border border-emerald-400/40 text-emerald-400 font-mono font-bold flex items-center justify-center mb-3">
              04
            </div>
            <h4 className="font-serif text-base font-bold text-white mb-2">Policy Gate & Alert Dispatch</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              <code className="text-slate-300">policy-threshold-engine</code> checks opt-in rules and emits <code className="text-slate-300">alerting-service</code> events with SHA-256 privacy hashing.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Section 4: HONEST CURRENT STATUS (Live Today vs. Roadmap) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-xl border border-obsidian-700 bg-obsidian-900 p-8 shadow-card-glow">
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-obsidian-800">
            <Layers className="w-6 h-6 text-forensic-amber" />
            <div>
              <h3 className="font-serif text-2xl font-bold text-white">Current System Capabilities & Status</h3>
              <p className="text-xs font-mono text-slate-400">Strict transparency breakdown: What is live today vs. what is on the roadmap</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Live Today */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs font-bold uppercase tracking-wider">
                <CheckCircle2 size={16} /> Verified Live Today (Hackathon Candidate)
              </div>
              <ul className="space-y-3 font-sans text-xs text-slate-300">
                <li className="flex items-start gap-2.5 p-3 rounded bg-obsidian-850 border border-obsidian-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5"></span>
                  <span><strong>8 Microservice Architecture:</strong> Python FastAPI services + Go gRPC Ingestion Gateway running in containerized Docker stack.</span>
                </li>
                <li className="flex items-start gap-2.5 p-3 rounded bg-obsidian-850 border border-obsidian-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5"></span>
                  <span><strong>Resemblyzer Voice Embeddings:</strong> 256-D d-vector extraction with cosine similarity comparison against enrolled voiceprints.</span>
                </li>
                <li className="flex items-start gap-2.5 p-3 rounded bg-obsidian-850 border border-obsidian-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5"></span>
                  <span><strong>Acoustic Heuristic Scoring:</strong> Spectral glitch & high-frequency synthesis artifact detection in <code className="text-amber-400">spoof-detection-service</code>.</span>
                </li>
                <li className="flex items-start gap-2.5 p-3 rounded bg-obsidian-850 border border-obsidian-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5"></span>
                  <span><strong>Groq LLM Content Scanning:</strong> Real-time transcript scam pattern & urgency keyword risk classification.</span>
                </li>
                <li className="flex items-start gap-2.5 p-3 rounded bg-obsidian-850 border border-obsidian-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5"></span>
                  <span><strong>Working Android Demo Client:</strong> Live microphone audio capture with Sarvam multilingual STT streaming to orchestrator.</span>
                </li>
              </ul>
            </div>

            {/* Roadmap */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-amber-400 font-mono text-xs font-bold uppercase tracking-wider">
                <AlertCircle size={16} /> Explicit Roadmap Items (Not Yet Built)
              </div>
              <ul className="space-y-3 font-sans text-xs text-slate-300">
                <li className="flex items-start gap-2.5 p-3 rounded bg-obsidian-850 border border-obsidian-800">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-950 text-amber-400 border border-amber-500/30">ROADMAP</span>
                  <span><strong>Deep neural spoof classifier:</strong> Replacing the current acoustic spectral heuristic with a fully fine-tuned ASVspoof 2021 neural model.</span>
                </li>
                <li className="flex items-start gap-2.5 p-3 rounded bg-obsidian-850 border border-obsidian-800">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-950 text-amber-400 border border-amber-500/30">ROADMAP</span>
                  <span><strong>Accent-Cluster Specialized Models:</strong> Routing sound features to language-specific accent models (<code className="text-slate-400">hi-in</code>, <code className="text-slate-400">ta-in</code>, <code className="text-slate-400">bn-in</code>).</span>
                </li>
                <li className="flex items-start gap-2.5 p-3 rounded bg-obsidian-850 border border-obsidian-800">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-950 text-amber-400 border border-amber-500/30">ROADMAP</span>
                  <span><strong>Edge Inference Engine:</strong> Running feature extraction & embedding creation directly on edge gateways without cloud hop.</span>
                </li>
                <li className="flex items-start gap-2.5 p-3 rounded bg-obsidian-850 border border-obsidian-800">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-950 text-amber-400 border border-amber-500/30">ROADMAP</span>
                  <span><strong>Production Telecom Integration:</strong> Direct SIP / RTP session border controller (SBC) integration for carrier networks.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
