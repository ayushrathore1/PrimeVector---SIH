import React, { useState, useEffect } from 'react';
import { BarChart3, Key, Clock, ShieldCheck, ShieldAlert, Trash2, Plus, Copy, Check, HelpCircle, Activity } from 'lucide-react';
import UsageChart from '../components/UsageChart';
import { getUsage, getUsageHistory, getRecentDetections } from '../utils/api';

const DEMO_API_KEY = 'pv_live_demo_000000000000000000000000';

const DEMO_USAGE = {
  api_key_id: 'key-demo-001',
  tier: 'pro',
  detections_today: 1840,
  detections_this_month: 34200,
  daily_limit: 100000,
  monthly_limit: 1000000,
  remaining_today: 98160,
  avg_latency_ms: 36.4,
  verdicts: { real: 1620, fake: 220, uncertain: 0 },
};

const DEMO_HISTORY = Array.from({ length: 14 }, (_, i) => {
  const d = new Date();
  d.setDate(d.getDate() - (13 - i));
  const total = Math.floor(Math.random() * 120) + 40;
  const fake = Math.floor(total * (0.15 + Math.random() * 0.2));
  const uncertain = 0;
  return {
    date: d.toISOString().split('T')[0],
    detections: total,
    real_count: total - fake - uncertain,
    fake_count: fake,
    uncertain_count: uncertain,
    avg_latency_ms: 32 + Math.random() * 14,
  };
});

const DEMO_DETECTIONS = Array.from({ length: 10 }, (_, i) => ({
  session_id: `pv-live-${(1000 + i).toString(36)}`,
  timestamp: new Date(Date.now() - i * 180000).toISOString(),
  verdict: ['real', 'fake', 'real', 'real', 'real', 'fake', 'real', 'real', 'real', 'fake'][i],
  spoof_score: [0.04, 0.94, 0.08, 0.02, 0.06, 0.89, 0.03, 0.07, 0.05, 0.91][i],
  confidence: [0.96, 0.88, 0.92, 0.98, 0.94, 0.78, 0.97, 0.93, 0.95, 0.82][i],
  latency_ms: [36, 41, 34, 38, 32, 45, 35, 37, 33, 40][i],
}));

