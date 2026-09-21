// The detector embeds this panel; it is intentionally not a routed page.
import React, { useCallback, useRef, useState } from 'react';
import { Activity, Radio } from 'lucide-react';
import RealtimeAudioCapture from '../components/RealtimeAudioCapture';
import RiskBadge from '../components/RiskBadge';
import { executePipelineProcess } from '../utils/api';

function parseRisk(value) {
  if (value === '') return 0;
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0 || parsed > 1) throw new Error('Risk metadata values must be between 0 and 1.');
  return parsed;
}

function parseJitter(value) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) throw new Error('SIP packet jitter must be a non-negative number of milliseconds.');
  return parsed;
}

const Signal = ({ name, value }) => <span className="rounded bg-white p-2">{name}: {typeof value === 'number' ? value.toFixed(2) : 'unavailable'}</span>;

export default function LiveDetectionPanel({ embedded = false }) {
  const [tenantId, setTenantId] = useState('');
  const [subjectId, setSubjectId] = useState('');
  const [transcript, setTranscript] = useState('');
  const [contextScore, setContextScore] = useState('');
  const [callerIdRisk, setCallerIdRisk] = useState('');
  const [codecRisk, setCodecRisk] = useState('');
  const [jitterMs, setJitterMs] = useState('');
  const [events, setEvents] = useState([]);
  const [combinedRisk, setCombinedRisk] = useState(null);
  const [latest, setLatest] = useState(null);
  const [error, setError] = useState(null);
  const sessionIdRef = useRef(null);
  const windowsRef = useRef(0);

  const beginStream = useCallback(() => {
    sessionIdRef.current = crypto.randomUUID();
    windowsRef.current = 0;
    setEvents([]);
    setCombinedRisk(null);
    setLatest(null);
    setError(null);
  }, []);

  const processWindow = useCallback(async (audioWindow) => {
    const payload = {
      session_id: sessionIdRef.current,
      tenant_id: tenantId.trim(),
      subject_id: subjectId.trim(),
      transcript: transcript.trim(),
      ...audioWindow,
    };
    if (contextScore !== '') payload.context_score = parseRisk(contextScore);
    if (callerIdRisk !== '') payload.caller_id_spoof_risk = parseRisk(callerIdRisk);
    if (codecRisk !== '') payload.codec_anomaly_score = parseRisk(codecRisk);
    if (jitterMs !== '') payload.sip_packet_jitter_ms = parseJitter(jitterMs);
    const response = await executePipelineProcess(payload);
    if (!response.success || !response.data) throw new Error(response.error || 'Pipeline unavailable. No score was produced for this audio window.');

    const data = response.data;
    const risk = data.risk_assessment?.risk_score;
    if (typeof risk !== 'number') throw new Error('The pipeline returned a degraded response without a fused risk score.');
    windowsRef.current += 1;
    setCombinedRisk((previous) => previous === null ? risk : previous + (risk - previous) / windowsRef.current);
    const event = {
      id: `${data.session_id}-${windowsRef.current}`,
      timestamp: new Date().toLocaleTimeString(),
      risk,
      action: data.final_action,
      degraded: data.degraded,
      latencyMs: response.latencyMs,
      synthesis: data.synthesis_signal?.score,
      speaker: data.speaker_match_signal?.score,
      content: data.content_risk_signal?.score,
      sip: data.sip_telemetry_signal?.score,
      explanation: data.explanation,
    };
    setLatest(event);
    setEvents((previous) => [event, ...previous].slice(0, 20));
  }, [callerIdRisk, codecRisk, contextScore, jitterMs, subjectId, tenantId, transcript]);

  const ready = Boolean(tenantId.trim() && subjectId.trim());
  return <div className={embedded ? "text-forest" : "min-h-screen bg-white py-10 text-forest"}><div className={embedded ? "space-y-7" : "mx-auto max-w-7xl space-y-7 px-4 sm:px-6 lg:px-8"}>
    {!embedded && <header className="border-b border-forest/10 pb-6"><div className="mb-1 flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-forest/70"><Radio size={14} /> Live 9-service pipeline</div><h1 className="font-display text-4xl font-extrabold">Continuous Voice Risk Analysis</h1><p className="mt-2 max-w-3xl text-sm text-forest/75">Each rolling microphone window is evaluated through acoustic analysis, voiceprint verification, content-risk analysis when a transcript is provided, fusion, policy, and alerting. The combined score is the running mean of real fused chunk scores.</p></header>}
    <section className="grid gap-5 lg:grid-cols-[1.15fr_.85fr]"><div className="space-y-4 rounded-2xl border border-forest/15 bg-white p-6 shadow-spade"><h2 className="font-display text-lg font-bold">Call context</h2><div className="grid gap-3 sm:grid-cols-2"><label className="text-xs font-mono font-bold">Tenant ID<input value={tenantId} onChange={(event) => setTenantId(event.target.value)} placeholder="Required" className="mt-1 w-full rounded-lg border border-forest/20 p-2 font-normal outline-none focus:border-forest" /></label><label className="text-xs font-mono font-bold">Subject ID<input value={subjectId} onChange={(event) => setSubjectId(event.target.value)} placeholder="Required for voiceprint matching" className="mt-1 w-full rounded-lg border border-forest/20 p-2 font-normal outline-none focus:border-forest" /></label><label className="text-xs font-mono font-bold">Context risk<input value={contextScore} onChange={(event) => setContextScore(event.target.value)} inputMode="decimal" placeholder="Optional, 0–1" className="mt-1 w-full rounded-lg border border-forest/20 p-2 font-normal outline-none focus:border-forest" /></label><label className="text-xs font-mono font-bold">Caller-ID risk<input value={callerIdRisk} onChange={(event) => setCallerIdRisk(event.target.value)} inputMode="decimal" placeholder="Optional, 0–1" className="mt-1 w-full rounded-lg border border-forest/20 p-2 font-normal outline-none focus:border-forest" /></label><label className="text-xs font-mono font-bold">Codec anomaly risk<input value={codecRisk} onChange={(event) => setCodecRisk(event.target.value)} inputMode="decimal" placeholder="Optional, 0–1" className="mt-1 w-full rounded-lg border border-forest/20 p-2 font-normal outline-none focus:border-forest" /></label><label className="text-xs font-mono font-bold">SIP jitter (ms)<input value={jitterMs} onChange={(event) => setJitterMs(event.target.value)} inputMode="decimal" placeholder="Optional, measured value" className="mt-1 w-full rounded-lg border border-forest/20 p-2 font-normal outline-none focus:border-forest" /></label></div><label className="block text-xs font-mono font-bold">Redacted transcript (optional; enables content-risk analysis)<textarea value={transcript} onChange={(event) => setTranscript(event.target.value)} rows={3} placeholder="Paste only a redacted, consented transcript." className="mt-1 w-full rounded-lg border border-forest/20 p-2 font-normal outline-none focus:border-forest" /></label><RealtimeAudioCapture disabled={!ready} onStart={beginStream} onWindow={processWindow} />{!ready && <p className="text-xs font-mono text-amber-800">Tenant ID and subject ID are required before live voiceprint-aware analysis can begin.</p>}{error && <p className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs font-mono text-rose-800">{error}</p>}</div>
    <aside className="space-y-4 rounded-2xl border border-forest/15 bg-sage-1 p-6 shadow-spade"><p className="text-xs font-mono font-bold uppercase tracking-wider">Live decision</p><div className="flex items-center gap-4"><div className="flex h-28 w-28 items-center justify-center rounded-full border-8 border-forest bg-white text-3xl font-extrabold">{combinedRisk === null ? '—' : `${Math.round(combinedRisk * 100)}%`}</div><div><p className="font-display text-lg font-bold">Combined fused risk</p><p className="text-xs text-forest/70">{windowsRef.current} real-time windows evaluated</p></div></div><div className="rounded-xl border border-forest/15 bg-white p-4"><p className="text-[11px] font-mono font-bold text-forest/60">CURRENT POLICY ACTION</p><p className="mt-1 break-words font-mono text-sm font-extrabold">{latest?.action || 'Awaiting first scored window'}</p><p className="mt-2 text-xs text-forest/70">{latest?.explanation || 'No decision is shown until the live pipeline returns a real response.'}</p></div>{latest && <div className="grid grid-cols-2 gap-2 text-xs font-mono"><Signal name="Acoustic" value={latest.synthesis} /><Signal name="Voiceprint" value={latest.speaker} /><Signal name="Content" value={latest.content} /><Signal name="SIP" value={latest.sip} /></div>}</aside></section>
    <section className="overflow-hidden rounded-2xl border border-forest/15 bg-white shadow-spade"><div className="flex items-center justify-between border-b border-forest/10 bg-sage-1 px-5 py-4"><span className="font-mono text-xs font-bold">REAL-TIME WINDOW LOG</span><Activity size={16} /></div><div className="overflow-x-auto"><table className="w-full text-left text-xs font-mono"><thead className="border-b border-forest/10 text-forest/60"><tr><th className="p-3">TIME</th><th className="p-3">ACOUSTIC</th><th className="p-3">VOICEPRINT</th><th className="p-3">CONTENT</th><th className="p-3">SIP</th><th className="p-3">FUSED RISK</th><th className="p-3">ACTION</th><th className="p-3">LATENCY</th></tr></thead><tbody>{events.length === 0 ? <tr><td colSpan={8} className="p-10 text-center text-forest/60">Start the microphone to receive real pipeline results.</td></tr> : events.map((event) => <tr key={event.id} className="border-b border-forest/5"><td className="p-3">{event.timestamp}</td><td className="p-3">{event.synthesis?.toFixed(2) ?? '—'}</td><td className="p-3">{event.speaker?.toFixed(2) ?? '—'}</td><td className="p-3">{event.content?.toFixed(2) ?? '—'}</td><td className="p-3">{event.sip?.toFixed(2) ?? '—'}</td><td className="p-3"><RiskBadge score={event.risk} /></td><td className="p-3 font-bold">{event.action}{event.degraded ? ' (degraded)' : ''}</td><td className="p-3">{event.latencyMs} ms</td></tr>)}</tbody></table></div></section>
  </div></div>;
}
