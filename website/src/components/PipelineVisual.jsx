import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mic, Activity, ShieldCheck, Zap, Brain, Sliders, ArrowRight, Lock } from 'lucide-react';
import RiskBadge from './RiskBadge';

export default function PipelineVisual() {
  const [synthesisScore, setSynthesisScore] = useState(0.85);
  const [speakerScore, setSpeakerScore] = useState(0.72);
  const [contentScore, setContentScore] = useState(0.65);
  const [contextScore, setContextScore] = useState(0.50);

  // Compute Noisy-OR formula: P = 1 - (1-s1)*(1-s2)*(1-s3)
  const pSuspicious = 1 - (1 - synthesisScore) * (1 - speakerScore) * (1 - contentScore);
  // Multiplier formula: 0.85 + contextScore * (1.35 - 0.85)
  const multiplier = 0.85 + contextScore * (1.35 - 0.85);
  // Final score bounded to 1.0
  const finalRiskScore = Math.min(1.0, pSuspicious * multiplier);

  let recommendedAction = 'PROCEED';
  if (finalRiskScore >= 0.70) {
    recommendedAction = 'RECOMMEND_SUPERVISOR_ESCALATION & CALLBACK';
  } else if (finalRiskScore >= 0.40) {
    recommendedAction = 'RECOMMEND_CALLBACK_VERIFICATION';
  }

  return (
    <div className="rounded-xl border border-obsidian-700 bg-obsidian-900 p-6 shadow-card-glow my-8">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 mb-6 border-b border-obsidian-700/80 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-forensic-amber/10 border border-forensic-amber/30 text-forensic-amber">
              <Sliders size={16} />
            </span>
            <h3 className="font-serif text-xl font-bold text-white">Interactive 3-Signal Evidence Fusion Engine</h3>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Drag the signal values to evaluate the live Noisy-OR probability formulation & action thresholds
          </p>
        </div>

        <div className="flex items-center gap-3 bg-obsidian-850 px-4 py-2 rounded-lg border border-obsidian-700 font-mono">
          <span className="text-xs text-slate-400">Fused Score:</span>
          <span className="text-xl font-bold text-white">{finalRiskScore.toFixed(3)}</span>
          <RiskBadge score={finalRiskScore} />
        </div>
      </div>

      {/* 3 Input Signals */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Signal 1 */}
        <div className="p-4 rounded-lg bg-obsidian-850 border border-obsidian-700/80">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-forensic-amber" />
              <span className="font-mono text-xs font-semibold text-slate-200 uppercase">1. Voice Authenticity</span>
            </div>
            <span className="font-mono text-xs text-forensic-amber font-bold">{synthesisScore.toFixed(2)}</span>
          </div>
          <p className="text-[11px] text-slate-400 mb-3">Acoustic spectral glitch & synthetic artifact scoring</p>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={synthesisScore}
            onChange={(e) => setSynthesisScore(parseFloat(e.target.value))}
            className="w-full accent-forensic-amber cursor-pointer"
          />
          <div className="flex justify-between text-[10px] font-mono text-slate-400 mt-1">
            <span>Clean Acoustic</span>
            <span>AI Synthetic</span>
          </div>
        </div>

        {/* Signal 2 */}
        <div className="p-4 rounded-lg bg-obsidian-850 border border-obsidian-700/80">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Mic className="w-4 h-4 text-cyan-400" />
              <span className="font-mono text-xs font-semibold text-slate-200 uppercase">2. Speaker Match</span>
            </div>
            <span className="font-mono text-xs text-cyan-400 font-bold">{speakerScore.toFixed(2)}</span>
          </div>
          <p className="text-[11px] text-slate-400 mb-3">Resemblyzer embedding mismatch score (1 - similarity)</p>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={speakerScore}
            onChange={(e) => setSpeakerScore(parseFloat(e.target.value))}
            className="w-full accent-cyan-400 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] font-mono text-slate-400 mt-1">
            <span>Enrolled Voice Match</span>
            <span>Voice Mismatch</span>
          </div>
        </div>

        {/* Signal 3 */}
        <div className="p-4 rounded-lg bg-obsidian-850 border border-obsidian-700/80">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-purple-400" />
              <span className="font-mono text-xs font-semibold text-slate-200 uppercase">3. Content Risk</span>
            </div>
            <span className="font-mono text-xs text-purple-400 font-bold">{contentScore.toFixed(2)}</span>
          </div>
          <p className="text-[11px] text-slate-400 mb-3">Groq LLM transcript scam & urgency pattern scan</p>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={contentScore}
            onChange={(e) => setContentScore(parseFloat(e.target.value))}
            className="w-full accent-purple-400 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] font-mono text-slate-400 mt-1">
            <span>Normal Speech</span>
            <span>Scam Keywords</span>
          </div>
        </div>
      </div>

      {/* Fusion Math & Context Box */}
      <div className="p-5 rounded-lg bg-obsidian-950 border border-obsidian-700 font-mono text-xs">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="text-slate-400 uppercase font-semibold mb-2 text-[11px]">
              Noisy-OR Formula Computation
            </div>
            <div className="bg-obsidian-900 p-3 rounded border border-obsidian-800 text-slate-300 space-y-1 text-[11px]">
              <div>P(suspicious) = 1 - ∏(1 - s_i)</div>
              <div>P(suspicious) = 1 - ((1 - {synthesisScore}) × (1 - {speakerScore}) × (1 - {contentScore}))</div>
              <div className="text-forensic-amber font-bold pt-1">
                = {pSuspicious.toFixed(4)} (Raw Acoustic + Content Threat)
              </div>
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1 text-[11px]">
              <span className="text-slate-400 uppercase font-semibold">Contextual Bounded Multiplier</span>
              <span className="text-slate-300 font-bold">{multiplier.toFixed(2)}x (Range: 0.85x - 1.35x)</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={contextScore}
              onChange={(e) => setContextScore(parseFloat(e.target.value))}
              className="w-full accent-emerald-400 cursor-pointer my-2"
            />
            <p className="text-[10px] text-slate-400">
              Transaction amount, device risk, and new beneficiary status map onto a strictly bounded scalar. Context alone cannot falsely accuse clean voice.
            </p>
          </div>
        </div>

        {/* Output Action Bar */}
        <div className="mt-5 pt-4 border-t border-obsidian-800 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-forensic-amber" />
            <span className="text-slate-400">Recommended System Action:</span>
          </div>
          <div className="px-4 py-2 rounded bg-obsidian-900 border border-obsidian-700 text-white font-bold text-xs tracking-wide flex items-center gap-2">
            <span className="text-forensic-amber">{recommendedAction}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
