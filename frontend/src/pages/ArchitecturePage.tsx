import React, { useState, useEffect, useCallback } from 'react';
import { checkAllHealth, HealthResult } from '../api';

const SERVICES = [
  { id: 'feat-extract', name: 'Feature Extraction', port: 8001, desc: 'PCM audio → log-mel spectrograms + ECAPA-TDNN speaker embeddings. Audio processed in-memory only — never persisted.', endpoints: ['POST /v1/extract', 'GET /healthz'], tech: 'Python · FastAPI · Librosa', x: 10, y: 20 },
  { id: 'spoof-detect', name: 'Spoof Detection', port: 8002, desc: 'AASIST/ResNet synthesis detection. Scores features for AI-generated speech. Returns synthesis_signal.', endpoints: ['POST /v1/detect', 'GET /healthz'], tech: 'Python · FastAPI · PyTorch', x: 10, y: 55 },
  { id: 'enrollment', name: 'Enrollment Service', port: 8003, desc: 'Multi-session voiceprint enrollment with challenge-response, liveness, RBAC, immutable audit logs.', endpoints: ['POST /enroll', 'POST /session', 'POST /revoke', 'GET /status', 'POST /match', 'GET /audit'], tech: 'Python · FastAPI', x: 10, y: 90 },
  { id: 'risk-fusion', name: 'Risk Fusion Engine', port: 8000, desc: 'Deterministic, regulator-audited fusion math. 4 signals → single risk_score. Same input → same output.', endpoints: ['POST /v1/assess', 'GET /healthz'], tech: 'Python · FastAPI · Audited', x: 40, y: 38 },
  { id: 'policy-engine', name: 'Policy Engine', port: 8004, desc: 'Per-tenant configurable thresholds. auto_block defaults false. Append-only audit trail.', endpoints: ['POST /v1/evaluate', 'GET/PUT /policy', 'GET /audit-log'], tech: 'Python · FastAPI', x: 65, y: 38 },
  { id: 'alerting', name: 'Alerting Service', port: 8005, desc: 'Multi-channel alert dispatch, UI push polling, SHA-256 hashed recipient audit trail.', endpoints: ['POST /v1/events', 'GET /alerts', 'GET /audit'], tech: 'Python · FastAPI · PubSub', x: 87, y: 38 },
  { id: 'orchestrator', name: 'Orchestrator', port: 8080, desc: 'End-to-end 5-step pipeline. Fail-safe: never fails open. Zero audio retention.', endpoints: ['POST /v1/pipeline/process', 'GET /healthz'], tech: 'Python · FastAPI · httpx', x: 40, y: 75 },
  { id: 'ingestion-gw', name: 'Ingestion Gateway', port: 50051, desc: 'Go gRPC gateway. Rate limiting (100 RPS/tenant), circuit breaker, 50K concurrent streams.', endpoints: ['gRPC StreamAudio'], tech: 'Go · gRPC', x: 87, y: 75 },
];

const CONNECTIONS = [
  { from: 'orchestrator', to: 'feat-extract', label: 'Step 1' },
  { from: 'orchestrator', to: 'spoof-detect', label: 'Step 2a' },
  { from: 'orchestrator', to: 'enrollment', label: 'Step 2b' },
  { from: 'orchestrator', to: 'risk-fusion', label: 'Step 3' },
  { from: 'risk-fusion', to: 'policy-engine', label: 'Step 4' },
  { from: 'policy-engine', to: 'alerting', label: 'Step 5' },
];

