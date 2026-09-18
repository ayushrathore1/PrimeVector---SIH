import React from 'react';
import { Shield, Lock, Cpu, ArrowUpRight, Sparkles } from 'lucide-react';

export default function Footer({ setActiveTab }) {
  return (
    <footer className="relative bg-forest text-white pt-16 pb-12 overflow-hidden border-t border-forest-dark">
      {/* Background Decorative Graphic */}
      <div className="absolute inset-0 pointer-events-none opacity-10 bg-grid-spade" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10 pb-12 border-b border-white/10">
          
          {/* Brand Column */}
          <div className="md:col-span-5 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded bg-lemongrass flex items-center justify-center text-forest font-bold">
                <Shield size={18} />
              </div>
              <span className="font-display text-2xl font-extrabold tracking-tight text-white">
                PRIME<span className="text-lemongrass">VECTOR</span>
              </span>
            </div>
            <p className="text-sm text-white/70 max-w-sm leading-relaxed">
              The high-speed AI platform for voice security & deepfake detection. Turning raw audio into structured, verified authenticity records — in under 50 milliseconds.
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-white/5 border border-white/10 text-xs font-mono text-lemongrass">
                <Sparkles size={12} /> Dhwani 2 Engine
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-white/5 border border-white/10 text-xs font-mono text-white/80">
                <Lock size={12} className="text-emerald-400" /> RAM-Only Zero Retention
              </span>
            </div>
          </div>

          {/* Nav Column 1 */}
          <div className="md:col-span-3 space-y-3">
            <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-lemongrass">
              Platform & Tools
            </h4>
            <ul className="space-y-2.5 text-sm text-white/80">
              <li>
                <button onClick={() => setActiveTab('home')} className="hover:text-lemongrass transition-colors">
                  Overview
                </button>
              </li>
              <li>
                <button onClick={() => setActiveTab('detect')} className="hover:text-lemongrass transition-colors flex items-center gap-1">
                  Audio Detector <ArrowUpRight size={13} className="opacity-60" />
                </button>
              </li>
              <li>
                <button onClick={() => setActiveTab('docs')} className="hover:text-lemongrass transition-colors">
                  API Keys & Endpoints
                </button>
              </li>
              <li>
                <button onClick={() => setActiveTab('pricing')} className="hover:text-lemongrass transition-colors">
                  Pay-As-You-Go Pricing
                </button>
              </li>
            </ul>
          </div>

          {/* Nav Column 2 */}
          <div className="md:col-span-4 space-y-3">
            <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-lemongrass">
              Engine Invariants
            </h4>
            <ul className="space-y-2 text-xs font-mono text-white/70">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-lemongrass" />
                P99 Latency &lt; 50ms (Optimized C++ & ONNX Run-Time)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-lemongrass" />
                Dhwani 2 LFCC Phase-Consistency Extraction
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-lemongrass" />
                Multi-Tenant Metered Usage & API Rate Limiting
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-lemongrass" />
                Zero Audio File Persistence on Disk
              </li>
            </ul>
          </div>

        </div>

        {/* Footer Bottom */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-white/50">
          <p>© 2026 PrimeVector Platform. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <span>Powered by Dhwani 2 Model Architecture</span>
            <span>•</span>
            <span className="text-lemongrass">Ayush Rathore</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
