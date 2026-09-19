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
    <div className="rounded-2xl border border-forest/15 bg-sage-1 p-6 sm:p-8 shadow-spade spade-cut-md my-8">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 mb-6 border-b border-forest/10 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-forest text-lemongrass shadow-sm">
              <Sliders size={16} />
            </span>
            <h3 className="font-display text-xl font-extrabold text-forest">Interactive 3-Signal Evidence Fusion Engine</h3>
          </div>
          <p className="text-xs text-forest/70 font-mono mt-1">
            Drag the signal sliders to evaluate live Noisy-OR probability formulation & action thresholds
          </p>
        </div>

        <div className="flex items-center gap-3 bg-white px-4 py-2 rounded-xl border border-forest/15 font-mono shadow-sm">
          <span className="text-xs text-forest/70 font-bold">Fused Score:</span>
          <span className="text-xl font-extrabold text-forest">{finalRiskScore.toFixed(3)}</span>
          <RiskBadge score={finalRiskScore} />
        </div>
      </div>

      {/* 3 Input Signals */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Signal 1 */}
        <div className="p-5 rounded-xl bg-white border border-forest/15 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-700" />
              <span className="font-mono text-xs font-bold text-forest uppercase">1. Voice Authenticity</span>
            </div>
            <span className="font-mono text-xs text-forest font-extrabold">{synthesisScore.toFixed(2)}</span>
          </div>
          <p className="text-[11px] text-forest/70 leading-normal">Acoustic spectral glitch & synthetic artifact scoring</p>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={synthesisScore}
            onChange={(e) => setSynthesisScore(parseFloat(e.target.value))}
            className="w-full accent-forest cursor-pointer"
          />
          <div className="flex justify-between text-[10px] font-mono text-forest/60">
            <span>Clean Acoustic</span>
            <span>AI Synthetic</span>
          </div>
        </div>

        {/* Signal 2 */}
        <div className="p-5 rounded-xl bg-white border border-forest/15 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Mic className="w-4 h-4 text-teal-700" />
              <span className="font-mono text-xs font-bold text-forest uppercase">2. Speaker Match</span>
            </div>
            <span className="font-mono text-xs text-forest font-extrabold">{speakerScore.toFixed(2)}</span>
          </div>
          <p className="text-[11px] text-forest/70 leading-normal">Resemblyzer embedding mismatch score (1 - similarity)</p>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={speakerScore}
            onChange={(e) => setSpeakerScore(parseFloat(e.target.value))}
            className="w-full accent-forest cursor-pointer"
          />
          <div className="flex justify-between text-[10px] font-mono text-forest/60">
            <span>Enrolled Match</span>
            <span>Voice Mismatch</span>
          </div>
        </div>

        {/* Signal 3 */}
        <div className="p-5 rounded-xl bg-white border border-forest/15 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-purple-700" />
              <span className="font-mono text-xs font-bold text-forest uppercase">3. Content Risk</span>
            </div>
            <span className="font-mono text-xs text-forest font-extrabold">{contentScore.toFixed(2)}</span>
          </div>
          <p className="text-[11px] text-forest/70 leading-normal">Local Ollama LLM transcript scam & urgency pattern scan</p>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={contentScore}
            onChange={(e) => setContentScore(parseFloat(e.target.value))}
            className="w-full accent-forest cursor-pointer"
          />
          <div className="flex justify-between text-[10px] font-mono text-forest/60">
            <span>Normal Speech</span>
            <span>Scam Keywords</span>
          </div>
        </div>
      </div>

      {/* Fusion Math & Context Box */}
      <div className="p-6 rounded-xl bg-forest text-white border border-forest-dark font-mono text-xs shadow-spade">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="text-lemongrass uppercase font-bold mb-2 text-[11px] tracking-wider">
              Noisy-OR Formula Computation
            </div>
            <div className="bg-forest-dark p-3.5 rounded-lg border border-white/10 text-sage-1 space-y-1 text-[11px]">
              <div>P(suspicious) = 1 - ∏(1 - s_i)</div>
              <div>P(suspicious) = 1 - ((1 - {synthesisScore}) × (1 - {speakerScore}) × (1 - {contentScore}))</div>
              <div className="text-lemongrass font-bold pt-1">
                = {pSuspicious.toFixed(4)} (Raw Acoustic + Content Threat)
              </div>
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1 text-[11px]">
              <span className="text-white/80 uppercase font-bold">Contextual Bounded Multiplier</span>
              <span className="text-lemongrass font-bold">{multiplier.toFixed(2)}x (Range: 0.85x - 1.35x)</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={contextScore}
              onChange={(e) => setContextScore(parseFloat(e.target.value))}
              className="w-full accent-lemongrass cursor-pointer my-2"
            />
            <p className="text-[10px] text-white/70 leading-normal">
              Transaction amount, device risk, and new beneficiary status map onto a strictly bounded scalar. Context alone cannot falsely accuse clean voice.
            </p>
          </div>
        </div>

        {/* Output Action Bar */}
        <div className="mt-6 pt-4 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-lemongrass" />
            <span className="text-white/80 font-bold">Recommended System Action:</span>
          </div>
          <div className="px-4 py-2 rounded-lg bg-lemongrass text-forest font-extrabold text-xs tracking-wide shadow-sm">
            <span>{recommendedAction}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