export default function UsagePage() {
  const [apiKey, setApiKey] = useState(DEMO_API_KEY);
  const [usage, setUsage] = useState(DEMO_USAGE);
  const [history, setHistory] = useState(DEMO_HISTORY);
  const [detections, setDetections] = useState(DEMO_DETECTIONS);
  const [isLive, setIsLive] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadData();
  }, [apiKey]);

  const loadData = async () => {
    const [usageRes, histRes, detRes] = await Promise.all([
      getUsage(apiKey),
      getUsageHistory(apiKey),
      getRecentDetections(apiKey, 20),
    ]);

    if (usageRes.success) { setUsage(usageRes.data); setIsLive(true); }
    else { setUsage(DEMO_USAGE); setIsLive(false); }

    if (histRes.success) setHistory(histRes.data.entries || []);
    else setHistory(DEMO_HISTORY);

    if (detRes.success) setDetections(detRes.data.detections || []);
    else setDetections(DEMO_DETECTIONS);
  };

  const usedPct = usage.daily_limit > 0 ? Math.round((usage.detections_today / usage.daily_limit) * 100) : 0;

  const copyKey = () => {
    navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-white text-forest selection:bg-lemongrass py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-forest/10">
          <div>
            <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-forest/70 mb-1">
              <BarChart3 size={14} className="text-forest" />
              <span>Real-Time Analytics</span>
            </div>
            <h1 className="font-display text-4xl font-extrabold text-forest tracking-tight">
              Usage & Metering Dashboard
            </h1>
          </div>

          {!isLive && (
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-lemongrass/30 border border-forest/20 text-forest font-mono text-xs font-semibold">
              <HelpCircle size={14} />
              <span>DEMO MODE ACTIVE — Live API endpoints responsive</span>
            </div>
          )}
        </div>

        {/* API Key Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-4 rounded-xl bg-sage-1 border border-forest/10 spade-cut-sm">
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <Key size={16} className="text-forest shrink-0" />
            <span className="text-xs font-mono font-bold text-forest whitespace-nowrap">API Key:</span>
            <input
              type="text"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="pv_live_your_key_here"
              className="w-full sm:w-80 bg-white border border-forest/15 px-3 py-1.5 rounded text-xs font-mono text-forest outline-none focus:border-forest"
            />
            <button onClick={copyKey} className="text-forest/60 hover:text-forest transition-colors cursor-pointer">
              {copied ? <Check size={16} className="text-emerald-600" /> : <Copy size={16} />}
            </button>
          </div>
          <span className="text-[11px] font-mono font-extrabold px-3 py-1 rounded bg-forest text-lemongrass uppercase">
            TIER: {usage.tier}
          </span>
        </div>

        {/* Stat Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-sage-1 border border-forest/10 rounded-2xl p-6 spade-cut-sm space-y-2">
            <div className="text-xs font-mono font-bold text-forest/60 uppercase tracking-wider">Today's Detections</div>
            <div className="text-3xl font-extrabold font-display text-forest">
              {usage.detections_today.toLocaleString()}
            </div>
            <div className="w-full bg-forest/10 rounded-full h-2 overflow-hidden mt-3">
              <div className="bg-forest h-full rounded-full" style={{ width: `${Math.min(100, usedPct)}%` }} />
            </div>
            <div className="text-[11px] font-mono text-forest/70 pt-1">
              {usage.remaining_today.toLocaleString()} remaining ({usedPct}% used)
            </div>
          </div>

          <div className="bg-sage-1 border border-forest/10 rounded-2xl p-6 spade-cut-sm space-y-2">
            <div className="text-xs font-mono font-bold text-forest/60 uppercase tracking-wider">Monthly Volume</div>
            <div className="text-3xl font-extrabold font-display text-forest">
              {usage.detections_this_month.toLocaleString()}
            </div>
            <div className="text-[11px] font-mono text-forest/70 pt-3">
              Monthly Limit: {usage.monthly_limit.toLocaleString()}
            </div>
          </div>

          <div className="bg-sage-1 border border-forest/10 rounded-2xl p-6 spade-cut-sm space-y-2">
            <div className="text-xs font-mono font-bold text-forest/60 uppercase tracking-wider">P99 Inference Latency</div>
            <div className="text-3xl font-extrabold font-display text-emerald-700">
              {usage.avg_latency_ms} ms
            </div>
            <div className="text-[11px] font-mono text-emerald-800 font-semibold pt-3 flex items-center gap-1">
              <Clock size={12} /> Model SLA Target: &lt;50ms
            </div>
          </div>

          <div className="bg-sage-1 border border-forest/10 rounded-2xl p-6 spade-cut-sm space-y-2">
            <div className="text-xs font-mono font-bold text-forest/60 uppercase tracking-wider">Verdict Breakdown</div>
            <div className="flex items-center gap-4 pt-2">
              <div className="flex items-center gap-1.5 font-mono text-sm">
                <ShieldCheck size={16} className="text-emerald-700" />
                <span className="font-extrabold text-forest">{usage.verdicts?.real || 0}</span>
                <span className="text-xs text-forest/60">Real</span>
              </div>
              <div className="flex items-center gap-1.5 font-mono text-sm">
                <ShieldAlert size={16} className="text-rose-700" />
                <span className="font-extrabold text-forest">{usage.verdicts?.fake || 0}</span>
                <span className="text-xs text-forest/60">Fake</span>
              </div>
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="bg-white border border-forest/10 rounded-2xl p-6 sm:p-8 space-y-4 shadow-spade spade-cut-md">
          <h3 className="font-display text-xl font-bold text-forest">Detection Stream Throughput (14 Days)</h3>
          <UsageChart data={history} />
        </div>

        {/* Recent Detections Log Table */}
        <div className="bg-white border border-forest/10 rounded-2xl overflow-hidden shadow-spade spade-cut-md">
          <div className="px-6 py-4 bg-sage-1 border-b border-forest/10 flex items-center justify-between">
            <span className="font-mono text-xs font-bold text-forest uppercase tracking-wider">
              Recent Detection Logs ({detections.length})
            </span>
            <span className="text-xs font-mono text-forest/60">Dhwani 2 Engine</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-sage-2 text-forest border-b border-forest/10 font-bold">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Session ID</th>
                  <th className="py-3 px-4">Verdict</th>
                  <th className="py-3 px-4">Spoof Score</th>
                  <th className="py-3 px-4">Confidence</th>
                  <th className="py-3 px-4">Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-forest/5 text-forest/80">
                {detections.map((det, i) => (
                  <tr key={i} className="hover:bg-sage-1/50 transition-colors">
                    <td className="py-3 px-4 text-forest/60 whitespace-nowrap">
                      {new Date(det.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-4 text-forest font-bold whitespace-nowrap">{det.session_id}</td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                        det.verdict === 'real'
                          ? 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                          : det.verdict === 'fake'
                          ? 'bg-rose-100 text-rose-900 border border-rose-300'
                          : 'bg-amber-100 text-amber-900 border border-amber-300'
                      }`}>
                        {det.verdict}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-bold">{det.spoof_score.toFixed(4)}</td>
                    <td className="py-3 px-4">{(det.confidence * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4 text-emerald-700 font-bold">{det.latency_ms} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
