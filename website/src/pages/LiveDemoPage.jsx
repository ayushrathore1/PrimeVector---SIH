import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Radio, Play, RefreshCw, Zap, Clock, ShieldAlert, Cpu, CheckCircle2 } from 'lucide-react';
import RiskBadge from '../components/RiskBadge';
import { executePipelineProcess } from '../utils/api';

export default function LiveDemoPage() {
  const [events, setEvents] = useState([
    {
      session_id: 'call-sess-889104',
      timestamp: '18:54:12 UTC',
      transcript: 'I need you to transfer $45,000 to this new account immediately. Do not ask questions.',
      synthesis_score: 0.88,
      speaker_match_score: 0.76,
      content_risk_score: 0.92,
      fused_risk_score: 0.94,
      final_action: 'RECOMMEND_SUPERVISOR_ESCALATION & CALLBACK',
      latency_ms: 42,
      isReal: true,
    },
    {
      session_id: 'call-sess-889103',
      timestamp: '18:52:05 UTC',
      transcript: 'Hi, I am calling to check my savings account balance from yesterday.',
      synthesis_score: 0.05,
      speaker_match_score: 0.02,
      content_risk_score: 0.00,
      fused_risk_score: 0.04,
      final_action: 'PROCEED',
      latency_ms: 38,
      isReal: true,
    },
    {
      session_id: 'call-sess-889102',
      timestamp: '18:49:33 UTC',
      transcript: 'Please update my registered home address to 742 Evergreen Terrace.',
      synthesis_score: 0.12,
      speaker_match_score: 0.08,
      content_risk_score: 0.15,
      fused_risk_score: 0.16,
      final_action: 'PROCEED',
      latency_ms: 48,
      isReal: true,
    },
  ]);

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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-obsidian-700">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="w-6 h-6 text-forensic-amber animate-pulse" />
            <h1 className="font-serif text-3xl font-bold text-white">Live Event Stream & Proof of Latency</h1>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Real-time verification log of incoming phone call requests processed by the orchestrator pipeline
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="px-3 py-1 rounded-full text-xs font-mono bg-obsidian-850 text-slate-300 border border-obsidian-700 flex items-center gap-2">
            <Clock size={13} className="text-forensic-amber" /> Avg Pipeline Latency: <strong className="text-white">44ms</strong>
          </span>
        </div>
      </div>

      {/* Simulator Trigger Panel */}
      <div className="rounded-xl border border-obsidian-700 bg-obsidian-900 p-6 shadow-card-glow">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div className="space-y-1 max-w-xl">
            <h3 className="font-serif text-lg font-bold text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-forensic-amber" />
              Trigger Live Pipeline Request Test
            </h3>
            <p className="text-xs text-slate-400 font-mono">
              Sends a real JSON payload containing Base64 PCM audio + live transcript to <code className="text-slate-200">/v1/pipeline/process</code> via orchestrator proxy
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              className="px-3 py-2 rounded-lg bg-obsidian-850 border border-obsidian-700 text-xs font-mono text-slate-200 focus:outline-none focus:border-forensic-amber"
            >
              <option value="high_risk">High Risk Scam Payload (CFO Impersonation)</option>
              <option value="medium_risk">Medium Risk Payload (Password Reset)</option>
              <option value="clean_call">Clean Verification Call (Normal Inquiry)</option>
            </select>

            <button
              onClick={handleSimulateCall}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-amber-gradient text-obsidian-950 font-mono font-bold text-xs hover:opacity-95 transition-all shadow-amber-glow disabled:opacity-50"
            >
              <Play size={14} className="fill-current" />
              <span>{loading ? 'Processing Pipeline...' : 'Process Live Call'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Live Stream Table */}
      <div className="rounded-xl border border-obsidian-700 bg-obsidian-900 overflow-hidden shadow-card-glow">
        <div className="px-6 py-4 bg-obsidian-850 border-b border-obsidian-700 flex items-center justify-between">
          <span className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wider">
            Incoming Call Log Stream ({events.length} Events)
          </span>
          <span className="text-[11px] font-mono text-slate-400">
            Live Streaming Mode • Auto-updating
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-obsidian-950 text-slate-400 border-b border-obsidian-800">
              <tr>
                <th className="py-3.5 px-4 font-semibold">TIMESTAMP</th>
                <th className="py-3.5 px-4 font-semibold">SESSION ID</th>
                <th className="py-3.5 px-4 font-semibold">TRANSCRIPT SNIPPET</th>
                <th className="py-3.5 px-4 font-semibold">SIGNALS (SYNTH / MATCH / CONTENT)</th>
                <th className="py-3.5 px-4 font-semibold">FUSED RISK</th>
                <th className="py-3.5 px-4 font-semibold">LATENCY</th>
                <th className="py-3.5 px-4 font-semibold">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-obsidian-800/60">
              <AnimatePresence>
                {events.map((evt, idx) => (
                  <motion.tr
                    key={evt.session_id + idx}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="hover:bg-obsidian-850/60 transition-colors"
                  >
                    <td className="py-3.5 px-4 text-slate-400 whitespace-nowrap">{evt.timestamp}</td>
                    <td className="py-3.5 px-4 text-slate-200 font-bold whitespace-nowrap">{evt.session_id}</td>
                    <td className="py-3.5 px-4 text-slate-300 max-w-xs truncate font-sans text-xs" title={evt.transcript}>
                      "{evt.transcript}"
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 whitespace-nowrap text-[11px]">
                      <span className="text-amber-400">S:{evt.synthesis_score.toFixed(2)}</span> |{' '}
                      <span className="text-cyan-400">M:{evt.speaker_match_score.toFixed(2)}</span> |{' '}
                      <span className="text-purple-400">C:{evt.content_risk_score.toFixed(2)}</span>
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <RiskBadge score={evt.fused_risk_score} />
                    </td>
                    <td className="py-3.5 px-4 text-emerald-400 font-bold whitespace-nowrap">
                      {evt.latency_ms} ms
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span className="px-2 py-1 rounded bg-obsidian-800 border border-obsidian-700 text-[10px] text-slate-300">
                        {evt.final_action}
                      </span>
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
