import React, { useState } from 'react';
import { FileCode, Terminal, Copy, Check, Lock, Sparkles, Server } from 'lucide-react';
import CodeBlock from '../components/CodeBlock';

export default function ApiDocsPage() {
  const [activeSdkTab, setActiveSdkTab] = useState('python');
  const [copiedEndpoint, setCopiedEndpoint] = useState(null);

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedEndpoint(id);
    setTimeout(() => setCopiedEndpoint(null), 2000);
  };

  const pythonSdk = `import requests
import base64

API_KEY = "pv_live_your_org_key_here"
BASE_URL = "https://api.primevector.dev"

# Read audio file and encode as base64
with open("incoming_call.wav", "rb") as f:
    audio_b64 = base64.b64encode(f.read()).decode()

# Perform real-time voice verification
response = requests.post(
    f"{BASE_URL}/v1/detect",
    headers={
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
    },
    json={
        "audio_pcm_base64": audio_b64,
        "sample_rate": 16000,
    },
)

result = response.json()
print(f"Verdict:    {result['verdict']}")       # "real" or "fake"
print(f"Score:      {result['spoof_score']}")    # 0.0 (real) → 1.0 (fake)
print(f"Confidence: {result['confidence']}")  # Confidence metric
print(f"Latency:    {result['latency_ms']}ms")   # Sub-50ms inference`;

  const nodeSdk = `const fs = require('fs');

const API_KEY = 'pv_live_your_org_key_here';
const BASE_URL = 'https://api.primevector.dev';

// Read audio file
const audioBuffer = fs.readFileSync('incoming_call.wav');
const audioBase64 = audioBuffer.toString('base64');

// Perform real-time voice verification
const response = await fetch(\`\${BASE_URL}/v1/detect\`, {
  method: 'POST',
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    audio_pcm_base64: audioBase64,
    sample_rate: 16000,
  }),
});

const result = await response.json();
console.log(\`Verdict: \${result.verdict}\`);       // "real" or "fake"
console.log(\`Score:   \${result.spoof_score}\`);    // 0.0 → 1.0
console.log(\`Latency: \${result.latency_ms}ms\`);`;

  const endpoints = [
    {
      method: 'POST',
      path: '/v1/detect',
      title: 'Detect Deepfake Audio',
      desc: 'Analyze a single audio sample for AI voice synthesis & cloning. Returns real vs. fake verdict and raw confidence score.',
      auth: true,
      tier: 'Free / Pro / Enterprise',
      request: `{
  "audio_pcm_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
  "sample_rate": 16000,
  "session_id": "call-tenant-9941"
}`,
      response: `{
  "session_id": "call-tenant-9941",
  "verdict": "real",
  "spoof_score": 0.0421,
  "confidence": 0.9579,
  "raw_logit": -2.8512,
  "threshold": 0.5,
  "latency_ms": 38.4,
  "model_version": "Dhwani-v2.0",
  "model_architecture": "DhwaniV2-ResNetSE-BiGRU-Attention",
  "timestamp": "2026-09-18T16:00:00.000Z"
}`,
    },
    {
      method: 'POST',
      path: '/v1/detect/batch',
      title: 'Batch Audio Analysis',
      desc: 'Submit up to 10 audio items concurrently for batch processing.',
      auth: true,
      tier: 'Pro+',
      request: `{
  "items": [
    { "audio_pcm_base64": "<b64-1>", "sample_rate": 16000 },
    { "audio_pcm_base64": "<b64-2>", "sample_rate": 16000 }
  ]
}`,
      response: `{
  "results": [ ... ],
  "total_latency_ms": 114.2
}`,
    },
    {
      method: 'GET',
      path: '/v1/usage',
      title: 'Organization API Usage & Quota',
      desc: 'Retrieve current API key usage, daily request counts, and remaining quota.',
      auth: true,
      tier: 'All Tiers',
      response: `{
  "api_key_id": "pv_live_0012",
  "tier": "pro",
  "detections_today": 1840,
  "detections_this_month": 34200,
  "daily_limit": 100000,
  "remaining_today": 98160,
  "avg_latency_ms": 36.4,
  "verdicts": { "real": 1620, "fake": 220, "uncertain": 0 }
}`,
    },
    {
      method: 'GET',
      path: '/v1/health',
      title: 'Gateway & Model Health Check',
      desc: 'Public health status endpoint for Dhwani 2 model availability.',
      auth: false,
      tier: 'Public',
      response: `{
  "status": "ok",
  "model_loaded": true,
  "model_version": "Dhwani-v2.0",
  "model_architecture": "DhwaniV2-ResNetSE-BiGRU-Attention",
  "uptime_seconds": 86400.0
}`,
    },
  ];

  return (
    <div className="min-h-screen bg-white text-forest selection:bg-lemongrass py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        
        {/* Header */}
        <div className="space-y-2 pb-6 border-b border-forest/10">
          <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-forest/70">
            <Terminal size={14} className="text-forest" />
            <span>Developer Reference</span>
          </div>
          <h1 className="font-display text-4xl font-extrabold text-forest tracking-tight">
            REST API & SDK Documentation
          </h1>
          <p className="text-sm text-forest/70">
            Complete endpoint reference for the PrimeVector voice authenticity and deepfake detection gateway.
          </p>
        </div>

        {/* Authentication Card */}
        <section className="bg-sage-1 border border-forest/10 rounded-2xl p-8 spade-cut-md space-y-4">
          <div className="flex items-center gap-2 text-forest font-display text-xl font-bold">
            <Lock size={20} />
            <h2>API Key Authentication</h2>
          </div>
          <p className="text-sm text-forest/80 leading-relaxed">
            All API calls (except <code className="bg-white border border-forest/15 px-1.5 py-0.5 rounded font-mono text-xs text-forest">/v1/health</code>) require an API key passed in the <code className="bg-white border border-forest/15 px-1.5 py-0.5 rounded font-mono text-xs font-bold text-forest">X-API-Key</code> request header.
          </p>
          <CodeBlock
            code={`curl -H "X-API-Key: pv_live_your_key_here" https://api.primevector.dev/v1/usage`}
            language="bash"
            title="cURL Authentication Header Example"
          />
        </section>

        {/* SDK Tabs */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-2xl font-bold text-forest">Quickstart Code Snippets</h2>
            <div className="flex items-center gap-2 bg-sage-1 p-1 rounded-lg border border-forest/10 font-mono text-xs">
              <button
                onClick={() => setActiveSdkTab('python')}
                className={`px-4 py-2 rounded-md font-bold transition-all cursor-pointer ${
                  activeSdkTab === 'python' ? 'bg-forest text-lemongrass shadow-sm' : 'text-forest/70 hover:text-forest'
                }`}
              >
                Python SDK
              </button>
              <button
                onClick={() => setActiveSdkTab('node')}
                className={`px-4 py-2 rounded-md font-bold transition-all cursor-pointer ${
                  activeSdkTab === 'node' ? 'bg-forest text-lemongrass shadow-sm' : 'text-forest/70 hover:text-forest'
                }`}
              >
                Node.js SDK
              </button>
            </div>
          </div>

          <CodeBlock
            code={activeSdkTab === 'python' ? pythonSdk : nodeSdk}
            language={activeSdkTab === 'python' ? 'python' : 'javascript'}
            title={activeSdkTab === 'python' ? 'Python — Detect Deepfake' : 'Node.js — Detect Deepfake'}
          />
        </section>

        {/* Endpoints List */}
        <section className="space-y-6">
          <h2 className="font-display text-2xl font-bold text-forest">API Endpoints Reference</h2>

          {endpoints.map((ep, i) => (
            <div key={i} className="bg-white border border-forest/10 rounded-2xl p-6 sm:p-8 space-y-4 shadow-spade spade-cut-md">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-forest/10">
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 rounded text-xs font-mono font-extrabold ${
                    ep.method === 'POST' ? 'bg-forest text-lemongrass' : 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                  }`}>
                    {ep.method}
                  </span>
                  <code className="font-mono text-base font-bold text-forest">{ep.path}</code>
                  <button
                    onClick={() => copyToClipboard(ep.path, i)}
                    className="text-forest/40 hover:text-forest transition-colors cursor-pointer"
                  >
                    {copiedEndpoint === i ? <Check size={16} className="text-emerald-600" /> : <Copy size={16} />}
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono font-semibold px-2.5 py-1 rounded bg-sage-1 text-forest border border-forest/10">
                    {ep.tier}
                  </span>
                </div>
              </div>

              <p className="text-sm text-forest/80 font-normal">{ep.desc}</p>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-2">
                {ep.request && (
                  <div>
                    <h4 className="font-mono text-xs font-bold text-forest uppercase tracking-wider mb-2">Request Body</h4>
                    <CodeBlock code={ep.request} language="json" title="Request Payload" />
                  </div>
                )}
                <div>
                  <h4 className="font-mono text-xs font-bold text-forest uppercase tracking-wider mb-2">Response Output</h4>
                  <CodeBlock code={ep.response} language="json" title="Response Payload" />
                </div>
              </div>
            </div>
          ))}
        </section>

      </div>
    </div>
  );
}
