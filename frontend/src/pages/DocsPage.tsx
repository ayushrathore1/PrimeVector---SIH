import React, { useState } from 'react';
import { assessRiskDirect, RiskAssessment } from '../api';

const SERVICE_DOCS = [
  { name: 'orchestrator', port: 8080, endpoints: [
    { method: 'POST', path: '/v1/pipeline/process', desc: 'Full 5-step pipeline: extract → spoof+enrollment+content → fusion → policy → alert', body: '{\n  "session_id": "s1",\n  "tenant_id": "t1",\n  "subject_id": "subj1",\n  "audio_pcm_base64": "<base64>",\n  "sample_rate_hz": 16000,\n  "channels": 1,\n  "context_score": 0.3,\n  "transcript": "Share your OTP now"\n}' },
    { method: 'GET', path: '/healthz', desc: 'Liveness probe' },
  ]},
  { name: 'risk-fusion-engine', port: 8000, endpoints: [
    { method: 'POST', path: '/v1/assess', desc: 'Deterministic fusion: 4 signals → single risk_score + actions', body: '{\n  "call_session_id": "s1",\n  "tenant_id": "t1",\n  "synthesis_signal": {\n    "score": 0.8,\n    "confidence": 0.9,\n    "available": true,\n    "detail": "AI speech"\n  },\n  "speaker_match_signal": { ... },\n  "contextual_signal": { ... }\n}' },
  ]},
  { name: 'feature-extraction', port: 8001, endpoints: [
    { method: 'POST', path: '/v1/extract', desc: 'PCM audio → log-mel spectrograms + speaker embeddings (in-memory only)', body: '{\n  "request_id": "r1",\n  "tenant_id": "t1",\n  "audio_bytes": "<base64>",\n  "sample_rate_hz": 16000\n}' },
  ]},
  { name: 'spoof-detection', port: 8002, endpoints: [
    { method: 'POST', path: '/v1/detect', desc: 'Score audio features for AI-synthesized speech likelihood', body: '{\n  "call_session_id": "s1",\n  "tenant_id": "t1",\n  "audio_features": [0.1, ...],\n  "feature_type": "wav2vec2"\n}' },
  ]},
  { name: 'enrollment-service', port: 8003, endpoints: [
    { method: 'POST', path: '/v1/tenants/{t}/enroll', desc: 'Start enrollment (tenant_admin required)' },
    { method: 'POST', path: '…/session', desc: 'Submit capture session + challenge phrase' },
    { method: 'POST', path: '…/revoke', desc: '⚠ Compliance: immutable audit record' },
    { method: 'GET', path: '…/status', desc: 'NOT_ENROLLED | ENROLLED | REVOKED' },
    { method: 'POST', path: '…/match', desc: 'Compare live embedding vs enrolled voiceprint' },
    { method: 'GET', path: '…/audit', desc: 'Immutable audit trail' },
  ]},
  { name: 'policy-threshold-engine', port: 8004, endpoints: [
    { method: 'POST', path: '/v1/evaluate', desc: 'Apply tenant policy → final action' },
    { method: 'GET', path: '/v1/tenants/{t}/policy', desc: 'Get current policy config' },
    { method: 'PUT', path: '/v1/tenants/{t}/policy', desc: '⚠ Creates audit entries' },
    { method: 'GET', path: '/v1/tenants/{t}/audit-log', desc: 'Immutable change trail' },
  ]},
  { name: 'alerting-service', port: 8005, endpoints: [
    { method: 'POST', path: '/v1/events', desc: 'Event injection' },
    { method: 'GET', path: '/v1/tenants/{t}/alerts', desc: 'UI push poll' },
    { method: 'GET', path: '/v1/tenants/{t}/audit', desc: 'Hashed recipient audit' },
  ]},
  { name: 'ingestion-gateway', port: 50051, endpoints: [
    { method: 'gRPC', path: 'StreamAudio', desc: 'Rate limited (100 RPS), circuit breaker, 50K streams' },
  ]},
];

