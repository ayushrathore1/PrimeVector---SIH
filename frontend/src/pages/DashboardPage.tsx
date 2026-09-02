import React, { useEffect, useState, useCallback } from 'react';
import { checkAllHealth, getTenantAlerts, HealthResult, AlertOut, PipelineResponse } from '../api';

interface DashboardPageProps {
  tenantId: string;
  recentResults: PipelineResponse[];
  onNavigate: (page: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ tenantId, recentResults, onNavigate }) => {
  const [services, setServices] = useState<HealthResult[]>([]);
  const [alerts, setAlerts] = useState<AlertOut[]>([]);
  const [alertError, setAlertError] = useState('');
  const [lastChecked, setLastChecked] = useState('');

  const refreshHealth = useCallback(async () => {
    const results = await checkAllHealth();
    setServices(results);
    setLastChecked(new Date().toLocaleTimeString());
  }, []);

  const refreshAlerts = useCallback(async () => {
    try {
      const data = await getTenantAlerts(tenantId);
      setAlerts(data.alerts || []);
      setAlertError('');
    } catch (e: any) { setAlertError(e.message); }
  }, [tenantId]);

  useEffect(() => {
    refreshHealth();
    refreshAlerts();
    const h = setInterval(refreshHealth, 12000);
    const a = setInterval(refreshAlerts, 5000);
    return () => { clearInterval(h); clearInterval(a); };
  }, [refreshHealth, refreshAlerts]);

  const healthyCount = services.filter(s => s.status === 'healthy').length;
  const avgLatency = services.filter(s => s.latencyMs).reduce((a, s) => a + (s.latencyMs || 0), 0) / (services.filter(s => s.latencyMs).length || 1);

  return (
    <>
      {/* Hero */}
      <section className="relative isolate">
        {/* Grid pattern overlay */}
        <div className="absolute inset-0 z-[-2] pointer-events-none opacity-[0.28]" style={{
          backgroundImage: 'linear-gradient(rgba(53,104,255,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(53,104,255,0.07) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
          maskImage: 'linear-gradient(to right, black 0%, transparent 72%)',
          WebkitMaskImage: 'linear-gradient(to right, black 0%, transparent 72%)',
        }} />
        {/* Ambient glow orb */}
        <div className="absolute z-[-1] w-[620px] h-[620px] rounded-full pointer-events-none" style={{
          left: '-180px', top: '40px',
          background: 'radial-gradient(circle, rgba(53,104,255,0.13), rgba(24,183,217,0.045) 38%, transparent 70%)',
          animation: 'ambient 7s ease-in-out infinite',
        }} />

        <div className="w-[min(1280px,calc(100%-64px))] mx-auto grid grid-cols-1 lg:grid-cols-[1.15fr_0.85fr] gap-16 items-center" style={{ minHeight: 'calc(100vh - 72px)', padding: '96px 0' }}>
          <div>
            <div className="font-mono text-xs tracking-[0.12em] uppercase text-[var(--muted)] mb-6">Prime Vector / Satya</div>
            <h1 className="text-[clamp(44px,6vw,72px)] leading-[1.02] tracking-[-0.055em] font-medium max-w-[720px]" style={{ animation: 'heroTitle 1s cubic-bezier(0.16,1,0.3,1) both' }}>
              Three signals.<br />One <span className="text-[var(--accent)]">truth-oriented</span><br />decision layer.
            </h1>
            <p className="mt-7 max-w-[640px] text-lg leading-relaxed text-[var(--muted)]" style={{ animation: 'fadeUp 0.8s 0.15s cubic-bezier(0.16,1,0.3,1) both' }}>
              Satya combines multiple signals through a distributed service pipeline designed to produce transparent results while failing safely when the system cannot establish sufficient confidence.
            </p>
            <div className="mt-10 flex gap-3 flex-wrap" style={{ animation: 'fadeUp 0.8s 0.28s cubic-bezier(0.16,1,0.3,1) both' }}>
              <button onClick={() => onNavigate('pipeline')} className="btn-primary inline-flex items-center justify-center min-h-[44px] px-[18px] rounded-lg text-sm font-medium text-white cursor-pointer" style={{
                background: 'var(--ink)', border: '1px solid var(--ink)', boxShadow: '0 10px 28px rgba(17,19,16,0.12)', position: 'relative', overflow: 'hidden',
              }}>Run Pipeline Test</button>
              <button onClick={() => onNavigate('architecture')} className="inline-flex items-center justify-center min-h-[44px] px-[18px] rounded-lg border border-[var(--line)] text-sm font-medium bg-white cursor-pointer hover:-translate-y-px transition-transform">
                View Architecture
              </button>
            </div>
          </div>

          {/* System Panel — matches original signal fusion panel */}
          <div className="bg-white border border-[var(--line)] rounded-xl overflow-hidden panel-bar" style={{ boxShadow: '0 30px 80px rgba(17,19,16,0.11)', animation: 'panelIn 1s 0.18s cubic-bezier(0.16,1,0.3,1) both' }}>
            <div className="px-5 py-4 border-b border-[var(--line)] flex justify-between items-center">
              <span className="text-[13px] font-medium">Live service health</span>
              <span className="font-mono text-[10px] text-[var(--muted)] uppercase"><span className="text-[var(--accent)]">●</span> Auto-refresh {lastChecked}</span>
            </div>
            {services.map((s, i) => (
              <div key={s.port} className="grid items-center gap-4 px-5 py-4 border-b border-[var(--line)] last:border-b-0 transition-all duration-300 hover:bg-[#F7F9FC] hover:translate-x-1.5 relative group" style={{ gridTemplateColumns: '42px 1fr auto' }}>
                <div className="font-mono text-[11px] text-[var(--muted)] transition-colors group-hover:text-[var(--accent)]">{String(i + 1).padStart(2, '0')}</div>
                <div>
                  <div className="text-sm font-medium">{s.name}</div>
                  <div className="text-xs text-[var(--muted)] mt-0.5">:{s.port}{s.latencyMs !== undefined ? ` · ${s.latencyMs}ms` : ''}</div>
                </div>
                <div className={`font-mono text-[10px] flex items-center gap-1.5 dot-pulse ${s.status === 'healthy' ? 'text-[var(--success)]' : 'text-[var(--danger)]'}`}>
                  {s.status === 'healthy' ? 'OPERATIONAL' : 'OFFLINE'}
                </div>
                {/* Bottom gradient line on hover */}
                <div className="absolute left-0 bottom-[-1px] h-px w-0 group-hover:w-full transition-all duration-400" style={{ background: 'linear-gradient(90deg, var(--accent), var(--cyan))' }} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Status Section */}
      <section className="py-24 border-t border-[var(--line)] relative">
        <div className="absolute right-0 top-0 w-px h-24" style={{ background: 'linear-gradient(var(--accent), transparent)', opacity: 0.18 }} />
        <div className="w-[min(1280px,calc(100%-64px))] mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-[0.7fr_1.3fr] gap-12 mb-14">
            <div className="font-mono text-xs text-[var(--muted)]">01 / SYSTEM STATUS</div>
            <div>
              <h2 className="text-[clamp(32px,4vw,48px)] leading-[1.08] tracking-[-0.045em] font-medium section-line">Operational visibility.</h2>
              <p className="mt-5 text-[var(--muted)] text-base leading-relaxed max-w-[650px]">Real-time service health polled from live /healthz endpoints. Alert feed streams from the alerting-service every 5 seconds.</p>
            </div>
          </div>

          {/* Status Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 border border-[var(--line)] bg-white overflow-hidden" style={{ boxShadow: '0 10px 35px rgba(17,19,16,0.04)' }}>
            {[
              { label: 'Services Online', value: `${healthyCount}/${services.length}`, state: healthyCount === services.length ? 'OPERATIONAL' : 'DEGRADED', color: healthyCount === services.length ? 'var(--success)' : 'var(--warning)' },
              { label: 'Avg Latency', value: `${Math.round(avgLatency)}ms`, state: 'MEASURED', color: 'var(--success)' },
              { label: 'Active Alerts', value: `${alerts.length}`, state: alerts.length > 0 ? 'PENDING' : 'CLEAR', color: alerts.length > 0 ? 'var(--warning)' : 'var(--success)' },
              { label: 'Pipeline Runs', value: `${recentResults.length}`, state: 'SESSION', color: 'var(--success)' },
            ].map((s, i) => (
              <div key={i} className="p-6 border-r border-[var(--line)] last:border-r-0 relative transition-colors hover:bg-[#F9FAF8] group overflow-hidden">
                <div className="absolute top-0 right-0 w-[90px] h-[90px] rounded-full translate-x-[30px] -translate-y-[30px] transition-transform group-hover:translate-x-0 group-hover:translate-y-0" style={{ background: `radial-gradient(circle, ${s.color}1f, transparent 65%)` }} />
                <div className="font-mono text-[10px] uppercase text-[var(--muted)]">{s.label}</div>
                <div className="text-[28px] font-medium my-5">{s.value}</div>
                <div className="font-mono text-[10px] flex items-center gap-1.5 dot-pulse" style={{ color: s.color }}>{s.state}</div>
                <div className="absolute bottom-0 left-6 right-6 h-0.5 origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-300" style={{ background: s.color }} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Live Alerts Feed */}
      <section className="py-24 border-t border-[var(--line)] relative">
        <div className="absolute right-0 top-0 w-px h-24" style={{ background: 'linear-gradient(var(--accent), transparent)', opacity: 0.18 }} />
        <div className="w-[min(1280px,calc(100%-64px))] mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-[0.7fr_1.3fr] gap-12 mb-14">
            <div className="font-mono text-xs text-[var(--muted)]">02 / LIVE ALERTS</div>
            <div>
              <h2 className="text-[clamp(32px,4vw,48px)] leading-[1.08] tracking-[-0.045em] font-medium section-line">See the system reason.</h2>
              <p className="mt-5 text-[var(--muted)] text-base leading-relaxed max-w-[650px]">Live alert feed from alerting-service polling GET /v1/tenants/{'{t}'}/alerts. Run pipeline tests to generate real events.</p>
            </div>
          </div>

          <div className="border border-[var(--line)] bg-white" style={{ boxShadow: '0 10px 35px rgba(17,19,16,0.04)' }}>
            {alerts.length === 0 && !alertError && (
              <div className="p-6 text-center text-sm text-[var(--muted)]">No active alerts — run a pipeline test to generate events</div>
            )}
            {alertError && <div className="p-6 text-sm text-[var(--danger)] font-mono">{alertError}</div>}
            {alerts.map(a => (
              <div key={a.alert_id} className="grid gap-6 px-5 py-[18px] border-b border-[var(--line)] last:border-b-0 text-[13px] transition-all duration-200 hover:bg-[#FAFBF9] hover:pl-[26px] relative overflow-hidden group" style={{ gridTemplateColumns: '110px 1fr auto' }}>
                <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-[var(--accent)] origin-center scale-y-0 group-hover:scale-y-100 transition-transform duration-250" />
                <div className="font-mono text-[11px] text-[var(--muted)]">{new Date(a.created_at).toLocaleTimeString()}</div>
                <div>{a.message_body}</div>
                <div className={`font-mono text-[10px] transition-all group-hover:tracking-wider ${a.action.includes('BLOCK') ? 'text-[var(--danger)]' : a.action.includes('CALLBACK') ? 'text-[var(--warning)]' : 'text-[var(--success)]'}`}>
                  {a.action.replace(/_/g, ' ')}
                </div>
              </div>
            ))}
          </div>

          {/* Recent Pipeline Results */}
          {recentResults.length > 0 && (
            <div className="mt-4 border border-[var(--line)] bg-white" style={{ boxShadow: '0 10px 35px rgba(17,19,16,0.04)' }}>
              <div className="px-5 py-3 border-b border-[var(--line)] font-mono text-[10px] text-[var(--muted)] uppercase">Recent Pipeline Results</div>
              {recentResults.slice(-5).reverse().map((r, i) => (
                <div key={i} className="grid gap-6 px-5 py-[18px] border-b border-[var(--line)] last:border-b-0 text-[13px] transition-all hover:bg-[#FAFBF9] hover:pl-[26px] relative overflow-hidden group" style={{ gridTemplateColumns: '110px 1fr auto' }}>
                  <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-[var(--accent)] origin-center scale-y-0 group-hover:scale-y-100 transition-transform" />
                  <div className="font-mono text-[11px] text-[var(--muted)]">{r.session_id?.slice(-8)}</div>
                  <div className="truncate">{r.explanation?.slice(0, 100)}</div>
                  <div className={`font-mono text-[10px] ${r.final_action === 'PROCEED' ? 'text-[var(--success)]' : r.final_action?.includes('CALLBACK') ? 'text-[var(--warning)]' : 'text-[var(--danger)]'}`}>
                    {r.risk_assessment ? `${Math.round(r.risk_assessment.risk_score * 100)}%` : '—'} · {r.final_action?.replace(/_/g, ' ')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </>
  );
};
