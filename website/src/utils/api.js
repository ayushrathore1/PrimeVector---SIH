/**
 * PrimeVector API Client
 *
 * Connects to the PrimeVector API Gateway for deepfake detection,
 * API key management, and usage tracking.
 */

const API_BASE = import.meta.env.VITE_API_BASE || '/api/8090';

// ── Detection ─────────────────────────────────────────────

// This is the input contract of the Dhwani checkpoint, not the format of an
// uploaded file. Browsers commonly produce WebM/Opus and uploads can be MP3,
// WAV, M4A, etc.; forwarding those container bytes as PCM corrupts inference.
const PCM_SAMPLE_RATE = 16000;

function encodeBase64(bytes) {
  const chunkSize = 0x8000;
  let binary = '';
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
  }
  return btoa(binary);
}

async function fileToPcmBase64(file) {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass || !window.OfflineAudioContext) {
    throw new Error('This browser cannot decode audio for secure local analysis. Use a current Chromium, Firefox, or Safari browser.');
  }

  const audioContext = new AudioContextClass();
  try {
    const encodedAudio = await file.arrayBuffer();
    const decoded = await audioContext.decodeAudioData(encodedAudio.slice(0));
    const frameCount = Math.max(1, Math.ceil(decoded.duration * PCM_SAMPLE_RATE));
    const offline = new OfflineAudioContext(1, frameCount, PCM_SAMPLE_RATE);
    const source = offline.createBufferSource();
    source.buffer = decoded;
    source.connect(offline.destination);
    source.start();

    const mono16k = await offline.startRendering();
    const pcm = new Int16Array(mono16k.length);
    const samples = mono16k.getChannelData(0);
    for (let index = 0; index < samples.length; index += 1) {
      const sample = Math.max(-1, Math.min(1, samples[index]));
      pcm[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
    }
    return encodeBase64(new Uint8Array(pcm.buffer));
  } catch (error) {
    throw new Error(`Could not decode ${file.name || 'the selected audio'} into 16 kHz mono PCM: ${error.message}`);
  } finally {
    await audioContext.close();
  }
}

// ── Direct Dhwani Model Inference ─────────────────────────

/**
 * Direct real-time streaming detection using Dhwani neural model.
 * Does NOT require tenant_id or subject_id.
 * Sends raw PCM audio chunk directly to Dhwani spoof detection endpoint.
 *
 * Tries API Gateway (/v1/detect) first; if unavailable, falls back to
 * direct spoof-detection-service on port 8002 (/api/8002/v1/detect)
 * or orchestrator on port 8080.
 */
