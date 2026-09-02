import React, { useState } from 'react';
import { startEnrollment, submitEnrollmentSession, getVoiceprintStatus, revokeVoiceprint, getEnrollmentAudit, generateTestTone, VoiceprintStatus, EnrollmentAuditEntry } from '../api';

interface EnrollmentPageProps { tenantId: string; }

export const EnrollmentPage: React.FC<EnrollmentPageProps> = ({ tenantId }) => {
  const [activeTab, setActiveTab] = useState<'status' | 'enroll' | 'revoke' | 'audit'>('status');
  const [actorId, setActorId] = useState('admin-001');
  const [subjectId, setSubjectId] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [enrollResult, setEnrollResult] = useState<any>(null);
  const [statusResult, setStatusResult] = useState<VoiceprintStatus | null>(null);
  const [sessionResult, setSessionResult] = useState<any>(null);
  const [revokeReason, setRevokeReason] = useState('USER_REQUEST');
  const [revokeDetail, setRevokeDetail] = useState('');
  const [auditEntries, setAuditEntries] = useState<EnrollmentAuditEntry[]>([]);
  const [challengePhrase, setChallengePhrase] = useState('');

  const doAction = async (fn: () => Promise<void>) => {
    setLoading(true); setMessage(null);
    try { await fn(); } catch (e: any) { setMessage({ type: 'error', text: e.message }); }
    setLoading(false);
  };

  const TABS = [
    { id: 'status' as const, label: 'Check Status' },
    { id: 'enroll' as const, label: 'Start Enrollment' },
    { id: 'revoke' as const, label: 'Revoke' },
    { id: 'audit' as const, label: 'Audit Log' },
  ];

  return (
    <section className="py-24 relative">
      <div className="absolute right-0 top-0 w-px h-24" style={{ background: 'linear-gradient(var(--accent), transparent)', opacity: 0.18 }} />
      <div className="w-[min(1280px,calc(100%-64px))] mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-[0.7fr_1.3fr] gap-12 mb-14">
          <div className="font-mono text-xs text-[var(--muted)]">04 / ENROLLMENT</div>
          <div>
            <h2 className="text-[clamp(32px,4vw,48px)] leading-[1.08] tracking-[-0.045em] font-medium section-line">Voiceprint management.</h2>
            <p className="mt-5 text-[var(--muted)] text-base leading-relaxed max-w-[650px]">Multi-session enrollment, challenge-response liveness, RBAC-gated operations, and immutable audit trails. All calls hit enrollment-service :8003.</p>
          </div>
        </div>

        {/* Shared Inputs */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div><label className="font-mono text-[10px] text-[var(--muted)] uppercase mb-1 block">Tenant ID</label><input value={tenantId} disabled className="w-full opacity-60" /></div>
          <div><label className="font-mono text-[10px] text-[var(--muted)] uppercase mb-1 block">Subject ID</label><input value={subjectId} onChange={e => setSubjectId(e.target.value)} placeholder="e.g. subject-001" className="w-full" /></div>
          <div><label className="font-mono text-[10px] text-[var(--muted)] uppercase mb-1 block">Actor ID (Admin)</label><input value={actorId} onChange={e => setActorId(e.target.value)} className="w-full" /></div>
        </div>

        {/* Tab Nav */}
        <div className="border border-[var(--line)] bg-white flex mb-4">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)}
              className={`flex-1 py-3 font-mono text-xs cursor-pointer transition-all ${activeTab === t.id ? 'text-[var(--ink)] bg-[#F0F1EC] font-medium' : 'text-[var(--muted)] hover:text-[var(--ink)] hover:bg-[#F5F6F2]'}`}>
              {t.label}
            </button>
          ))}
        </div>

        {message && (
          <div className={`p-3 mb-4 text-xs font-mono border ${message.type === 'success' ? 'bg-[rgba(22,121,74,0.04)] text-[var(--success)] border-[var(--success)]/20' : 'bg-[rgba(180,35,24,0.04)] text-[var(--danger)] border-[var(--danger)]/20'}`}>
            {message.text}
          </div>
        )}

        <div className="bg-white border border-[var(--line)] rounded-xl p-6 card-accent" style={{ boxShadow: '0 12px 35px rgba(17,19,16,0.035)' }}>
          {activeTab === 'status' && (
            <div className="space-y-4">
              <p className="text-sm text-[var(--muted)]">GET /v1/tenants/{'{t}'}/subjects/{'{s}'}/status — returns NOT_ENROLLED | ENROLLED | ENROLLMENT_REVOKED</p>
              <button onClick={() => doAction(async () => { if (!subjectId.trim()) throw new Error('Subject ID required'); const r = await getVoiceprintStatus(tenantId, subjectId.trim()); setStatusResult(r); })} disabled={loading}
                className="min-h-[44px] px-5 rounded-lg text-sm font-medium text-white cursor-pointer disabled:opacity-50" style={{ background: 'var(--ink)', border: '1px solid var(--ink)' }}>
                {loading ? 'Checking...' : 'Check Status'}
              </button>
              {statusResult && (
                <div className="border border-[var(--line)] bg-[#F7F9FC] p-4 space-y-2">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div><span className="font-mono text-[10px] text-[var(--muted)]">Status:</span> <span className={`font-medium ${statusResult.status === 'ENROLLED' ? 'text-[var(--success)]' : statusResult.status === 'ENROLLMENT_REVOKED' ? 'text-[var(--danger)]' : 'text-[var(--warning)]'}`}>{statusResult.status}</span></div>
                    {statusResult.voiceprint_id && <div><span className="font-mono text-[10px] text-[var(--muted)]">Voiceprint:</span> <span className="font-mono text-xs">{statusResult.voiceprint_id}</span></div>}
                    {statusResult.sessions_completed !== undefined && <div><span className="font-mono text-[10px] text-[var(--muted)]">Sessions:</span> <span>{statusResult.sessions_completed} done, {statusResult.sessions_remaining} remaining</span></div>}
                    {statusResult.enrolled_at && <div><span className="font-mono text-[10px] text-[var(--muted)]">Enrolled:</span> <span>{statusResult.enrolled_at}</span></div>}
                    {statusResult.revoked_at && <div><span className="font-mono text-[10px] text-[var(--muted)]">Revoked:</span> <span>{statusResult.revoked_at}</span></div>}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'enroll' && (
            <div className="space-y-4">
              <p className="text-sm text-[var(--muted)]">POST /v1/tenants/{'{t}'}/enroll — starts multi-session enrollment. Requires tenant_admin role.</p>
              <button onClick={() => doAction(async () => { if (!subjectId.trim()) throw new Error('Subject ID required'); const r = await startEnrollment(tenantId, subjectId.trim(), actorId); setEnrollResult(r); setChallengePhrase(r.challenge_phrase || ''); setMessage({ type: 'success', text: r.message || 'Enrollment started' }); })} disabled={loading}
                className="min-h-[44px] px-5 rounded-lg text-sm font-medium text-white cursor-pointer disabled:opacity-50" style={{ background: 'var(--ink)', border: '1px solid var(--ink)' }}>
                {loading ? 'Starting...' : 'Start Enrollment'}
              </button>
              {enrollResult && (
                <div className="border border-[var(--line)] bg-[#F7F9FC] p-4 text-sm space-y-1">
                  <div><span className="font-mono text-[10px] text-[var(--muted)]">Voiceprint ID:</span> <span className="font-mono text-xs">{enrollResult.voiceprint_id}</span></div>
                  <div><span className="font-mono text-[10px] text-[var(--muted)]">Challenge:</span> <span className="text-[var(--accent)]">"{enrollResult.challenge_phrase}"</span></div>
                </div>
              )}
              {challengePhrase && (
                <div className="pt-4 border-t border-[var(--line)] space-y-3">
                  <div className="font-mono text-[10px] text-[var(--muted)] uppercase">Submit Capture Session</div>
                  <p className="text-xs text-[var(--muted)]">Challenge: <span className="text-[var(--accent)]">"{challengePhrase}"</span> — test tone audio will be used.</p>
                  <button onClick={() => doAction(async () => { if (!subjectId.trim()) throw new Error('Subject ID required'); const r = await submitEnrollmentSession(tenantId, subjectId.trim(), generateTestTone(), challengePhrase, actorId); setSessionResult(r); setChallengePhrase(r.next_challenge_phrase || ''); setMessage({ type: 'success', text: r.message || 'Session submitted' }); })} disabled={loading}
                    className="min-h-[40px] px-5 rounded-lg text-sm font-medium text-white cursor-pointer disabled:opacity-50 bg-[var(--success)] border border-[var(--success)]">
                    {loading ? 'Submitting...' : 'Submit Session'}
                  </button>
                  {sessionResult && <div className="text-xs font-mono text-[var(--muted)]">Sessions: {sessionResult.sessions_completed} done, {sessionResult.sessions_remaining} remaining — {sessionResult.status}</div>}
                </div>
              )}
            </div>
          )}

          {activeTab === 'revoke' && (
            <div className="space-y-4">
              <p className="text-sm text-[var(--muted)]">POST /v1/tenants/{'{t}'}/subjects/{'{s}'}/revoke — creates immutable audit record. ⚠️ Compliance-relevant.</p>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="font-mono text-[10px] text-[var(--muted)] uppercase mb-1 block">Reason Code</label>
                  <select value={revokeReason} onChange={e => setRevokeReason(e.target.value)} className="w-full">
                    <option value="USER_REQUEST">USER_REQUEST</option><option value="SECURITY_CONCERN">SECURITY_CONCERN</option><option value="DATA_DELETION">DATA_DELETION</option><option value="ADMINISTRATIVE">ADMINISTRATIVE</option>
                  </select></div>
                <div><label className="font-mono text-[10px] text-[var(--muted)] uppercase mb-1 block">Detail</label><input value={revokeDetail} onChange={e => setRevokeDetail(e.target.value)} placeholder="Reason for revocation..." className="w-full" /></div>
              </div>
              <button onClick={() => doAction(async () => { if (!subjectId.trim()) throw new Error('Subject ID required'); await revokeVoiceprint(tenantId, subjectId.trim(), revokeReason, revokeDetail || 'Revoked from dashboard', actorId); setMessage({ type: 'success', text: 'Voiceprint revoked. Audit log entry created.' }); })} disabled={loading}
                className="min-h-[44px] px-5 rounded-lg text-sm font-medium text-white cursor-pointer disabled:opacity-50 bg-[var(--danger)] border border-[var(--danger)]">
                {loading ? 'Revoking...' : 'Revoke Voiceprint'}
              </button>
            </div>
          )}

          {activeTab === 'audit' && (
            <div className="space-y-4">
              <p className="text-sm text-[var(--muted)]">GET /v1/tenants/{'{t}'}/subjects/{'{s}'}/audit — immutable enrollment lifecycle audit trail.</p>
              <button onClick={() => doAction(async () => { if (!subjectId.trim()) throw new Error('Subject ID required'); const r = await getEnrollmentAudit(tenantId, subjectId.trim(), actorId); setAuditEntries(r.entries || []); })} disabled={loading}
                className="min-h-[44px] px-5 rounded-lg text-sm font-medium text-white cursor-pointer disabled:opacity-50" style={{ background: 'var(--ink)', border: '1px solid var(--ink)' }}>
                {loading ? 'Loading...' : 'Load Audit Log'}
              </button>
              {auditEntries.length > 0 && (
                <div className="border border-[var(--line)] overflow-x-auto">
                  <table className="w-full text-[11px] font-mono">
                    <thead><tr className="text-[var(--muted)] border-b border-[var(--line)] bg-[#F0F1EC]">
                      <th className="text-left py-2 px-3">Action</th><th className="text-left py-2 px-3">Actor</th><th className="text-left py-2 px-3">Detail</th><th className="text-left py-2 px-3">Timestamp</th>
                    </tr></thead>
                    <tbody>{auditEntries.map(e => (
                      <tr key={e.entry_id} className="border-b border-[var(--line)] hover:bg-[#F7F9FC] transition-colors">
                        <td className="py-2 px-3 text-[var(--accent)]">{e.action}</td>
                        <td className="py-2 px-3 text-[var(--muted)]">{e.actor_id}</td>
                        <td className="py-2 px-3 text-[var(--muted)] max-w-[200px] truncate">{e.detail}</td>
                        <td className="py-2 px-3 text-[var(--muted)]">{e.timestamp}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              )}
              {auditEntries.length === 0 && !loading && <div className="text-xs text-[var(--muted)] text-center py-4">No audit entries — enroll a subject first</div>}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
