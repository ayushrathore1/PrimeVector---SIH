/**
 * PrimeVector API Client
 *
 * Connects to the PrimeVector API Gateway for deepfake detection,
 * API key management, and usage tracking.
 */

const API_BASE = import.meta.env.VITE_API_BASE || '/api/8090';

// ── Detection ─────────────────────────────────────────────

/**
 * Convert an audio File to base64-encoded PCM string.
 */
async function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = reader.result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

/**
 * Detect deepfake in an audio file.
 */
export async function detectAudio(file, apiKey) {
  const startTime = performance.now();
  const base64 = await fileToBase64(file);

  try {
    const resp = await fetch(`${API_BASE}/v1/detect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify({
        audio_pcm_base64: base64,
        sample_rate: 16000,
      }),
    });

    const latencyMs = Math.round(performance.now() - startTime);

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      return { success: false, statusCode: resp.status, latencyMs, error: err };
    }

    const data = await resp.json();
    return { success: true, statusCode: resp.status, latencyMs, data };
  } catch (err) {
    return {
      success: false,
      statusCode: 0,
      latencyMs: Math.round(performance.now() - startTime),
      error: err.message,
    };
  }
}

/**
 * Detect deepfake from base64 audio.
 */
export async function detectAudioBase64(base64, apiKey, sampleRate = 16000) {
  try {
    const resp = await fetch(`${API_BASE}/v1/detect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify({
        audio_pcm_base64: base64,
        sample_rate: sampleRate,
      }),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      return { success: false, error: err };
    }

    return { success: true, data: await resp.json() };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

// ── Usage ─────────────────────────────────────────────────

/**
 * Get current usage stats.
 */
export async function getUsage(apiKey) {
  try {
    const resp = await fetch(`${API_BASE}/v1/usage`, {
      headers: { 'X-API-Key': apiKey },
    });
    if (!resp.ok) return { success: false };
    return { success: true, data: await resp.json() };
  } catch {
    return { success: false };
  }
}

/**
 * Get usage history for a date range.
 */
export async function getUsageHistory(apiKey, startDate, endDate) {
  const params = new URLSearchParams();
  if (startDate) params.set('start_date', startDate);
  if (endDate) params.set('end_date', endDate);

  try {
    const resp = await fetch(`${API_BASE}/v1/usage/history?${params}`, {
      headers: { 'X-API-Key': apiKey },
    });
    if (!resp.ok) return { success: false };
    return { success: true, data: await resp.json() };
  } catch {
    return { success: false };
  }
}

/**
 * Get recent detections.
 */
export async function getRecentDetections(apiKey, limit = 50) {
  try {
    const resp = await fetch(`${API_BASE}/v1/usage/detections?limit=${limit}`, {
      headers: { 'X-API-Key': apiKey },
    });
    if (!resp.ok) return { success: false };
    return { success: true, data: await resp.json() };
  } catch {
    return { success: false };
  }
}

// ── API Keys ──────────────────────────────────────────────

/**
 * List API keys for the org.
 */
export async function listApiKeys(apiKey) {
  try {
    const resp = await fetch(`${API_BASE}/v1/keys`, {
      headers: { 'X-API-Key': apiKey },
    });
    if (!resp.ok) return { success: false };
    return { success: true, data: await resp.json() };
  } catch {
    return { success: false };
  }
}

/**
 * Create a new API key.
 */
export async function createApiKey(apiKey, name, tier = 'free') {
  try {
    const resp = await fetch(`${API_BASE}/v1/keys`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify({ name, tier }),
    });
    if (!resp.ok) return { success: false };
    return { success: true, data: await resp.json() };
  } catch {
    return { success: false };
  }
}

/**
 * Revoke an API key.
 */
export async function revokeApiKey(apiKey, keyId) {
  try {
    const resp = await fetch(`${API_BASE}/v1/keys/${keyId}`, {
      method: 'DELETE',
      headers: { 'X-API-Key': apiKey },
    });
    return { success: resp.ok || resp.status === 204 };
  } catch {
    return { success: false };
  }
}

// ── Health ─────────────────────────────────────────────────

/**
 * Check API gateway health.
 */
export async function checkHealth() {
  try {
    const resp = await fetch(`${API_BASE}/v1/health`);
    if (!resp.ok) return { success: false };
    return { success: true, data: await resp.json() };
  } catch {
    return { success: false };
  }
}

// ── Microservices Registry ────────────────────────────────

/**
 * Complete registry of PrimeVector platform microservices.
 * Each entry maps to a containerized service with its health endpoint.
 */
export const MICROSERVICES = [
  { id: 'risk-fusion',       name: 'Risk Fusion Engine',          port: 8000, desc: 'Noisy-OR multi-signal risk fusion with deterministic scoring' },
  { id: 'feature-extract',   name: 'Feature Extraction Service',  port: 8001, desc: 'Log-Mel + Delta + Delta² 3-channel spectrogram extraction' },
  { id: 'spoof-detection',   name: 'Spoof Detection / DhVani',    port: 8002, desc: 'DhVani v2 neural deepfake classifier (ResNet-SE + BiGRU)' },
  { id: 'enrollment',        name: 'Enrollment Service',          port: 8003, desc: 'Voiceprint enrollment, matching & speaker verification' },
  { id: 'policy-threshold',  name: 'Policy Threshold Engine',     port: 8004, desc: 'Configurable per-tenant risk thresholds & auto-block gate' },
  { id: 'alerting',          name: 'Alerting Service',            port: 8005, desc: 'Real-time alert dispatch (webhook, email, SMS, Slack)' },
  { id: 'orchestrator',      name: 'Pipeline Orchestrator',       port: 8080, desc: 'End-to-end call processing pipeline coordinator' },
  { id: 'ingestion-gateway', name: 'Ingestion Gateway',           port: 8006, desc: 'Go-based high-throughput audio frame ingestion endpoint' },
  { id: 'api-gateway',       name: 'API Gateway',                 port: 8090, desc: 'Public REST API for detection, keys, usage & metering' },
];

// ── Service Health Check ──────────────────────────────────

export async function checkServiceHealth(port) {
  const startTime = performance.now();
  try {
    const resp = await fetch(`/api/${port}/healthz`, {
      signal: AbortSignal.timeout(2500),
    });
    const latency = Math.round(performance.now() - startTime);
    if (resp.ok) {
      return { status: 'online', statusCode: resp.status, latencyMs: latency, data: await resp.json() };
    }
    return { status: 'degraded', statusCode: resp.status, latencyMs: latency };
  } catch {
    return { status: 'offline', statusCode: 0, latencyMs: Math.round(performance.now() - startTime) };
  }
}

// ── Orchestrator Pipeline ─────────────────────────────────

/**
 * Execute a full pipeline process via the orchestrator.
 * Used by the LiveStreamPage to process real call data through the pipeline.
 */
export async function executePipelineProcess(payload) {
  const startTime = performance.now();
  try {
    const resp = await fetch('/api/8080/v1/pipeline/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const latencyMs = Math.round(performance.now() - startTime);
    if (!resp.ok) {
      return { success: false, latencyMs, error: `HTTP ${resp.status}` };
    }
    return { success: true, latencyMs, data: await resp.json() };
  } catch (err) {
    return { success: false, latencyMs: Math.round(performance.now() - startTime), error: err.message };
  }
}