export const ArchitecturePage: React.FC = () => {
  const [healthMap, setHealthMap] = useState<Map<number, HealthResult>>(new Map());
  const [selectedNode, setSelectedNode] = useState<typeof SERVICES[0] | null>(null);

  const refresh = useCallback(async () => {
    const results = await checkAllHealth();
    const map = new Map<number, HealthResult>();
    results.forEach(r => map.set(r.port, r));
    setHealthMap(map);
  }, []);

  useEffect(() => { refresh(); const iv = setInterval(refresh, 15000); return () => clearInterval(iv); }, [refresh]);

  return (
    <section className="py-24 relative">
      <div className="absolute right-0 top-0 w-px h-24" style={{ background: 'linear-gradient(var(--accent), transparent)', opacity: 0.18 }} />
      <div className="w-[min(1280px,calc(100%-64px))] mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-[0.7fr_1.3fr] gap-12 mb-14">
          <div className="font-mono text-xs text-[var(--muted)]">06 / ARCHITECTURE</div>
          <div>
            <h2 className="text-[clamp(32px,4vw,48px)] leading-[1.08] tracking-[-0.045em] font-medium section-line">Built around evidence, not presentation.</h2>
            <p className="mt-5 text-[var(--muted)] text-base leading-relaxed max-w-[650px]">Eight microservices with clear boundaries. Failures isolate rather than silently propagate. Click any node to inspect endpoints and live health.</p>
          </div>
        </div>

        {/* Network Visual — matches original */}
        <div className="relative h-[320px] border border-[var(--line)] rounded-xl bg-white overflow-hidden mb-6" style={{
          background: 'radial-gradient(circle at 50% 50%, rgba(53,104,255,0.10), transparent 30%), #fff',
          boxShadow: '0 12px 35px rgba(17,19,16,0.035)',
        }}>
          {/* Grid overlay */}
          <div className="absolute inset-0 opacity-45 grid-bg" />

          {/* Connectors */}
          <svg className="absolute inset-0 w-full h-full" style={{ zIndex: 1 }}>
            {CONNECTIONS.map((c, i) => {
              const from = SERVICES.find(s => s.id === c.from)!;
              const to = SERVICES.find(s => s.id === c.to)!;
              return (
                <g key={i}>
                  <line x1={`${from.x + 4}%`} y1={`${from.y + 5}%`} x2={`${to.x + 4}%`} y2={`${to.y + 5}%`} stroke="url(#connector-grad)" strokeWidth="1" strokeDasharray="6 3" />
                  <circle r="3" fill="var(--accent)" opacity="0.9">
                    <animateMotion dur={`${2 + i * 0.4}s`} repeatCount="indefinite" path={`M${from.x + 4},${from.y + 5} L${to.x + 4},${to.y + 5}`} />
                  </circle>
                </g>
              );
            })}
            <defs>
              <linearGradient id="connector-grad"><stop offset="0%" stopColor="#AFC0F6" /><stop offset="100%" stopColor="var(--cyan)" /></linearGradient>
            </defs>
          </svg>

          {/* Nodes */}
          {SERVICES.map(svc => {
            const health = healthMap.get(svc.port);
            const isHealthy = health?.status === 'healthy';
            const isSel = selectedNode?.id === svc.id;
            const isDark = svc.id === 'orchestrator';
            return (
              <button key={svc.id} onClick={() => setSelectedNode(isSel ? null : svc)}
                className={`absolute w-14 h-14 rounded-full grid place-items-center font-mono text-[10px] cursor-pointer z-[3] transition-all border ${
                  isDark ? 'bg-[#111310] text-white border-[#111310]' : isSel ? 'bg-[rgba(21,94,239,0.08)] border-[var(--accent)]' : 'bg-white border-[#BFC8D6]'
                }`}
                style={{ left: `${svc.x}%`, top: `${svc.y}%`, boxShadow: '0 8px 25px rgba(17,19,16,0.08)' }}>
                <div className="absolute -inset-[7px] rounded-full border border-[rgba(53,104,255,0.18)]" style={{ animation: 'ring 2.8s ease-out infinite' }} />
                <div className="text-center leading-tight">
                  <div className="text-[8px]">:{svc.port}</div>
                  <div className={`w-1.5 h-1.5 rounded-full mx-auto mt-0.5 ${isHealthy ? 'bg-[var(--success)]' : health ? 'bg-[var(--danger)]' : 'bg-[var(--muted)]'}`} />
                </div>
              </button>
            );
          })}

          <div className="absolute left-5 bottom-4 font-mono text-[10px] text-[var(--muted)] tracking-[0.08em] uppercase z-[4]">
            eight-service pipeline / live health
          </div>
        </div>

        {/* Detail Panel */}
        {selectedNode && (
          <div className="bg-white border border-[var(--line)] rounded-xl p-6 card-accent" style={{ boxShadow: '0 12px 35px rgba(17,19,16,0.035)' }}>
            <div className="flex items-center gap-3 mb-3">
              <div className={`w-2 h-2 rounded-full ${healthMap.get(selectedNode.port)?.status === 'healthy' ? 'bg-[var(--success)]' : 'bg-[var(--danger)]'}`} />
              <span className="text-lg font-medium">{selectedNode.name}</span>
              <span className="font-mono text-xs text-[var(--muted)]">:{selectedNode.port} · {healthMap.get(selectedNode.port)?.latencyMs || '—'}ms</span>
            </div>
            <div className="font-mono text-[10px] text-[var(--accent)] mb-2">{selectedNode.tech}</div>
            <p className="text-sm text-[var(--muted)] leading-relaxed mb-4">{selectedNode.desc}</p>
            <div className="flex flex-wrap gap-2">
              {selectedNode.endpoints.map((ep, i) => (
                <span key={i} className="font-mono text-[10px] px-2 py-1 bg-[#F0F1EC] border border-[var(--line)] rounded">{ep}</span>
              ))}
            </div>
          </div>
        )}

        {/* Service Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          {[
            { num: '01', title: 'Three-signal fusion', desc: 'Synthesis, speaker, and contextual signals — combined through deterministic, auditable fusion math.' },
            { num: '02', title: 'Eight microservices', desc: 'Clear boundaries between processing responsibilities. Failures isolate rather than silently propagate.' },
            { num: '03', title: 'Fail-safe by design', desc: 'When sufficient confidence cannot be established, Satya fails safely instead of manufacturing certainty.' },
          ].map((c, i) => (
            <div key={i} className="bg-white border border-[var(--line)] rounded-xl p-6 card-accent transition-all duration-200 hover:-translate-y-1.5 hover:shadow-lg group" style={{ boxShadow: '0 8px 30px rgba(17,19,16,0.035)' }}>
              <div className="font-mono text-[11px] text-[#7A7F78] mb-10 group-hover:text-[var(--accent)] transition-colors">{c.num}</div>
              <h3 className="text-xl font-medium tracking-[-0.02em] mb-2.5 transition-colors group-hover:text-[var(--accent)]">{c.title}</h3>
              <p className="text-sm leading-relaxed text-[var(--muted)]">{c.desc}</p>
            </div>
          ))}
        </div>

        {/* Pipeline Steps Legend */}
        <div className="mt-4 flex items-center gap-2 font-mono text-[10px] text-[var(--muted)] flex-wrap">
          {['1. Extract', '2. Spoof+Enroll+Content (∥)', '3. Fuse', '4. Policy', '5. Alert'].map((s, i) => (
            <React.Fragment key={i}>
              <span className="px-2 py-1 bg-white border border-[var(--line)] rounded">{s}</span>
              {i < 4 && <span className="text-[var(--accent)]">→</span>}
            </React.Fragment>
          ))}
        </div>
      </div>
    </section>
  );
};
