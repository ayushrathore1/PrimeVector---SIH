import React from 'react';
import { Lock, Shield, Cpu, ExternalLink } from 'lucide-react';

export default function Footer({ setActiveTab }) {
  return (
    <footer className="bg-obsidian-950 border-t border-obsidian-700/80 py-12 text-slate-400 font-sans">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Col 1 */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-5 h-5 text-forensic-amber" />
              <span className="font-serif text-lg font-bold text-white tracking-wide">
                PRIME<span className="text-forensic-amber">VECTOR</span>
              </span>
            </div>
            <p className="text-sm text-slate-400 mb-4 max-w-md leading-relaxed">
              Real-time voice authenticity verification and scam pattern analysis platform. Built for banking, call centers, and telecom infrastructure.
            </p>
            <div className="flex flex-wrap gap-2 text-xs font-mono">
              <span className="px-2.5 py-1 rounded bg-obsidian-900 border border-obsidian-700 text-slate-300 flex items-center gap-1.5">
                <Lock size={12} className="text-emerald-400" /> Fail-Safe Guarantee
              </span>
              <span className="px-2.5 py-1 rounded bg-obsidian-900 border border-obsidian-700 text-slate-300 flex items-center gap-1.5">
                <Cpu size={12} className="text-forensic-amber" /> RAM-Only Audio Processing
              </span>
            </div>
          </div>

          {/* Col 2 */}
          <div>
            <h4 className="font-mono text-xs font-semibold text-slate-200 uppercase tracking-wider mb-3">
              Platform Navigation
            </h4>
            <ul className="space-y-2 text-sm font-mono">
              <li>
                <button onClick={() => setActiveTab('home')} className="hover:text-forensic-amber transition-colors">
                  System Overview
                </button>
              </li>
              <li>
                <button onClick={() => setActiveTab('status')} className="hover:text-forensic-amber transition-colors">
                  Live Service Status (8/8)
                </button>
              </li>
              <li>
                <button onClick={() => setActiveTab('demo')} className="hover:text-forensic-amber transition-colors">
                  Real-Time Event Stream
                </button>
              </li>
              <li>
                <button onClick={() => setActiveTab('docs')} className="hover:text-forensic-amber transition-colors">
                  API & SDK Documentation
                </button>
              </li>
            </ul>
          </div>

          {/* Col 3 */}
          <div>
            <h4 className="font-mono text-xs font-semibold text-slate-200 uppercase tracking-wider mb-3">
              System Invariants
            </h4>
            <ul className="space-y-2 text-xs text-slate-400 font-mono">
              <li>• Noisy-OR Acoustic Fusion</li>
              <li>• Bounded Context Multiplier (0.85x - 1.35x)</li>
              <li>• Opt-In Auto-Block Liability Gate</li>
              <li>• Resemblyzer 256-D Voice Embeddings</li>
              <li>• Local Ollama Content Risk Classifier</li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-obsidian-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono">
          <p className="text-slate-400">
            © 2026 PrimeVector Platform • SIH Hackathon Production Candidate
          </p>
          <div className="flex items-center gap-4 text-slate-400">
            <span>Built with Go + FastAPI + React</span>
            <span>•</span>
            <span className="text-forensic-amber">Zero Audio Retention Verified</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
