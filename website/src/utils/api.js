/**
 * API Helper for PrimeVector Microservices
 * Configured to work via serve_dashboard.py proxy (/api/{port}/{path}) or direct localhost endpoints
 */

export const MICROSERVICES = [
  {
    id: 'orchestrator',
    name: 'orchestrator',
    port: 8080,
    role: 'Central Pipeline Ingestion & Orchestration',
    tier: 'Tier 3 (Orchestrator)',
    language: 'Python / FastAPI',
    endpoint: '/healthz',
  },
  {
    id: 'risk-fusion-engine',
    name: 'risk-fusion-engine',
    port: 8000,
    role: 'Noisy-OR Evidence Fusion & Bounded Context Multiplier',
    tier: 'Tier 0 (Core)',
    language: 'Python / FastAPI',
    endpoint: '/healthz',
  },
  {
    id: 'feature-extraction-service',
    name: 'feature-extraction-service',
    port: 8001,
    role: 'Log-Mel Spectrogram & Resemblyzer Embedding Extraction',
    tier: 'Tier 0 (Core)',
    language: 'Python / FastAPI',
    endpoint: '/healthz',
  },
  {
    id: 'spoof-detection-service',
    name: 'spoof-detection-service',
    port: 8002,
    role: 'Acoustic AI Synthesis Detection & Accent Routing',
    tier: 'Tier 0 (Core)',
    language: 'Python / FastAPI',
    endpoint: '/healthz',
  },
  {
    id: 'enrollment-service',
    name: 'enrollment-service',
    port: 8003,
    role: 'Voiceprint Registration & Liveness Challenge Audit',
    tier: 'Tier 0 (Core)',
    language: 'Python / FastAPI',
    endpoint: '/healthz',
  },
  {
    id: 'policy-threshold-engine',
    name: 'policy-threshold-engine',
    port: 8004,
    role: 'Tenant Policy Rules & Opt-In Auto-Block Gate',
    tier: 'Tier 1 (Rules)',
    language: 'Python / FastAPI',
    endpoint: '/healthz',
  },
  {
    id: 'alerting-service',
    name: 'alerting-service',
    port: 8005,
    role: 'Idempotent Alert Dispatch & Hashed Audit Logging',
    tier: 'Tier 2 (Events)',
    language: 'Python / FastAPI',
    endpoint: '/healthz',
  },
  {
    id: 'ingestion-gateway',
    name: 'ingestion-gateway',
    port: 50051,
    role: 'gRPC Streaming Ingress, Rate-limiting & Token-bucket',
    tier: 'Ingress (gRPC)',
    language: 'Go 1.22 / gRPC',
    endpoint: '/healthz', // gRPC native probe check
  },
];

/**
 * Fetch service health status
 */
export async function checkServiceHealth(port) {
  const startTime = performance.now();
  try {
    // Try via serve_dashboard proxy path first: /api/{port}/healthz
    const proxyUrl = `/api/${port}/healthz`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2500);

    const response = await fetch(proxyUrl, {
      method: 'GET',
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    const latency = Math.round(performance.now() - startTime);

    if (response.ok) {
      const data = await response.json();
      return {
        status: 'online',
        statusCode: response.status,
        latencyMs: latency,
        data,
      };
    } else {
      return {
        status: 'degraded',
        statusCode: response.status,
        latencyMs: latency,
        data: null,
      };
    }
  } catch (err) {
    const latency = Math.round(performance.now() - startTime);
    return {
      status: 'offline',
      statusCode: 0,
      latencyMs: latency,
      error: err.name === 'AbortError' ? 'Timeout (2.5s)' : 'Connection refused / Offline',
    };
  }
}

/**
 * Execute real pipeline process request through orchestrator
 */
export async function executePipelineProcess(payload) {
  const startTime = performance.now();
  const proxyUrl = `/api/8080/v1/pipeline/process`;
  
  try {
    const response = await fetch(proxyUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    const latencyMs = Math.round(performance.now() - startTime);

    if (!response.ok) {
      const errorText = await response.text();
      return {
        success: false,
        statusCode: response.status,
        latencyMs,
        error: errorText,
      };
    }

    const data = await response.json();
    return {
      success: true,
      statusCode: response.status,
      latencyMs,
      data,
    };
  } catch (err) {
    const latencyMs = Math.round(performance.now() - startTime);
    return {
      success: false,
      statusCode: 0,
      latencyMs,
      error: err.message || 'Network error connecting to orchestrator',
    };
  }
}
