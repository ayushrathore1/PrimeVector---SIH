/**
 * api.ts — Single source of truth for ALL backend microservice calls.
 *
 * Every function here calls a REAL backend endpoint via the Vite proxy.
 * /api/{port}/path → http://localhost:{port}/path
 *
 * ZERO hardcoded data. Every return value comes from the network.
 */

// ─── Service Port Map ───────────────────────────────────────────────
const PORTS = {
  RISK_FUSION:       8000,
  FEATURE_EXTRACT:   8001,
  SPOOF_DETECT:      8002,
  ENROLLMENT:        8003,
  POLICY_ENGINE:     8004,
  ALERTING:          8005,
  ORCHESTRATOR:      8080,
} as const;

// ─── Helpers ────────────────────────────────────────────────────────
async function apiGet(port: number, path: string, headers?: Record<string, string>) {
  const res = await fetch(`/api/${port}${path}`, {
    method: 'GET',
    headers: { 'Accept': 'application/json', ...headers },
    signal: AbortSignal.timeout(8000),
  });
  return res;
}

async function apiPost(port: number, path: string, body: any, headers?: Record<string, string>) {
  const res = await fetch(`/api/${port}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', ...headers },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(60000),
  });
  return res;
}

async function apiPut(port: number, path: string, body: any, headers?: Record<string, string>) {
  const res = await fetch(`/api/${port}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', ...headers },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(8000),
  });
  return res;
}

// ─── Types ──────────────────────────────────────────────────────────
export interface HealthResult {
  name: string;
  port: number;
  status: 'healthy' | 'unhealthy' | 'checking';
  latencyMs?: number;
  extra?: Record<string, any>;
}

export interface PipelineRequest {
  session_id: string;
  tenant_id: string;
  subject_id: string;
  audio_pcm_base64: string;
  sample_rate_hz: number;
  channels: number;
  context_score: number;
  transcript: string;
}

export interface SignalResult {
  score: number;
  confidence: number;
  available: boolean;
  detail: string;
}

export interface RiskAssessment {
  call_session_id: string;
  risk_score: number;
  confidence: number;
  actions: string[];
  explanation: string;
  evaluated_at: string;
  degraded: boolean;
}

export interface PolicyDecision {
  call_session_id: string;
  tenant_id: string;
  risk_score: number;
  original_actions: string[];
  final_action: string;
  explanation: string;
  policy_version: number;
  decided_at: string;
}

export interface AlertEvent {
  event_id: string;
  channels_dispatched: number;
  message: string;
}

export interface PipelineResponse {
  session_id: string;
  tenant_id: string;
  degraded: boolean;
  extraction?: any;
  synthesis_signal?: SignalResult;
  speaker_match_signal?: SignalResult;
  content_risk_signal?: SignalResult;
  risk_assessment?: RiskAssessment;
  policy_decision?: PolicyDecision;
  alert_event?: AlertEvent;
  final_action: string;
  explanation: string;
}

export interface TenantPolicyConfig {
  tenant_id: string;
  callback_verification_threshold: number;
  supervisor_escalation_threshold: number;
  block_threshold: number;
  auto_block_enabled: boolean;
  policy_version: number;
  updated_at: string;
}

export interface PolicyAuditEntry {
  entry_id: string;
  tenant_id: string;
  actor: string;
  action: string;
  field_changed: string;
  old_value: string;
  new_value: string;
  timestamp: string;
}

export interface AlertOut {
  alert_id: string;
  event_id: string;
  call_session_id: string;
  tenant_id: string;
  action: string;
  message_body: string;
  created_at: string;
}

export interface VoiceprintStatus {
  status: string;
  voiceprint_id?: string;
  version?: number;
  sessions_completed?: number;
  sessions_remaining?: number;
  enrolled_at?: string;
  revoked_at?: string;
}

export interface EnrollmentAuditEntry {
  entry_id: string;
  action: string;
  actor_id: string;
  actor_role: string;
  timestamp: string;
  detail: string;
}

export interface AlertAuditEntry {
  entry_id: string;
  event_id: string;
  call_session_id: string;
  tenant_id: string;
  channel: string;
  recipient_hash: string;
  status: string;
  detail: string;
  timestamp: string;
}

