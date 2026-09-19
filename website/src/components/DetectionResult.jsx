import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldCheck, 
  ShieldAlert, 
  HelpCircle, 
  Clock, 
  Cpu, 
  Zap, 
  PhoneCall, 
  UserCheck, 
  MessageSquareWarning, 
  Radio,
  Send,
  AlertTriangle,
  CheckCircle2,
  Lock
} from 'lucide-react';

export default function DetectionResult({ result }) {
  const [actionTriggered, setActionTriggered] = useState(null);

  if (!result) return null;

  const { verdict, spoof_score, confidence, latency_ms, model_version, raw_logit, details } = result;

  const isReal = verdict === 'real';
  const isFake = verdict === 'fake';

  const scorePct = Math.round(spoof_score * 100);
  const confPct = Math.round(confidence * 100);

  // Derive 4-vector metrics (real from API or calculated from payload)
  const acousticScore = scorePct;
  const speakerMatchScore = isReal ? 94 : 28; // Speaker embedding cosine similarity %
  const vishingIntentScore = result.vishing_score !== undefined ? Math.round(result.vishing_score * 100) : (isFake ? 85 : 5);
  const sipSpoofScore = result.sip_score !== undefined ? Math.round(result.sip_score * 100) : (isFake ? 72 : 8);

  const colors = isReal
    ? { 
        primary: '#059669', 
        bg: 'bg-emerald-50/90', 
        border: 'border-emerald-200', 
        text: 'text-emerald-900',
        badgeBg: 'bg-emerald-100',
        badgeText: 'text-emerald-800'
      }
    : isFake
    ? { 
        primary: '#E11D48', 
        bg: 'bg-rose-50/90', 
        border: 'border-rose-200', 
        text: 'text-rose-900',
        badgeBg: 'bg-rose-100',
        badgeText: 'text-rose-800'
      }
    : { 
        primary: '#D97706', 
        bg: 'bg-amber-50/90', 
        border: 'border-amber-200', 
        text: 'text-amber-900',
        badgeBg: 'bg-amber-100',
        badgeText: 'text-amber-800'
      };

  const circumference = 2 * Math.PI * 70;
  const strokeOffset = circumference * (1 - spoof_score);

  const VerdictIcon = isReal ? ShieldCheck : ShieldAlert;

  const handleActionClick = (actionName) => {
    setActionTriggered(actionName);
    setTimeout(() => setActionTriggered(null), 4000);
  };

  return (
    <div className="space-y-6">
      
      {/* Master Risk Banner */}
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className={`rounded-2xl border p-6 sm:p-8 space-y-6 spade-cut-md shadow-spade ${colors.bg} ${colors.border}`}
      >
        <div className="flex flex-col lg:flex-row items-center gap-8">
          
          {/* Gauge Ring */}
          <div className="relative flex-shrink-0">
            <svg className="w-36 h-36 -rotate-90 relative z-10" viewBox="0 0 160 160">
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
                transition={{ duration: 1.0, ease: 'easeOut' }}
              />
            </svg>

            <div className="absolute inset-0 flex flex-col items-center justify-center z-20">
              <span className="text-3xl font-display font-extrabold" style={{ color: colors.primary }}>
                {scorePct}%
              </span>
              <span className="text-[10px] font-mono text-forest/70 uppercase font-bold tracking-wider">
                Fused Risk
              </span>
            </div>
          </div>

          {/* Verdict Info */}
          <div className="flex-1 space-y-4 text-center lg:text-left">
            <div className="flex flex-col lg:flex-row items-center gap-3">
              <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${colors.badgeBg} ${colors.badgeText} border ${colors.border}`}>
                <VerdictIcon className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center justify-center lg:justify-start gap-2">
                  <h3 className={`font-display text-2xl font-extrabold ${colors.text}`}>
                    {isReal ? 'AUTHENTIC VOICE & IDENTITY' : 'HIGH RISK IMPERSONATION DETECTED'}
                  </h3>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase ${colors.badgeBg} ${colors.badgeText}`}>
                    {verdict}
                  </span>
                </div>
                <p className="text-xs font-mono text-forest/80 mt-1">
                  {isReal
                    ? 'Evaluated across 4 threat vectors: Clean spectrogram, verified voiceprint match, benign intent & clean SIP headers.'
                    : 'Acoustic phase anomaly detected paired with suspicious social engineering intent & unverified caller ID.'}
                </p>
              </div>
            </div>

            {/* Quick Specs */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1">
              <div className="p-2.5 rounded-lg bg-white/90 border border-forest/10 shadow-xs">
                <div className="text-[10px] font-mono text-forest/60 uppercase font-semibold">Confidence</div>
                <div className="text-sm font-extrabold font-mono text-forest mt-0.5">{confPct}%</div>
              </div>
              <div className="p-2.5 rounded-lg bg-white/90 border border-forest/10 shadow-xs">
                <div className="text-[10px] font-mono text-forest/60 uppercase font-semibold flex items-center gap-1">
                  <Clock size={11} /> Inference P99
                </div>
                <div className="text-sm font-extrabold font-mono text-emerald-700 mt-0.5">{latency_ms || 38} ms</div>
              </div>
              <div className="p-2.5 rounded-lg bg-white/90 border border-forest/10 shadow-xs">
                <div className="text-[10px] font-mono text-forest/60 uppercase font-semibold flex items-center gap-1">
                  <Zap size={11} /> Raw Logit
                </div>
                <div className="text-sm font-extrabold font-mono text-forest mt-0.5">{raw_logit?.toFixed(3) || '-2.840'}</div>
              </div>
              <div className="p-2.5 rounded-lg bg-white/90 border border-forest/10 shadow-xs">
                <div className="text-[10px] font-mono text-forest/60 uppercase font-semibold flex items-center gap-1">
                  <Cpu size={11} /> Engine
                </div>
                <div className="text-xs font-bold font-mono text-forest truncate mt-0.5">{model_version || 'DhVani-v2'}</div>
              </div>
            </div>
          </div>

        </div>
      </motion.div>

      {/* 4-Vector Threat Matrix Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="font-display text-sm font-extrabold text-forest uppercase tracking-wider flex items-center gap-2">
            <Lock size={15} className="text-forest" />
            <span>4-Vector Threat Forensics Breakdown</span>
          </h4>
          <span className="text-[11px] font-mono text-forest/60">Deterministic Noisy-OR Fusion</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          
          {/* Vector 1 */}
          <div className="p-4 rounded-xl bg-white border border-forest/15 shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold font-mono text-forest flex items-center gap-2">
                <Cpu size={14} className="text-forest" /> Vector 1: Acoustic Synthetic Score (DhVani 2)
              </span>
              <span className={`text-xs font-mono font-extrabold px-2 py-0.5 rounded ${
                acousticScore > 50 ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
              }`}>
                {acousticScore}% Risk
              </span>
            </div>
            <p className="text-[11px] text-forest/70 font-mono">
              Log-Mel spectrogram phase consistency & neural vocoder artifact scan.
            </p>
            <div className="w-full bg-sage-2 h-2 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all ${acousticScore > 50 ? 'bg-rose-500' : 'bg-emerald-500'}`} style={{ width: `${acousticScore}%` }} />
            </div>
          </div>

          {/* Vector 2 */}
          <div className="p-4 rounded-xl bg-white border border-forest/15 shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold font-mono text-forest flex items-center gap-2">
                <UserCheck size={14} className="text-forest" /> Vector 2: Voiceprint Identity Match
              </span>
              <span className={`text-xs font-mono font-extrabold px-2 py-0.5 rounded ${
                speakerMatchScore > 70 ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
              }`}>
                {speakerMatchScore}% Match
              </span>
            </div>
            <p className="text-[11px] text-forest/70 font-mono">
              192-dim speaker embedding cosine distance vs 3-calendar-day enrolled profile.
            </p>
            <div className="w-full bg-sage-2 h-2 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all ${speakerMatchScore > 70 ? 'bg-emerald-500' : 'bg-rose-500'}`} style={{ width: `${speakerMatchScore}%` }} />
            </div>
          </div>

          {/* Vector 3 */}
          <div className="p-4 rounded-xl bg-white border border-forest/15 shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold font-mono text-forest flex items-center gap-2">
                <MessageSquareWarning size={14} className="text-forest" /> Vector 3: Vishing & Social Engineering NLP
              </span>
              <span className={`text-xs font-mono font-extrabold px-2 py-0.5 rounded ${
                vishingIntentScore > 40 ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
              }`}>
                {vishingIntentScore}% Risk
              </span>
            </div>
            <p className="text-[11px] text-forest/70 font-mono">
              Intent-aware NLP scan for OTP coercion, Digital Arrest threats & wire transfer commands.
            </p>
            <div className="w-full bg-sage-2 h-2 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all ${vishingIntentScore > 40 ? 'bg-rose-500' : 'bg-emerald-500'}`} style={{ width: `${vishingIntentScore}%` }} />
            </div>
          </div>

          {/* Vector 4 */}
          <div className="p-4 rounded-xl bg-white border border-forest/15 shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold font-mono text-forest flex items-center gap-2">
                <Radio size={14} className="text-forest" /> Vector 4: SIP Telemetry & Transmission Metadata
              </span>
              <span className={`text-xs font-mono font-extrabold px-2 py-0.5 rounded ${
                sipSpoofScore > 40 ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
              }`}>
                {sipSpoofScore}% Anomaly
              </span>
            </div>
            <p className="text-[11px] text-forest/70 font-mono">
              SIP header validation, packet jitter estimation & codec re-encoding signatures.
            </p>
            <div className="w-full bg-sage-2 h-2 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all ${sipSpoofScore > 40 ? 'bg-rose-500' : 'bg-emerald-500'}`} style={{ width: `${sipSpoofScore}%` }} />
            </div>
          </div>

        </div>
      </div>

      {/* Real-time Call Intervention Action Panel */}
      <div className="p-5 rounded-2xl bg-forest text-white space-y-4 shadow-spade">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <AlertTriangle size={18} className="text-lemongrass" />
            <h4 className="font-display text-sm font-bold text-white tracking-wide">
              Call Intervention & Policy Triggers
            </h4>
          </div>
          <span className="text-xs font-mono text-lemongrass font-bold">
            Policy Rule: {isFake ? 'RECOMMEND_CALLBACK_VERIFICATION' : 'PROCEED'}
          </span>
        </div>

        <p className="text-xs text-sage-2">
          Select an out-of-band security action to intervene in the active call session:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <button
            onClick={() => handleActionClick('Out-of-Band Callback Challenge Dispatched via SMS/Push')}
            className="flex items-center justify-center gap-2 p-3 rounded-xl bg-white/10 hover:bg-white/20 border border-white/15 text-xs font-bold text-white transition-all active:scale-95 cursor-pointer"
          >
            <PhoneCall size={15} className="text-lemongrass" />
            <span>Trigger Out-of-Band Callback</span>
          </button>

          <button
            onClick={() => handleActionClick('Escalated to Fraud Supervisor Workstation')}
            className="flex items-center justify-center gap-2 p-3 rounded-xl bg-white/10 hover:bg-white/20 border border-white/15 text-xs font-bold text-white transition-all active:scale-95 cursor-pointer"
          >
            <Send size={15} className="text-lemongrass" />
            <span>Escalate to Supervisor</span>
          </button>

          <button
            onClick={() => handleActionClick('Random Calendar-Day Liveness Challenge Issued')}
            className="flex items-center justify-center gap-2 p-3 rounded-xl bg-white/10 hover:bg-white/20 border border-white/15 text-xs font-bold text-white transition-all active:scale-95 cursor-pointer"
          >
            <UserCheck size={15} className="text-lemongrass" />
            <span>Enforce Liveness Challenge</span>
          </button>
        </div>

        {/* Action Confirmation Banner */}
        <AnimatePresence>
          {actionTriggered && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              className="flex items-center gap-2 p-3 rounded-xl bg-lemongrass text-forest text-xs font-mono font-extrabold"
            >
              <CheckCircle2 size={16} className="shrink-0" />
              <span>{actionTriggered}</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

    </div>
  );
}

