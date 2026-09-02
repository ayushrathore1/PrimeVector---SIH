import React, { useState, useEffect, useCallback } from 'react';
import { getTenantPolicy, updateTenantPolicy, getPolicyAuditLog, TenantPolicyConfig, PolicyAuditEntry } from '../api';

interface PolicyPageProps { tenantId: string; }

export const PolicyPage: React.FC<PolicyPageProps> = ({ tenantId }) => {
  const [policy, setPolicy] = useState<TenantPolicyConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [auditLog, setAuditLog] = useState<PolicyAuditEntry[]>([]);
  const [showAudit, setShowAudit] = useState(false);
  const [actorIdentity, setActorIdentity] = useState('admin-001');
  const [cbThreshold, setCbThreshold] = useState(0.4);
  const [supThreshold, setSupThreshold] = useState(0.7);
  const [blockThreshold, setBlockThreshold] = useState(0.9);
  const [autoBlock, setAutoBlock] = useState(false);

  const fetchPolicy = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const p = await getTenantPolicy(tenantId);
      setPolicy(p); setCbThreshold(p.callback_verification_threshold); setSupThreshold(p.supervisor_escalation_threshold); setBlockThreshold(p.block_threshold); setAutoBlock(p.auto_block_enabled);
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  }, [tenantId]);

  useEffect(() => { fetchPolicy(); }, [fetchPolicy]);

  const handleSave = async () => {
    setSaving(true); setError(''); setSuccess('');
    try {
      const updated = await updateTenantPolicy(tenantId, { callback_verification_threshold: cbThreshold, supervisor_escalation_threshold: supThreshold, block_threshold: blockThreshold, auto_block_enabled: autoBlock }, actorIdentity);
      setPolicy(updated); setSuccess(`Policy updated to v${updated.policy_version}`);
      setTimeout(() => setSuccess(''), 4000);
    } catch (e: any) { setError(e.message); }
    setSaving(false);
  };

  const loadAudit = async () => {
    try { const entries = await getPolicyAuditLog(tenantId); setAuditLog(entries); setShowAudit(true); } catch (e: any) { setError(e.message); }
  };

  const zones = [
    { label: 'PROCEED', color: 'var(--success)', start: 0, end: cbThreshold },
    { label: 'CALLBACK', color: 'var(--warning)', start: cbThreshold, end: supThreshold },
    { label: 'ESCALATION', color: '#D97706', start: supThreshold, end: blockThreshold },
    { label: autoBlock ? 'BLOCK' : 'DISABLED', color: autoBlock ? 'var(--danger)' : 'var(--muted)', start: blockThreshold, end: 1 },
  ];

  return (
    <section className="py-24 relative">
      <div className="absolute right-0 top-0 w-px h-24" style={{ background: 'linear-gradient(var(--accent), transparent)', opacity: 0.18 }} />
      <div className="w-[min(1280px,calc(100%-64px))] mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-[0.7fr_1.3fr] gap-12 mb-14">
          <div className="font-mono text-xs text-[var(--muted)]">05 / POLICY CONFIG</div>
          <div>
            <h2 className="text-[clamp(32px,4vw,48px)] leading-[1.08] tracking-[-0.045em] font-medium section-line">Configurable thresholds.</h2>
            <p className="mt-5 text-[var(--muted)] text-base leading-relaxed max-w-[650px]">Per-tenant policy rules applied downstream of risk fusion. auto_block_enabled defaults to false — the system never blocks without explicit opt-in (DESIGN.md §4.7).</p>
          </div>
        </div>

        {error && <div className="p-3 mb-4 text-xs font-mono border bg-[rgba(180,35,24,0.04)] text-[var(--danger)] border-[var(--danger)]/20">{error}</div>}
        {success && <div className="p-3 mb-4 text-xs font-mono border bg-[rgba(22,121,74,0.04)] text-[var(--success)] border-[var(--success)]/20">{success}</div>}

        {/* Risk Zone Visualizer */}
        <div className="bg-white border border-[var(--line)] rounded-xl p-6 mb-4 panel-bar" style={{ boxShadow: '0 12px 35px rgba(17,19,16,0.035)' }}>
          <div className="font-mono text-[10px] text-[var(--muted)] uppercase mb-4">Policy Risk Zones</div>
          <div className="h-10 rounded-lg overflow-hidden flex">
            {zones.map((z, i) => (
              <div key={i} style={{ width: `${(z.end - z.start) * 100}%`, backgroundColor: z.color }} className="flex items-center justify-center text-[9px] font-mono font-bold text-white/90 transition-all duration-300">
                {(z.end - z.start) >= 0.08 && z.label}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-1 text-[9px] font-mono text-[var(--muted)]">
            <span>0.0</span><span>{cbThreshold.toFixed(2)}</span><span>{supThreshold.toFixed(2)}</span><span>{blockThreshold.toFixed(2)}</span><span>1.0</span>
          </div>
        </div>

        {/* Threshold Controls */}
        <div className="bg-white border border-[var(--line)] rounded-xl p-6 card-accent space-y-5" style={{ boxShadow: '0 12px 35px rgba(17,19,16,0.035)' }}>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="font-mono text-[10px] text-[var(--muted)] uppercase mb-1 block">Actor Identity</label><input value={actorIdentity} onChange={e => setActorIdentity(e.target.value)} className="w-full" /></div>
            {policy && <div className="flex items-end text-[10px] font-mono text-[var(--muted)]">Policy v{policy.policy_version} · Updated: {new Date(policy.updated_at).toLocaleString()}</div>}
          </div>

          {[
            { label: 'Callback Verification Threshold', val: cbThreshold, set: setCbThreshold, color: 'var(--warning)' },
            { label: 'Supervisor Escalation Threshold', val: supThreshold, set: setSupThreshold, color: '#D97706' },
            { label: 'Block Threshold', val: blockThreshold, set: setBlockThreshold, color: 'var(--danger)' },
          ].map((t, i) => (
            <div key={i}>
              <div className="flex justify-between items-center mb-1">
                <label className="text-sm text-[var(--muted)]">{t.label}</label>
                <span className="text-sm font-mono font-bold" style={{ color: t.color }}>{t.val.toFixed(2)}</span>
              </div>
              <input type="range" min="0" max="1" step="0.01" value={t.val} onChange={e => t.set(parseFloat(e.target.value))} className="w-full accent-[var(--accent)] bg-transparent border-none p-0" />
            </div>
          ))}

          {/* Auto-Block Toggle */}
          <div className="flex items-start gap-3 p-4 bg-[#F0F1EC] rounded-lg border border-[var(--line)]">
            <button onClick={() => setAutoBlock(!autoBlock)} className={`mt-0.5 w-10 h-5 rounded-full p-0.5 cursor-pointer transition-colors ${autoBlock ? 'bg-[var(--danger)]' : 'bg-[var(--line)]'}`}>
              <div className={`w-4 h-4 rounded-full bg-white transition-transform shadow-sm ${autoBlock ? 'translate-x-5' : ''}`} />
            </button>
            <div>
              <div className="text-sm font-medium">Auto-Block Enabled</div>
              <div className="text-[11px] text-[var(--muted)] mt-0.5">
                {autoBlock ? <span className="text-[var(--danger)]">⚠ BLOCK_PENDING_VERIFICATION fires at risk_score ≥ {blockThreshold.toFixed(2)}</span> : <span>Disabled — NEVER outputs BLOCK_PENDING_VERIFICATION (DESIGN.md §4.7)</span>}
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={handleSave} disabled={saving} className="min-h-[44px] px-6 rounded-lg text-sm font-medium text-white cursor-pointer disabled:opacity-50 transition-all" style={{ background: 'var(--ink)', border: '1px solid var(--ink)', boxShadow: '0 10px 28px rgba(17,19,16,0.12)' }}>
              {saving ? 'Saving...' : 'Save Policy'}
            </button>
            <button onClick={loadAudit} className="min-h-[44px] px-6 rounded-lg border border-[var(--line)] text-sm font-medium bg-white cursor-pointer hover:-translate-y-px transition-transform">
              View Audit Log
            </button>
            <button onClick={fetchPolicy} disabled={loading} className="min-h-[44px] px-4 rounded-lg border border-[var(--line)] text-sm bg-white cursor-pointer hover:-translate-y-px transition-transform disabled:opacity-50">
              {loading ? '↻' : '↻ Reload'}
            </button>
          </div>
        </div>

        {/* Audit Log */}
        {showAudit && (
          <div className="mt-4 bg-white border border-[var(--line)] rounded-xl overflow-hidden" style={{ boxShadow: '0 12px 35px rgba(17,19,16,0.035)' }}>
            <div className="px-5 py-3 border-b border-[var(--line)] font-mono text-[10px] text-[var(--muted)] uppercase">Policy Audit Log — {auditLog.length} entries</div>
            {auditLog.length === 0 ? (
              <div className="p-6 text-xs text-[var(--muted)] text-center">No audit entries — modify the policy to create records</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-[11px] font-mono">
                  <thead><tr className="text-[var(--muted)] border-b border-[var(--line)] bg-[#F0F1EC]">
                    <th className="text-left py-2 px-3">Action</th><th className="text-left py-2 px-3">Field</th><th className="text-left py-2 px-3">Old → New</th><th className="text-left py-2 px-3">Actor</th><th className="text-left py-2 px-3">Timestamp</th>
                  </tr></thead>
                  <tbody>{auditLog.map(e => (
                    <tr key={e.entry_id} className="border-b border-[var(--line)] hover:bg-[#F7F9FC] transition-colors">
                      <td className="py-2 px-3 text-[var(--accent)]">{e.action}</td>
                      <td className="py-2 px-3">{e.field_changed}</td>
                      <td className="py-2 px-3"><span className="text-[var(--danger)]">{e.old_value}</span> → <span className="text-[var(--success)]">{e.new_value}</span></td>
                      <td className="py-2 px-3 text-[var(--muted)]">{e.actor}</td>
                      <td className="py-2 px-3 text-[var(--muted)]">{new Date(e.timestamp).toLocaleString()}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
};
