import React from 'react';
import { Info, Shield, Users, Lock, Cpu, Code2 } from 'lucide-react';

export default function AboutPage() {
  const teamMembers = [
    {
      name: 'Backend & ML Architecture Lead',
      role: 'Microservices & Fusion Math',
      focus: 'Built the 8 FastAPI + Go microservices, Noisy-OR fusion engine, and fail-safe pipeline logic.',
    },
    {
      name: 'Audio Processing & Speech Engineer',
      role: 'Feature Extraction & Embeddings',
      focus: 'Integrated 256-D Resemblyzer d-vectors, Log-Mel spectrogram generation, and RAM privacy guards.',
    },
    {
      name: 'Mobile & Android Engineer',
      role: 'Android App & Sarvam STT',
      focus: 'Built the native Android mic capture ingestion client and live Sarvam STT streaming integration.',
    },
    {
      name: 'Frontend Engineer & Designer',
      role: 'Web Platform & Live Dashboard',
      focus: 'Hand-crafted the bespoke security design system, live status telemetry, and API documentation.',
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">
      {/* Header */}
      <div className="pb-6 border-b border-obsidian-700">
        <div className="flex items-center gap-2">
          <Info className="w-6 h-6 text-forensic-amber" />
          <h1 className="font-serif text-3xl font-bold text-white">About PrimeVector & Project Context</h1>
        </div>
        <p className="text-xs font-mono text-slate-400 mt-1">
          Developed for SIH Hackathon • Real voice integrity & impersonation defense platform
        </p>
      </div>

      {/* Project Overview */}
      <div className="rounded-xl border border-obsidian-700 bg-obsidian-900 p-8 shadow-card-glow space-y-4">
        <h2 className="font-serif text-2xl font-bold text-white">Engineering Philosophy</h2>
        <p className="text-sm text-slate-300 font-sans leading-relaxed max-w-3xl">
          Voice fraud and AI voice cloning pose an existential threat to phone-based banking, wire transfer approvals, and corporate decision-making. Human ears can no longer distinguish between genuine human speech and sub-second voice clones.
        </p>
        <p className="text-sm text-slate-300 font-sans leading-relaxed max-w-3xl">
          PrimeVector was engineered as an <strong>event-driven, zero-trust voice defense layer</strong> that analyzes acoustic spectral artifacts, speaker identity embedding vectors, and conversation content simultaneously, enforcing strict zero-audio-retention invariants.
        </p>
      </div>

      {/* Minimal Team Cards */}
      <div className="space-y-4">
        <h2 className="font-serif text-2xl font-bold text-white flex items-center gap-2">
          <Users size={20} className="text-forensic-amber" /> Team Roles
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {teamMembers.map((member, idx) => (
            <div key={idx} className="p-5 rounded-xl bg-obsidian-900 border border-obsidian-700 space-y-2">
              <div className="w-8 h-8 rounded bg-obsidian-850 border border-obsidian-700 flex items-center justify-center font-mono text-xs font-bold text-forensic-amber">
                0{idx + 1}
              </div>
              <h4 className="font-serif text-base font-bold text-white">{member.name}</h4>
              <div className="text-xs font-mono text-forensic-amber font-semibold">{member.role}</div>
              <p className="text-xs text-slate-400 font-sans leading-relaxed pt-1">{member.focus}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