// ─── Health Checks ──────────────────────────────────────────────────
const SERVICE_LIST: { name: string; port: number }[] = [
  { name: 'orchestrator',         port: PORTS.ORCHESTRATOR },
  { name: 'risk-fusion-engine',   port: PORTS.RISK_FUSION },
  { name: 'feature-extraction',   port: PORTS.FEATURE_EXTRACT },
  { name: 'spoof-detection',      port: PORTS.SPOOF_DETECT },
  { name: 'enrollment-service',   port: PORTS.ENROLLMENT },
  { name: 'policy-threshold-engine', port: PORTS.POLICY_ENGINE },
  { name: 'alerting-service',     port: PORTS.ALERTING },
];

export { SERVICE_LIST };

export async function checkServiceHealth(port: number): Promise<HealthResult> {
  const svc = SERVICE_LIST.find(s => s.port === port) || { name: `port-${port}`, port };
  const start = performance.now();
  try {
    const res = await apiGet(port, '/healthz');
    const latencyMs = Math.round(performance.now() - start);
    if (res.ok) {
      const data = await res.json();
      return { name: svc.name, port, status: 'healthy', latencyMs, extra: data };
    }
    return { name: svc.name, port, status: 'unhealthy', latencyMs };
  } catch {
    return { name: svc.name, port, status: 'unhealthy' };
  }
}

export async function checkAllHealth(): Promise<HealthResult[]> {
  return Promise.all(SERVICE_LIST.map(s => checkServiceHealth(s.port)));
}

