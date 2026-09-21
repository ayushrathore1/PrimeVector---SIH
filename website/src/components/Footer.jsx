import React from 'react';
import { Shield, Lock, ArrowUpRight, Sparkles, Cpu, Radio, ShieldCheck, ExternalLink } from 'lucide-react';

export default function Footer({ setActiveTab }) {
  const teamMembers = [
    { name: 'Ayush Rathore', role: 'Team Lead & Architect', url: 'https://linkedin.com/in/ayushrathore1' },
    { name: 'Gourav Nagori', role: 'ML & Acoustics', url: 'https://www.linkedin.com/in/gourav-nagori1/' },
    { name: 'Awantika Jaiswal', role: 'Backend & Ingestion', url: 'https://www.linkedin.com/in/awantika-jaiswal-31904a23b/' },
    { name: 'Abhishi Samar', role: 'Frontend & UI/UX', url: 'https://www.linkedin.com/in/abhishi-samar-364083355/' },
    { name: 'Soumalya Jana', role: 'Security & Audit', url: 'https://www.linkedin.com/in/soumalya-jana-746294230/' },
    { name: 'Tarun Jha', role: 'Cloud & Infrastructure', url: 'https://www.linkedin.com/in/tarunjhaaa/' },
  ];

  return (
    <footer className="relative bg-forest text-white pt-16 pb-12 overflow-hidden border-t border-forest-dark">
      {/* Background Decorative Grid */}
      <div className="absolute inset-0 pointer-events-none opacity-10 bg-grid-spade" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">

        {/* Top Section: Main Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10 pb-12 border-b border-white/20">

          {/* Brand Column */}
          <div className="md:col-span-4 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-lemongrass flex items-center justify-center text-forest font-bold shadow-md">
                <Shield size={20} />
              </div>
              <div>
                <span className="font-display text-2xl font-black tracking-tight text-white block leading-none">
                  SatyaDh<span className="text-lemongrass">Vani 2</span>
                </span>
                <span className="text-[10px] font-mono tracking-widest uppercase text-white/70 font-semibold">
                  Enterprise Voice Firewall
                </span>
              </div>
            </div>

            <p className="text-xs sm:text-sm text-white/90 leading-relaxed font-normal max-w-sm">
              Real-time voice integrity & deepfake detection platform. Transforming raw acoustic streams into deterministic authenticity records — certifying <strong>Satya (Genuine)</strong> vs. <strong>ASatya (Deepfake)</strong> in under 50ms.
            </p>

            {/* Badges */}
            <div className="flex flex-wrap gap-2 pt-1">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-white/10 border border-white/25 text-xs font-mono font-semibold text-lemongrass">
                <Sparkles size={13} /> SatyaDhVani
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-white/10 border border-white/25 text-xs font-mono font-semibold text-white">
                <Lock size={13} className="text-emerald-400" /> RAM-Only Zero Retention
              </span>
            </div>

            <div className="text-[11px] font-mono text-white/75 pt-1">
              Engineered by <span className="text-lemongrass font-bold">Team PrimeVector</span>
            </div>
          </div>

          {/* Navigation Column 1: Platform & Features */}
          <div className="md:col-span-3 space-y-4">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-lemongrass border-b border-white/10 pb-1">
              Platform & Features
            </h4>
            <ul className="space-y-2.5 text-xs font-mono">
              <li>
                <button
                  onClick={() => setActiveTab('home')}
                  className="text-white hover:text-lemongrass transition-colors flex items-center gap-1.5 text-left cursor-pointer font-medium"
                >
                  <span>Voice Integrity Overview</span>
                </button>
              </li>
              <li>
                <button
                  onClick={() => setActiveTab('detect')}
                  className="text-white hover:text-lemongrass transition-colors flex items-center gap-1.5 text-left cursor-pointer font-medium"
                >
                  <span>Live Deepfake Detector</span>
                  <ArrowUpRight size={13} className="text-lemongrass" />
                </button>
              </li>
              <li>
                <button
                  onClick={() => setActiveTab('stream')}
                  className="text-white hover:text-lemongrass transition-colors flex items-center gap-1.5 text-left cursor-pointer font-medium"
                >
                  <Radio size={12} className="text-lemongrass" />
                  <span>SIP Telemetry Monitor</span>
                </button>
              </li>
              <li>
                <button
                  onClick={() => setActiveTab('docs')}
                  className="text-white hover:text-lemongrass transition-colors text-left cursor-pointer font-medium"
                >
                  API Docs & Enterprise SDKs
                </button>
              </li>
              <li>
                <button
                  onClick={() => setActiveTab('pricing')}
                  className="text-white hover:text-lemongrass transition-colors text-left cursor-pointer font-medium"
                >
                  Metered Pricing & Tokens
                </button>
              </li>
              <li>
                <button
                  onClick={() => setActiveTab('android')}
                  className="text-white hover:text-lemongrass transition-colors text-left cursor-pointer font-medium"
                >
                  Android Mobile Client APK
                </button>
              </li>
            </ul>
          </div>

          {/* Navigation Column 2: Architecture & Hard Invariants */}
          <div className="md:col-span-5 space-y-4">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-lemongrass border-b border-white/10 pb-1">
              Architectural Invariants & Science
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono text-white/90">
              <div className="bg-white/5 border border-white/10 rounded-lg p-3 space-y-1">
                <div className="text-lemongrass font-bold flex items-center gap-1.5">
                  <ShieldCheck size={14} /> Never Fail Open
                </div>
                <p className="text-[11px] text-white/80 leading-snug">
                  Missing data triggers automatic callback verification.
                </p>
              </div>

              <div className="bg-white/5 border border-white/10 rounded-lg p-3 space-y-1">
                <div className="text-lemongrass font-bold flex items-center gap-1.5">
                  <Lock size={14} /> Audio Non-Retention
                </div>
                <p className="text-[11px] text-white/80 leading-snug">
                  PCM bytes are processed in-memory & instantly purged.
                </p>
              </div>

              <div className="bg-white/5 border border-white/10 rounded-lg p-3 space-y-1">
                <div className="text-lemongrass font-bold flex items-center gap-1.5">
                  <Cpu size={14} /> Sub-50ms P99 Latency
                </div>
                <p className="text-[11px] text-white/80 leading-snug">
                  C++ LFCC feature extraction & ONNX acceleration.
                </p>
              </div>

              <div className="bg-white/5 border border-white/10 rounded-lg p-3 space-y-1">
                <div className="text-lemongrass font-bold flex items-center gap-1.5">
                  <Sparkles size={14} /> Satya Verdicts
                </div>
                <p className="text-[11px] text-white/80 leading-snug">
                  Deterministic fusion scoring (Satya vs ASatya).
                </p>
              </div>
            </div>
          </div>

        </div>

        {/* Middle Section: Team PrimeVector Credits */}
        <div className="py-8 border-b border-white/15">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-4">
            <div>
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-lemongrass">
                Team PrimeVector Innovators
              </h4>
              <p className="text-xs font-mono text-white/70">
                Architects & engineers behind SatyaDhVani 2
              </p>
            </div>
            <button
              onClick={() => setActiveTab('about')}
              className="text-xs font-mono text-white hover:text-lemongrass underline flex items-center gap-1 cursor-pointer"
            >
              <span>View Full Architecture & Team Specs</span>
              <ArrowUpRight size={13} />
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {teamMembers.map((member) => (
              <a
                key={member.name}
                href={member.url}
                target="_blank"
                rel="noreferrer"
                className="group flex flex-col p-2.5 rounded-lg bg-white/5 border border-white/10 hover:border-lemongrass/50 hover:bg-white/10 transition-all text-left"
              >
                <div className="flex items-center justify-between w-full">
                  <span className="font-mono text-xs font-bold text-white group-hover:text-lemongrass transition-colors truncate">
                    {member.name}
                  </span>
                  <ExternalLink size={11} className="text-white/40 group-hover:text-lemongrass shrink-0" />
                </div>
                <span className="text-[10px] font-mono text-white/70 truncate mt-0.5">
                  {member.role}
                </span>
              </a>
            ))}
          </div>
        </div>

        {/* Bottom Section: Copyright & Status */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-white/80">
          <p>© 2026 SatyaDhVani 2 Platform by Team PrimeVector. All rights reserved.</p>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 text-lemongrass font-bold">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              All Systems Operational
            </span>
            <span>•</span>
            <span>SIH 2026 Project</span>
          </div>
        </div>

      </div>
    </footer>
  );
}

