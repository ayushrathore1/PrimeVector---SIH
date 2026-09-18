import React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, ShieldAlert, HelpCircle, Clock, Cpu, Zap, Sparkles } from 'lucide-react';

export default function DetectionResult({ result }) {
  if (!result) return null;

  const { verdict, spoof_score, confidence, latency_ms, model_version, raw_logit } = result;

  const isReal = verdict === 'real';
  const isFake = verdict === 'fake';
  const isUncertain = verdict === 'uncertain';

  const scorePct = Math.round(spoof_score * 100);
  const confPct = Math.round(confidence * 100);

  // Verdict style matching Spade
  const colors = isReal
    ? { 
        primary: '#059669', 
        bg: 'bg-emerald-50', 
        border: 'border-emerald-200', 
        text: 'text-emerald-900',
        badgeBg: 'bg-emerald-100',
        badgeText: 'text-emerald-800',
        ring: '#059669'
      }
    : isFake
    ? { 
        primary: '#E11D48', 
        bg: 'bg-rose-50', 
        border: 'border-rose-200', 
        text: 'text-rose-900',
        badgeBg: 'bg-rose-100',
        badgeText: 'text-rose-800',
        ring: '#E11D48'
      }
    : { 
        primary: '#D97706', 
        bg: 'bg-amber-50', 
        border: 'border-amber-200', 
        text: 'text-amber-900',
        badgeBg: 'bg-amber-100',
        badgeText: 'text-amber-800',
        ring: '#D97706'
      };

  const circumference = 2 * Math.PI * 70;
  const strokeOffset = circumference * (1 - spoof_score);

  const VerdictIcon = isReal ? ShieldCheck : isFake ? ShieldAlert : HelpCircle;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className={`rounded-2xl border p-8 space-y-6 spade-cut-md shadow-spade ${colors.bg} ${colors.border}`}
    >
      <div className="flex flex-col lg:flex-row items-center gap-8">
        
        {/* Gauge Ring */}
        <div className="relative flex-shrink-0">
          <svg className="w-40 h-40 -rotate-90 relative z-10" viewBox="0 0 160 160">
            <circle
              cx="80" cy="80" r="70"
              fill="none"
              stroke="rgba(24, 40, 14, 0.1)"
              strokeWidth="8"
            />
            <motion.circle
              cx="80" cy="80" r="70"
              fill="none"
              stroke={colors.primary}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: strokeOffset }}
              transition={{ duration: 1.2, ease: 'easeOut', delay: 0.2 }}
            />
          </svg>

          {/* Center Score Text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center z-20">
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="text-3xl font-display font-extrabold"
              style={{ color: colors.primary }}
            >
              {scorePct}%
            </motion.span>
            <span className="text-[10px] font-mono text-forest/70 uppercase font-semibold tracking-wider">
              Spoof Score
            </span>
          </div>
        </div>

        {/* Verdict & Details */}
        <div className="flex-1 space-y-5 text-center lg:text-left">
          
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="flex flex-col lg:flex-row items-center gap-4"
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colors.badgeBg} ${colors.badgeText} border ${colors.border}`}>
              <VerdictIcon className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center justify-center lg:justify-start gap-2">
                <h3 className={`font-display text-2xl font-extrabold ${colors.text}`}>
                  {isReal ? 'AUTHENTIC VOICE' : isFake ? 'SYNTHETIC / AI DEEPFAKE' : 'INCONCLUSIVE'}
                </h3>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase ${colors.badgeBg} ${colors.badgeText}`}>
                  {verdict}
                </span>
              </div>
              <p className="text-xs font-mono text-forest/70 mt-1">
                {isReal
                  ? 'High spectral & phase consistency. Speech verified as authentic human.'
                  : isFake
                  ? 'Acoustic anomalies detected. High likelihood of AI voice cloning.'
                  : 'Acoustic feature scores are ambiguous. Additional sample recommended.'}
              </p>
            </div>
          </motion.div>

          {/* Metrics Grid */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2"
          >
            <div className="p-3.5 rounded-xl bg-white/80 border border-forest/10 shadow-sm">
              <div className="text-[10px] font-mono text-forest/60 uppercase font-semibold">Confidence</div>
              <div className="text-lg font-extrabold font-mono text-forest mt-0.5">{confPct}%</div>
              <div className="mt-1.5 h-1.5 rounded-full bg-forest/10 overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: colors.primary }}
                  initial={{ width: 0 }}
                  animate={{ width: `${confPct}%` }}
                  transition={{ duration: 0.8, delay: 0.5 }}
                />
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-white/80 border border-forest/10 shadow-sm">
              <div className="text-[10px] font-mono text-forest/60 uppercase font-semibold flex items-center gap-1">
                <Clock size={11} /> P99 Latency
              </div>
              <div className="text-lg font-extrabold font-mono text-emerald-700 mt-0.5">{latency_ms} ms</div>
            </div>

            <div className="p-3.5 rounded-xl bg-white/80 border border-forest/10 shadow-sm">
              <div className="text-[10px] font-mono text-forest/60 uppercase font-semibold flex items-center gap-1">
                <Zap size={11} /> Raw Logit
              </div>
              <div className="text-lg font-extrabold font-mono text-forest mt-0.5">{raw_logit?.toFixed(3)}</div>
            </div>

            <div className="p-3.5 rounded-xl bg-white/80 border border-forest/10 shadow-sm">
              <div className="text-[10px] font-mono text-forest/60 uppercase font-semibold flex items-center gap-1">
                <Cpu size={11} /> Model Engine
              </div>
              <div className="text-xs font-bold font-mono text-forest truncate mt-1">
                {model_version || 'Dhwani-v2'}
              </div>
            </div>
          </motion.div>

        </div>
      </div>
    </motion.div>
  );
}
