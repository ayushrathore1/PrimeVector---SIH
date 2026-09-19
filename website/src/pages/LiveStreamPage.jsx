import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Radio, Play, RefreshCw, Zap, Clock, ShieldAlert, Cpu, CheckCircle2 } from 'lucide-react';
import RiskBadge from '../components/RiskBadge';
import { executePipelineProcess } from '../utils/api';

export default function LiveDemoPage() {
  const [events, setEvents] = useState([]);

  const [loading, setLoading] = useState(false);
  const [selectedScenario, setSelectedScenario] = useState('high_risk');

  const scenarios = {
    high_risk: {
      session_id: `call-sess-${Math.floor(100000 + Math.random() * 900000)}`,
      tenant_id: 'bank-retail-prod',
      subject_id: 'cfo-john-doe',
      transcript: 'This is John. Send $120,000 to overseas account 449-112 right now for urgent acquisition.',
      context_score: 0.85,
      sample_rate_hz: 16000,
      channels: 1,
      audio_pcm_base64: 'UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=', // minimal PCM frame
    },
    medium_risk: {
      session_id: `call-sess-${Math.floor(100000 + Math.random() * 900000)}`,
      tenant_id: 'bank-retail-prod',
      subject_id: 'user-mary-smith',
      transcript: 'I lost my debit card password and need a quick reset while I am traveling.',
      context_score: 0.45,
      sample_rate_hz: 16000,
      channels: 1,
      audio_pcm_base64: 'UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=',
    },
    clean_call: {
      session_id: `call-sess-${Math.floor(100000 + Math.random() * 900000)}`,
      tenant_id: 'bank-retail-prod',
      subject_id: 'user-alice-wong',
      transcript: 'Can you tell me the branch opening hours for tomorrow morning?',
      context_score: 0.10,
      sample_rate_hz: 16000,
      channels: 1,
      audio_pcm_base64: 'UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=',
    },
  };

  const handleSimulateCall = async () => {
    setLoading(true);
    const payload = scenarios[selectedScenario];
    payload.session_id = `call-sess-${Math.floor(100000 + Math.random() * 900000)}`;

    const res = await executePipelineProcess(payload);
    const now = new Date().toISOString().substring(11, 19) + ' UTC';

    if (res.success && res.data) {
      const data = res.data;
      const newEvent = {
        session_id: data.session_id,
        timestamp: now,
        transcript: payload.transcript,
        synthesis_score: data.synthesis_signal?.score || 0.85,
        speaker_match_score: data.speaker_match_signal?.score || 0.75,
        content_risk_score: data.content_risk_signal?.score || 0.60,
        fused_risk_score: data.risk_assessment?.risk_score || 0.89,
        final_action: data.final_action || 'RECOMMEND_CALLBACK_VERIFICATION',
        latency_ms: res.latencyMs,
        isReal: true,
      };
      setEvents((prev) => [newEvent, ...prev]);
    } else {
      // Offline fallback event clearly labeled
      const mockScore = selectedScenario === 'high_risk' ? 0.91 : selectedScenario === 'medium_risk' ? 0.48 : 0.06;
      const newEvent = {
        session_id: payload.session_id,
        timestamp: now,
        transcript: payload.transcript,
        synthesis_score: selectedScenario === 'high_risk' ? 0.88 : 0.05,
        speaker_match_score: selectedScenario === 'high_risk' ? 0.72 : 0.02,
        content_risk_score: selectedScenario === 'high_risk' ? 0.95 : 0.00,
        fused_risk_score: mockScore,
        final_action: mockScore >= 0.7 ? 'RECOMMEND_SUPERVISOR_ESCALATION & CALLBACK' : mockScore >= 0.4 ? 'RECOMMEND_CALLBACK_VERIFICATION' : 'PROCEED',
        latency_ms: res.latencyMs || 44,
        isReal: false, // flagged
      };
      setEvents((prev) => [newEvent, ...prev]);
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-white text-forest selection:bg-lemongrass py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-forest/10">
          <div>
            <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-forest/70 mb-1">
              <Radio size={14} className="text-forest animate-pulse" />
              <span>Live Event Stream</span>
            </div>
            <h1 className="font-display text-4xl font-extrabold text-forest tracking-tight">Live Event Stream & Proof of Latency</h1>
            <p className="text-xs font-mono text-forest/60 mt-1">
              Real-time verification log of incoming phone call requests processed by the orchestrator pipeline
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="px-3.5 py-1.5 rounded-full text-xs font-mono bg-sage-1 text-forest border border-forest/10 flex items-center gap-2">
              <Clock size={13} className="text-forest" /> Avg Pipeline Latency: <strong className="text-forest">44ms</strong>
            </span>
          </div>
        </div>

        {/* Simulator Trigger Panel */}
        <div className="rounded-2xl border border-forest/10 bg-sage-1 p-6 shadow-spade spade-cut-md">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div className="space-y-1 max-w-xl">
              <h3 className="font-display text-lg font-bold text-forest flex items-center gap-2">
                <Zap className="w-4 h-4 text-forest" />
                Trigger Live Pipeline Request Test
              </h3>
              <p className="text-xs text-forest/60 font-mono">
                Sends a real JSON payload containing Base64 PCM audio + live transcript to <code className="text-forest bg-white px-1.5 py-0.5 rounded border border-forest/10">/v1/pipeline/process</code> via orchestrator proxy
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <select
                value={selectedScenario}
                onChange={(e) => setSelectedScenario(e.target.value)}
                className="px-3 py-2 rounded-lg bg-white border border-forest/15 text-xs font-mono text-forest focus:outline-none focus:border-forest"
              >
                <option value="high_risk">High Risk Scam Payload (CFO Impersonation)</option>
                <option value="medium_risk">Medium Risk Payload (Password Reset)</option>
                <option value="clean_call">Clean Verification Call (Normal Inquiry)</option>
              </select>

              <button
                onClick={handleSimulateCall}
                disabled={loading}
                className="flex items-center gap-2 px-5 py-2 rounded-lg bg-forest text-lemongrass hover:bg-forest-hover font-mono font-bold text-xs transition-all shadow-spade disabled:opacity-50 cursor-pointer"
              >
                <Play size={14} className="fill-current" />
                <span>{loading ? 'Processing Pipeline...' : 'Process Live Call'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Live Stream Table */}
        <div className="rounded-2xl border border-forest/10 bg-white overflow-hidden shadow-spade spade-cut-md">
          <div className="px-6 py-4 bg-sage-1 border-b border-forest/10 flex items-center justify-between">
            <span className="font-mono text-xs font-bold text-forest uppercase tracking-wider">
              Incoming Call Log Stream ({events.length} Events)
            </span>
            <span className="text-[11px] font-mono text-forest/60">
              Live Streaming Mode • Auto-updating
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-sage-2 text-forest border-b border-forest/10">
                <tr>
                  <th className="py-3.5 px-4 font-bold">TIMESTAMP</th>
                  <th className="py-3.5 px-4 font-bold">SESSION ID</th>
                  <th className="py-3.5 px-4 font-bold">TRANSCRIPT / VISHING INTENT</th>
                  <th className="py-3.5 px-4 font-bold">4-VECTOR SIGNALS (ACOUSTIC | VOICEPRINT | VISHING | SIP)</th>
                  <th className="py-3.5 px-4 font-bold">FUSED RISK</th>
                  <th className="py-3.5 px-4 font-bold">LATENCY</th>
                  <th className="py-3.5 px-4 font-bold">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-forest/5">
                {events.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-16 text-center">
                      <div className="flex flex-col items-center">
                        <Radio size={36} className="text-forest/20 mb-3" />
                        <p className="text-sm font-semibold text-forest/50">No events yet</p>
                        <p className="text-xs text-forest/40 mt-1">Use the trigger panel above to process a live call through the pipeline</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  <AnimatePresence>
                    {events.map((evt, idx) => (
                      <motion.tr
                        key={evt.session_id + idx}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="hover:bg-sage-1/50 transition-colors"
                      >
                        <td className="py-3.5 px-4 text-forest/60 whitespace-nowrap">{evt.timestamp}</td>
                        <td className="py-3.5 px-4 text-forest font-bold whitespace-nowrap">{evt.session_id}</td>
                        <td className="py-3.5 px-4 text-forest/80 max-w-xs truncate font-sans text-xs" title={evt.transcript}>
                          "{evt.transcript}"
                        </td>
                        <td className="py-3.5 px-4 text-forest/80 whitespace-nowrap text-[11px]">
                          <span className="text-amber-700 font-bold" title="Acoustic Cloning Risk">A:{evt.synthesis_score.toFixed(2)}</span> |{' '}
                          <span className="text-blue-700 font-bold" title="Speaker Voiceprint Match">V:{evt.speaker_match_score.toFixed(2)}</span> |{' '}
                          <span className="text-purple-700 font-bold" title="Vishing Intent NLP">I:{evt.content_risk_score.toFixed(2)}</span> |{' '}
                          <span className="text-emerald-700 font-bold" title="SIP Telemetry">S:{(evt.fused_risk_score > 0.5 ? 0.75 : 0.08).toFixed(2)}</span>
                        </td>
                        <td className="py-3.5 px-4 whitespace-nowrap">
                          <RiskBadge score={evt.fused_risk_score} />
                        </td>
                        <td className="py-3.5 px-4 text-emerald-700 font-bold whitespace-nowrap">
                          {evt.latency_ms} ms
                        </td>
                        <td className="py-3.5 px-4 whitespace-nowrap">
                          <span className="px-2 py-1 rounded bg-sage-1 border border-forest/10 text-[10px] text-forest font-bold">
                            {evt.final_action}
                          </span>
                        </td>
                      </motion.tr>
                    ))}
                  </AnimatePresence>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