export const DocsPage: React.FC = () => {
  const [expandedSvc, setExpandedSvc] = useState<string | null>('orchestrator');
  const [synthScore, setSynthScore] = useState(0.7);
  const [speakerScore, setSpeakerScore] = useState(0.3);
  const [contextScore, setContextScore] = useState(0.4);
  const [speakerAvail, setSpeakerAvail] = useState(true);
  const [sandboxResult, setSandboxResult] = useState<RiskAssessment | null>(null);
  const [sandboxLoading, setSandboxLoading] = useState(false);
  const [sandboxError, setSandboxError] = useState('');

  const handleSandbox = async () => {
    setSandboxLoading(true); setSandboxError(''); setSandboxResult(null);
    try {
      const res = await assessRiskDirect({
        call_session_id: `sandbox-${Date.now()}`, tenant_id: 'demo-tenant',
        synthesis_signal: { score: synthScore, confidence: 0.9, available: true, detail: 'sandbox' },
        speaker_match_signal: { score: speakerScore, confidence: speakerAvail ? 0.85 : 0, available: speakerAvail, detail: speakerAvail ? 'enrolled' : 'unenrolled' },
        contextual_signal: { score: contextScore, confidence: 1.0, available: true, detail: 'sandbox' },
      });
      setSandboxResult(res);
    } catch (e: any) { setSandboxError(e.message); }
    setSandboxLoading(false);
  };

  return (
    <>
      {/* API Docs Section */}
      <section className="py-24 border-t border-[var(--line)] relative">
        <div className="absolute right-0 top-0 w-px h-24" style={{ background: 'linear-gradient(var(--accent), transparent)', opacity: 0.18 }} />
        <div className="w-[min(1280px,calc(100%-64px))] mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-[0.7fr_1.3fr] gap-12 mb-14">
            <div className="font-mono text-xs text-[var(--muted)]">07 / API DOCUMENTATION</div>
            <div>
              <h2 className="text-[clamp(32px,4vw,48px)] leading-[1.08] tracking-[-0.045em] font-medium section-line">Simple enough to inspect.</h2>
              <p className="mt-5 text-[var(--muted)] text-base leading-relaxed max-w-[650px]">Complete endpoint reference for all 8 services — {SERVICE_DOCS.reduce((a, s) => a + s.endpoints.length, 0)} endpoints total. The sandbox below calls the real risk-fusion-engine.</p>
            </div>
          </div>

          {/* Fusion Sandbox */}
          <div className="bg-white border border-[var(--line)] rounded-xl overflow-hidden mb-6 panel-bar" style={{ boxShadow: '0 30px 80px rgba(17,19,16,0.11)' }}>
            <div className="px-5 py-4 border-b border-[var(--line)] flex justify-between items-center">
              <span className="text-[13px] font-medium">Risk Fusion Sandbox</span>
              <span className="font-mono text-[10px] text-[var(--muted)] uppercase"><span className="text-[var(--accent)]">●</span> POST /api/8000/v1/assess</span>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr] gap-0">
              <div className="p-5 border-r border-[var(--line)] space-y-4">
                {[
                  { label: 'Synthesis signal', val: synthScore, set: setSynthScore },
                  { label: 'Speaker match', val: speakerScore, set: setSpeakerScore },
                  { label: 'Contextual risk', val: contextScore, set: setContextScore },
                ].map((s, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-[11px] font-mono mb-1"><span className="text-[var(--muted)]">{s.label}</span><span>{s.val.toFixed(2)}</span></div>
                    <input type="range" min="0" max="1" step="0.05" value={s.val} onChange={e => s.set(parseFloat(e.target.value))} className="w-full accent-[var(--accent)] bg-transparent border-none p-0" />
                  </div>
                ))}
                <label className="flex items-center gap-2 text-[11px] text-[var(--muted)] font-mono cursor-pointer">
                  <input type="checkbox" checked={speakerAvail} onChange={e => setSpeakerAvail(e.target.checked)} className="accent-[var(--accent)] w-3 h-3" /> Speaker available
                </label>
                <button onClick={handleSandbox} disabled={sandboxLoading}
                  className="w-full min-h-[44px] rounded-lg text-sm font-medium text-white cursor-pointer disabled:opacity-50" style={{ background: 'var(--ink)', border: '1px solid var(--ink)', boxShadow: '0 10px 28px rgba(17,19,16,0.12)' }}>
                  {sandboxLoading ? 'Assessing...' : '▶ Assess Risk'}
                </button>
                {sandboxError && <div className="text-xs text-[var(--danger)] font-mono">{sandboxError}</div>}
              </div>
              <div className="p-5">
                {sandboxResult ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-4">
                      <div className="text-4xl font-medium">{Math.round(sandboxResult.risk_score * 100)}%</div>
                      <div>
                        <div className={`text-sm font-medium ${sandboxResult.actions[0] === 'PROCEED' ? 'text-[var(--success)]' : sandboxResult.actions[0]?.includes('BLOCK') ? 'text-[var(--danger)]' : 'text-[var(--warning)]'}`}>
                          {sandboxResult.actions[0]?.replace(/_/g, ' ')}
                        </div>
                        <div className="text-[10px] text-[var(--muted)] font-mono">confidence: {sandboxResult.confidence.toFixed(3)} · {sandboxResult.degraded ? 'DEGRADED' : 'FULL'}</div>
                      </div>
                    </div>
                    <div className="h-[5px] bg-[#E3E5DF] rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${sandboxResult.risk_score * 100}%`, background: 'linear-gradient(90deg, var(--success), var(--cyan))' }} />
                    </div>
                    <p className="text-[11px] text-[var(--muted)] font-mono">{sandboxResult.explanation}</p>
                    <pre className="p-4 code-block text-[10px] overflow-auto max-h-40">{JSON.stringify(sandboxResult, null, 2)}</pre>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full text-sm text-[var(--muted)]">Adjust signals and click "Assess Risk"</div>
                )}
              </div>
            </div>
          </div>

          {/* API Reference */}
          <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-4">
            {/* Service Nav */}
            <div className="border border-[var(--line)] bg-white p-3 h-max" style={{ boxShadow: '0 8px 30px rgba(17,19,16,0.035)' }}>
              {SERVICE_DOCS.map(svc => (
                <button key={svc.name} onClick={() => setExpandedSvc(expandedSvc === svc.name ? null : svc.name)}
                  className={`w-full text-left px-3 py-3 font-mono text-xs rounded-md cursor-pointer transition-all ${expandedSvc === svc.name ? 'text-[var(--ink)] bg-[#F0F1EC] font-medium' : 'text-[var(--muted)] hover:bg-[#F5F6F2] hover:text-[var(--ink)] hover:translate-x-0.5'}`}>
                  <span className="text-[9px] mr-1.5">:{svc.port}</span> {svc.name}
                </button>
              ))}
            </div>

            {/* Endpoint Detail */}
            <div className="space-y-2">
              {expandedSvc && SERVICE_DOCS.filter(s => s.name === expandedSvc).map(svc => (
                <React.Fragment key={svc.name}>
                  {svc.endpoints.map((ep, i) => (
                    <div key={i} className="bg-white border border-[var(--line)] rounded-xl p-5 card-accent transition-all hover:-translate-y-0.5" style={{ boxShadow: '0 8px 30px rgba(17,19,16,0.035)' }}>
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`font-mono text-[10px] font-bold px-1.5 py-0.5 rounded ${
                          ep.method === 'POST' ? 'bg-[rgba(22,121,74,0.08)] text-[var(--success)]' :
                          ep.method === 'PUT' ? 'bg-[rgba(161,92,0,0.08)] text-[var(--warning)]' :
                          ep.method === 'gRPC' ? 'bg-[rgba(24,183,217,0.08)] text-[var(--cyan)]' :
                          'bg-[rgba(21,94,239,0.08)] text-[var(--accent)]'
                        }`}>{ep.method}</span>
                        <span className="font-mono text-xs">{ep.path}</span>
                      </div>
                      <p className="text-[11px] text-[var(--muted)]">{ep.desc}</p>
                      {ep.body && (
                        <pre className="mt-3 p-4 code-block text-[10px] overflow-auto max-h-48">{ep.body}</pre>
                      )}
                    </div>
                  ))}
                </React.Fragment>
              ))}
              {!expandedSvc && <div className="text-sm text-[var(--muted)] text-center py-12">Select a service from the sidebar</div>}
            </div>
          </div>
        </div>
      </section>
    </>
  );
};