export async function detectDhwaniLiveStream({
  audio_pcm_base64,
  sample_rate = 16000,
  apiKey = 'pv_live_demo_000000000000000000000000',
  sessionId = null,
}) {
  const startTime = performance.now();

  // Tier 1: Primary API Gateway (/v1/detect on port 8090)
  try {
    const resp = await fetch(`${API_BASE}/v1/detect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey || 'pv_live_demo_000000000000000000000000',
      },
      body: JSON.stringify({
        audio_pcm_base64,
        sample_rate,
        session_id: sessionId || undefined,
      }),
      signal: AbortSignal.timeout(4500),
    });

    if (resp.ok) {
      const data = await resp.json();
      const latencyMs = Math.round(performance.now() - startTime);
      const detailStr = String(data.detail || '');
      const isSilence = detailStr.includes('speech_status=SILENCE');
      const isNoise = detailStr.includes('speech_status=NOISE');
      const speechStatus = isSilence ? 'SILENCE' : isNoise ? 'NOISE' : 'VOICE';
      const rawScore = typeof data.spoof_score === 'number' ? data.spoof_score : (data.score ?? 0);
      const score = (isSilence || isNoise) ? 0.0 : rawScore;
      const confidence = isSilence ? 0.95 : isNoise ? 0.90 : (typeof data.confidence === 'number' ? data.confidence : 0);
      const verdict = isSilence ? 'NO_VOICE' : isNoise ? 'AMBIENT_NOISE' : (data.verdict || (score >= 0.5 ? 'FAKE' : 'REAL'));

      return {
        success: true,
        latencyMs,
        data: {
          spoofScore: score,
          confidence,
          verdict,
          speechStatus,
          modelVersion: data.model_version || 'Dhwani v2 (ResNet-18 + BiGRU)',
          modelArchitecture: data.model_architecture || 'ResNet-18 + SE + BiGRU + Attention',
          detail: data.raw_logit !== undefined ? `Logit: ${data.raw_logit}` : (data.detail || ''),
          policyAction: data.final_action || data.policy_action || null,
          preTransactionDefense: data.pre_transaction_defense || null,
          sessionAggregate: data.session_aggregate || null,
          serviceOrigin: 'API Gateway (:8090)',
          raw: data,
        },
      };
    }
  } catch {
    // Continue to Tier 2 fallback
  }

  // Tier 2: Direct Spoof Detection Service (/v1/detect on port 8002)
  try {
    const resp = await fetch('/api/8002/v1/detect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        call_session_id: `dhwani-live-${Date.now()}`,
        tenant_id: 'direct-dhwani-mic',
        audio_pcm_base64,
        audio_features: [],
      }),
      signal: AbortSignal.timeout(4500),
    });

    if (resp.ok) {
      const data = await resp.json();
      const latencyMs = Math.round(performance.now() - startTime);
      const detailStr = String(data.detail || '');
      const isSilence = detailStr.includes('speech_status=SILENCE');
      const isNoise = detailStr.includes('speech_status=NOISE');
      const speechStatus = isSilence ? 'SILENCE' : isNoise ? 'NOISE' : 'VOICE';
      const rawScore = typeof data.score === 'number' ? data.score : 0;
      const score = (isSilence || isNoise) ? 0.0 : rawScore;
      const confidence = isSilence ? 0.95 : isNoise ? 0.90 : (typeof data.confidence === 'number' ? data.confidence : 0);
      const verdict = isSilence ? 'NO_VOICE' : isNoise ? 'AMBIENT_NOISE' : (score >= 0.5 ? 'FAKE' : 'REAL');

      return {
        success: true,
        latencyMs,
        data: {
          spoofScore: score,
          confidence,
          verdict,
          speechStatus,
          modelVersion: 'Dhwani v2 Neural Model',
          modelArchitecture: 'Log-Mel Spectrogram + SE-BiGRU',
          detail: data.detail || '',
          serviceOrigin: 'Direct Spoof Service (:8002)',
          raw: data,
        },
      };
    }
  } catch {
    // Continue to Tier 3 fallback
  }

  // Tier 3: Orchestrator Pipeline (/v1/pipeline/process on port 8080/8085)
  try {
    const resp = await fetch('/api/8080/v1/pipeline/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: `direct-dhwani-${Date.now()}`,
        tenant_id: 'default-tenant',
        subject_id: 'anonymous-mic',
        audio_pcm_base64,
        sample_rate_hz: sample_rate,
        channels: 1,
      }),
      signal: AbortSignal.timeout(4500),
    });

    if (resp.ok) {
      const data = await resp.json();
      const latencyMs = Math.round(performance.now() - startTime);
      const synth = data.synthesis_signal || {};
      const score = typeof synth.score === 'number' ? synth.score : (data.risk_assessment?.risk_score ?? 0);
      const confidence = typeof synth.confidence === 'number' ? synth.confidence : 0;
      const verdict = score >= 0.5 ? 'FAKE' : 'REAL';

      return {
        success: true,
        latencyMs,
        data: {
          spoofScore: score,
          confidence,
          verdict,
          modelVersion: 'Dhwani v2 (Orchestrated)',
          modelArchitecture: synth.detail || 'Dhwani Neural Classifier',
          detail: data.explanation || '',
          serviceOrigin: 'Pipeline Orchestrator (:8080)',
          raw: data,
        },
      };
    }
  } catch {
    // All tiers exhausted
  }

  return {
    success: false,
    latencyMs: Math.round(performance.now() - startTime),
    error: 'Dhwani spoof detection backend is currently unreachable. Ensure either the API Gateway (:8090), Spoof Detection Service (:8002), or Orchestrator (:8080) is running.',
  };
}

/**
 * Detect deepfake in an audio file.
 */
export async function detectAudio(file, apiKey) {
  const startTime = performance.now();

  try {
    const base64 = await fileToPcmBase64(file);
    const resp = await fetch(`${API_BASE}/v1/detect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify({
        audio_pcm_base64: base64,
        sample_rate: PCM_SAMPLE_RATE,
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
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      return { success: false, error: err.detail?.message || err.detail || 'Failed to fetch usage' };
    }
    return { success: true, data: await resp.json() };
  } catch (err) {
    return { success: false, error: err.message };
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
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      return { success: false, error: err.detail?.message || err.detail || 'Failed to fetch usage history' };
    }
    return { success: true, data: await resp.json() };
  } catch (err) {
    return { success: false, error: err.message };
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
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      return { success: false, error: err.detail?.message || err.detail || 'Failed to fetch detection logs' };
    }
    return { success: true, data: await resp.json() };
  } catch (err) {
    return { success: false, error: err.message };
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
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      return { success: false, error: err.detail?.message || err.detail || 'Failed to list API keys' };
    }
    return { success: true, data: await resp.json() };
  } catch (err) {
    return { success: false, error: err.message };
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
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      return { success: false, error: err.detail?.message || err.detail || 'Failed to create API key' };
    }
    return { success: true, data: await resp.json() };
  } catch (err) {
    return { success: false, error: err.message };
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
    if (!resp.ok && resp.status !== 204) {
      const err = await resp.json().catch(() => ({}));
      return { success: false, error: err.detail?.message || err.detail || 'Failed to revoke API key' };
    }
    return { success: true };
  } catch (err) {
    return { success: false, error: err.message };
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
  { id: 'risk-fusion', name: 'Risk Fusion Engine', port: 8000, healthPath: '/healthz', location: 'local', desc: 'Noisy-OR multi-signal risk fusion with deterministic scoring' },
  { id: 'feature-extract', name: 'Feature Extraction Service', port: 8001, healthPath: '/healthz', location: 'colab', desc: 'Log-Mel + Delta + Delta² extraction through the configured ngrok tunnel' },
  { id: 'spoof-detection', name: 'Spoof Detection / Dhwani', port: 8002, healthPath: '/healthz', location: 'local', desc: 'Dhwani v2 neural deepfake classifier' },
  { id: 'enrollment', name: 'Enrollment Service', port: 8003, healthPath: '/healthz', location: 'colab', desc: 'Voiceprint enrollment and matching through the configured ngrok tunnel' },
  { id: 'policy-threshold', name: 'Policy Threshold Engine', port: 8004, healthPath: '/healthz', location: 'local', desc: 'Tenant policy evaluation and action recommendation' },
  { id: 'alerting', name: 'Alerting Service', port: 8005, healthPath: '/healthz', location: 'local', desc: 'Real-time event dispatch' },
  { id: 'orchestrator', name: 'Pipeline Orchestrator', port: 8080, healthPath: '/healthz', location: 'local', desc: 'End-to-end streaming pipeline coordinator' },
  { id: 'ingestion-gateway', name: 'Ingestion Gateway', port: 50051, healthPath: null, location: 'local', desc: 'gRPC-only audio ingestion; HTTP health is not exposed' },
  { id: 'api-gateway', name: 'API Gateway', port: 8090, healthPath: '/v1/health', location: 'local', desc: 'Public REST API, authentication, and metering' },
];

// ── Service Health Check ──────────────────────────────────

export async function checkServiceHealth(service) {
  if (!service.healthPath) return { status: 'unobservable', statusCode: null, latencyMs: null };
  const startTime = performance.now();
  try {
    const resp = await fetch(`/api/${service.port}${service.healthPath}`, {
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
 * Used by the Detector's embedded live-analysis panel to process PCM windows.
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
