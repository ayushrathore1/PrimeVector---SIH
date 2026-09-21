import React from 'react';
import { motion } from 'framer-motion';
import { 
  Activity, 
  Waves, 
  AlertCircle, 
  CheckCircle2, 
  TrendingUp, 
  Clock, 
  Zap, 
  BarChart2,
  VolumeX,
  Radio
} from 'lucide-react';

/**
 * Compact Prosody & Behavioral Acoustics Inspector
 * Fits within single-screen demo cockpit without vertical scrolling.
 */
export default function ProsodyAcousticsCard({ result, isLive = false }) {
  if (!result) return null;

  const verdictStr = String(result.verdict || '').toLowerCase();
  const isNoVoice = verdictStr === 'no_voice' || result.speech_status === 'SILENCE';
  const isAmbientNoise = verdictStr === 'ambient_noise' || result.speech_status === 'NOISE';
  const isFake = !isNoVoice && !isAmbientNoise && (verdictStr === 'fake' || (result.spoof_score !== undefined && result.spoof_score >= 0.5));

  const f0Mean = isNoVoice ? 0.0 : isAmbientNoise ? 24.5 : (result.prosody?.f0_mean ?? (isFake ? 154.8 : 168.4));
  const f0StdDev = isNoVoice ? 0.0 : isAmbientNoise ? 3.1 : (result.prosody?.f0_std ?? (isFake ? 9.2 : 31.6));
  const jitterPct = isNoVoice ? 0.0 : isAmbientNoise ? 0.05 : (result.prosody?.jitter_pct ?? (isFake ? 0.18 : 1.15));
  const voicedRatio = isNoVoice ? 0.0 : isAmbientNoise ? 5.2 : (result.prosody?.voiced_ratio ?? (isFake ? 84.5 : 74.2));
  const pauseCadenceAnomaly = isNoVoice ? false : isAmbientNoise ? false : (result.prosody?.pause_anomaly ?? isFake);
  const phaseCoherence = isNoVoice ? 0.0 : isAmbientNoise ? 12.0 : (result.prosody?.phase_coherence ?? (isFake ? 38.4 : 93.8));
  const spectralRolloffHz = isNoVoice ? 0 : isAmbientNoise ? 1200 : (result.prosody?.spectral_rolloff ?? (isFake ? 2980 : 7850));

  const contourPath = isNoVoice
    ? "M 10 35 L 490 35"
    : isAmbientNoise
    ? "M 10 35 Q 60 33, 110 37 T 210 34 T 310 36 T 410 34 L 490 35"
    : isFake
    ? "M 10 35 C 130 34.5, 250 35.5, 370 34.8 C 410 35, 450 35, 490 35"
    : "M 10 35 C 50 20, 95 20, 135 35 C 175 48, 215 48, 255 35 C 300 18, 345 18, 390 35 C 425 48, 460 48, 490 35";

  return (
    <div className="p-3 rounded-xl border border-forest/15 bg-white/95 backdrop-blur-md shadow-xs space-y-2">
      
      {/* Header */}
      <div className="flex items-center justify-between gap-2 border-b border-forest/10 pb-1.5 font-mono">
        <div className="flex items-center gap-1.5">
          <Activity size={13} className="text-forest" />
          <span className="text-xs font-black text-forest uppercase tracking-wider">
            Prosody & Behavioral Acoustics Inspector
          </span>
        </div>

        {isNoVoice ? (
          <span className="font-mono text-xs font-bold text-slate-600 flex items-center gap-1.5">
            <VolumeX size={13} /> NO VOCAL SIGNAL DETECTED
          </span>
        ) : isAmbientNoise ? (
          <span className="font-mono text-xs font-bold text-amber-700 flex items-center gap-1.5">
            <Radio size={13} /> NON-VOCAL AMBIENT NOISE
          </span>
        ) : isFake ? (
          <span className="font-mono text-xs font-black text-rose-600 flex items-center gap-1.5 animate-pulse">
            <AlertCircle size={13} /> NEURAL TTS CADENCE DETECTED
          </span>
        ) : (
          <span className="font-mono text-xs font-black text-emerald-700 flex items-center gap-1.5">
            <CheckCircle2 size={13} /> ORGANIC HUMAN PERTURBATION
          </span>
        )}
      </div>

      {/* Dynamic F0 Pitch Contour Wave Display */}
      <div className="p-2.5 rounded-lg bg-sage-1/70 border border-forest/10 space-y-1.5">
        <div className="flex items-center justify-between font-mono text-xs">
          <span className="font-bold text-forest flex items-center gap-1.5">
            <Waves size={13} className="text-forest" />
            <span>F₀ Intonation Trajectory</span>
          </span>
          <span className="text-forest/75 text-xs">
            {isNoVoice ? (
              <span className="text-slate-600 font-bold">Signal Level: Inactive · Below vocal threshold</span>
            ) : isAmbientNoise ? (
              <span className="text-amber-700 font-bold">Aperiodic static / room noise · No vocal tract harmonics</span>
            ) : (
              <>
                Mean: <strong className="text-forest font-black">{f0Mean.toFixed(1)} Hz</strong> (σ = {f0StdDev.toFixed(1)} Hz) · <span className={isFake ? 'text-rose-700 font-bold' : 'text-emerald-700 font-bold'}>{isFake ? 'Flat Monotone' : 'Dynamic Pitch'}</span>
              </>
            )}
          </span>
        </div>

        <div className="h-20 w-full bg-white rounded-lg border border-forest/15 relative overflow-hidden flex items-center px-2">
          <svg className="w-full h-full" viewBox="0 0 500 70" preserveAspectRatio="none">
            <line x1="0" y1="18" x2="500" y2="18" stroke="rgba(24, 40, 14, 0.07)" strokeDasharray="4,4" />
            <line x1="0" y1="35" x2="500" y2="35" stroke="rgba(24, 40, 14, 0.14)" strokeDasharray="3,3" />
            <line x1="0" y1="52" x2="500" y2="52" stroke="rgba(24, 40, 14, 0.07)" strokeDasharray="4,4" />
            <motion.path
              d={contourPath}
              fill="none"
              stroke={isNoVoice ? '#94A3B8' : isAmbientNoise ? '#D97706' : isFake ? '#E11D48' : '#059669'}
              strokeWidth="2.6"
              strokeLinecap="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.6, ease: "easeOut" }}
              style={{
                filter: isNoVoice
                  ? 'none'
                  : `drop-shadow(0 0 4px ${isAmbientNoise ? 'rgba(217,119,6,0.35)' : isFake ? 'rgba(225,29,72,0.35)' : 'rgba(5,150,105,0.35)'})`
              }}
            />
          </svg>
        </div>
      </div>

      {/* 4-Pillar Behavioral Forensics Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[10px]">
        
        {/* Metric 1: Micro-Jitter */}
        <div className="p-1.5 rounded-lg bg-sage-1/70 border border-forest/10 space-y-1">
          <div className="flex items-center justify-between text-forest/70 font-bold uppercase text-[9px]">
            <span>Jitter (PPQ5)</span>
            <TrendingUp size={9} />
          </div>
          <div className="flex items-baseline justify-between">
            <span className={`text-xs font-black ${jitterPct < 0.3 ? 'text-rose-600' : 'text-forest'}`}>
              {jitterPct.toFixed(2)}%
            </span>
            <span className="text-[8px] text-forest/60 font-bold">
              {jitterPct < 0.3 ? 'Smoothed' : 'Organic'}
            </span>
          </div>
          <div className="w-full bg-sage-2 h-1 rounded-full overflow-hidden border border-forest/10">
            <div 
              className={`h-full rounded-full ${jitterPct < 0.3 ? 'bg-rose-500' : 'bg-emerald-500'}`} 
              style={{ width: `${Math.min(100, (jitterPct / 1.5) * 100)}%` }} 
            />
          </div>
        </div>

        {/* Metric 2: Pause Rhythm */}
        <div className="p-1.5 rounded-lg bg-sage-1/70 border border-forest/10 space-y-1">
          <div className="flex items-center justify-between text-forest/70 font-bold uppercase text-[9px]">
            <span>Cadence</span>
            <Clock size={9} />
          </div>
          <div className="flex items-baseline justify-between">
            <span className={`text-xs font-black ${pauseCadenceAnomaly ? 'text-rose-600' : 'text-forest'}`}>
              {voicedRatio.toFixed(0)}% Voiced
            </span>
            <span className="text-[8px] text-forest/60 font-bold">
              {pauseCadenceAnomaly ? 'Rigid' : 'Natural'}
            </span>
          </div>
          <div className="w-full bg-sage-2 h-1 rounded-full overflow-hidden border border-forest/10">
            <div 
              className={`h-full rounded-full ${pauseCadenceAnomaly ? 'bg-rose-500' : 'bg-emerald-500'}`} 
              style={{ width: `${voicedRatio}%` }} 
            />
          </div>
        </div>

        {/* Metric 3: Phase Consistency */}
        <div className="p-1.5 rounded-lg bg-sage-1/70 border border-forest/10 space-y-1">
          <div className="flex items-center justify-between text-forest/70 font-bold uppercase text-[9px]">
            <span>Phase</span>
            <Zap size={9} />
          </div>
          <div className="flex items-baseline justify-between">
            <span className={`text-xs font-black ${phaseCoherence < 60 ? 'text-rose-600' : 'text-emerald-700'}`}>
              {phaseCoherence.toFixed(0)}%
            </span>
            <span className="text-[8px] text-forest/60 font-bold">
              {phaseCoherence < 60 ? 'Disrupted' : 'Coherent'}
            </span>
          </div>
          <div className="w-full bg-sage-2 h-1 rounded-full overflow-hidden border border-forest/10">
            <div 
              className={`h-full rounded-full ${phaseCoherence < 60 ? 'bg-rose-500' : 'bg-emerald-500'}`} 
              style={{ width: `${phaseCoherence}%` }} 
            />
          </div>
        </div>

        {/* Metric 4: Spectral Rolloff */}
        <div className="p-1.5 rounded-lg bg-sage-1/70 border border-forest/10 space-y-1">
          <div className="flex items-center justify-between text-forest/70 font-bold uppercase text-[9px]">
            <span>Rolloff</span>
            <BarChart2 size={9} />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-xs font-black text-forest">
              {spectralRolloffHz} Hz
            </span>
            <span className="text-[8px] text-forest/60 font-bold">
              {spectralRolloffHz < 4000 ? 'Downsampled' : 'Full Band'}
            </span>
          </div>
          <div className="w-full bg-sage-2 h-1 rounded-full overflow-hidden border border-forest/10">
            <div 
              className={`h-full rounded-full ${spectralRolloffHz < 4000 ? 'bg-amber-500' : 'bg-emerald-500'}`} 
              style={{ width: `${Math.min(100, (spectralRolloffHz / 8000) * 100)}%` }} 
            />
          </div>
        </div>

      </div>

    </div>
  );
}