// ─── Orchestrator Pipeline ──────────────────────────────────────────
export async function runPipeline(req: PipelineRequest): Promise<PipelineResponse> {
  const res = await apiPost(PORTS.ORCHESTRATOR, '/v1/pipeline/process', req);
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Pipeline failed (${res.status}): ${errText}`);
  }
  return res.json();
}

// ─── Risk Fusion Engine (Direct) ────────────────────────────────────
export async function assessRiskDirect(body: {
  call_session_id: string;
  tenant_id: string;
  synthesis_signal: { score: number; confidence: number; available: boolean; detail: string };
  speaker_match_signal: { score: number; confidence: number; available: boolean; detail: string };
  contextual_signal: { score: number; confidence: number; available: boolean; detail: string };
  content_risk_signal?: { score: number; confidence: number; available: boolean; detail: string };
}): Promise<RiskAssessment> {
  const res = await apiPost(PORTS.RISK_FUSION, '/v1/assess', body);
  if (!res.ok) throw new Error(`Fusion failed (${res.status})`);
  return res.json();
}

// ─── Enrollment Service ─────────────────────────────────────────────
export async function startEnrollment(
  tenantId: string, subjectId: string, actorId: string
): Promise<any> {
  const res = await apiPost(PORTS.ENROLLMENT, `/v1/tenants/${tenantId}/enroll`, {
    subject_id: subjectId,
  }, {
    'X-Actor-Id': actorId,
    'X-Actor-Role': 'tenant_admin',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `Enrollment failed (${res.status})`);
  }
  return res.json();
}

export async function submitEnrollmentSession(
  tenantId: string, subjectId: string, audioBase64: string, challengePhrase: string, actorId: string
): Promise<any> {
  const res = await apiPost(PORTS.ENROLLMENT, `/v1/tenants/${tenantId}/subjects/${subjectId}/session`, {
    audio_data: audioBase64,
    challenge_phrase: challengePhrase,
  }, {
    'X-Actor-Id': actorId,
    'X-Actor-Role': 'tenant_admin',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `Session submit failed (${res.status})`);
  }
  return res.json();
}

export async function getVoiceprintStatus(tenantId: string, subjectId: string): Promise<VoiceprintStatus> {
  const res = await apiGet(PORTS.ENROLLMENT, `/v1/tenants/${tenantId}/subjects/${subjectId}/status`);
  if (!res.ok) throw new Error(`Status check failed (${res.status})`);
  return res.json();
}

export async function revokeVoiceprint(
  tenantId: string, subjectId: string, reasonCode: string, reasonDetail: string, actorId: string
): Promise<any> {
  const res = await apiPost(PORTS.ENROLLMENT, `/v1/tenants/${tenantId}/subjects/${subjectId}/revoke`, {
    reason_code: reasonCode,
    reason_detail: reasonDetail,
  }, {
    'X-Actor-Id': actorId,
    'X-Actor-Role': 'tenant_admin',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `Revocation failed (${res.status})`);
  }
  return res.json();
}

export async function matchSpeaker(
  tenantId: string, subjectId: string, liveEmbedding: number[]
): Promise<any> {
  const res = await apiPost(PORTS.ENROLLMENT, `/v1/tenants/${tenantId}/subjects/${subjectId}/match`, {
    live_embedding: liveEmbedding,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `Match failed (${res.status})`);
  }
  return res.json();
}

export async function getEnrollmentAudit(
  tenantId: string, subjectId: string, actorId: string
): Promise<{ entries: EnrollmentAuditEntry[] }> {
  const res = await apiGet(PORTS.ENROLLMENT, `/v1/tenants/${tenantId}/subjects/${subjectId}/audit`, {
    'X-Actor-Id': actorId,
    'X-Actor-Role': 'tenant_admin',
  });
  if (!res.ok) throw new Error(`Audit fetch failed (${res.status})`);
  return res.json();
}

// ─── Policy Threshold Engine ────────────────────────────────────────
export async function getTenantPolicy(tenantId: string): Promise<TenantPolicyConfig> {
  const res = await apiGet(PORTS.POLICY_ENGINE, `/v1/tenants/${tenantId}/policy`, {
    'X-Tenant-Admin': 'true',
  });
  if (!res.ok) throw new Error(`Policy fetch failed (${res.status})`);
  return res.json();
}

export async function updateTenantPolicy(
  tenantId: string,
  updates: {
    callback_verification_threshold?: number;
    supervisor_escalation_threshold?: number;
    block_threshold?: number;
    auto_block_enabled?: boolean;
  },
  actorIdentity: string
): Promise<TenantPolicyConfig> {
  const res = await apiPut(PORTS.POLICY_ENGINE, `/v1/tenants/${tenantId}/policy`, updates, {
    'X-Tenant-Admin': 'true',
    'X-Actor-Identity': actorIdentity,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `Policy update failed (${res.status})`);
  }
  return res.json();
}

export async function getPolicyAuditLog(tenantId: string): Promise<PolicyAuditEntry[]> {
  const res = await apiGet(PORTS.POLICY_ENGINE, `/v1/tenants/${tenantId}/audit-log`, {
    'X-Tenant-Admin': 'true',
  });
  if (!res.ok) throw new Error(`Audit log fetch failed (${res.status})`);
  return res.json();
}

// ─── Alerting Service ───────────────────────────────────────────────
export async function getTenantAlerts(tenantId: string): Promise<{ alerts: AlertOut[] }> {
  const res = await apiGet(PORTS.ALERTING, `/v1/tenants/${tenantId}/alerts`);
  if (!res.ok) throw new Error(`Alerts fetch failed (${res.status})`);
  return res.json();
}

export async function getAlertAuditLog(tenantId: string): Promise<{ entries: AlertAuditEntry[] }> {
  const res = await apiGet(PORTS.ALERTING, `/v1/tenants/${tenantId}/audit`);
  if (!res.ok) throw new Error(`Alert audit failed (${res.status})`);
  return res.json();
}

// ─── Audio Utilities ────────────────────────────────────────────────
/** Generate a 1s 440Hz test tone as base64 16-bit PCM (fallback when no mic). */
export function generateTestTone(): string {
  const sampleRate = 16000;
  const nSamples = sampleRate; // 1 second
  const pcm16 = new Int16Array(nSamples);
  for (let i = 0; i < nSamples; i++) {
    pcm16[i] = Math.floor(32767 * 0.8 * Math.sin((2 * Math.PI * 440 * i) / sampleRate));
  }
  const bytes = new Uint8Array(pcm16.buffer);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}
