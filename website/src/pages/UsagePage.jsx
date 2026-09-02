import React, { useState } from 'react';
import { BarChart3, AlertTriangle, Calendar, Layers, Clock, ShieldAlert, Info } from 'lucide-react';

export default function UsagePage() {
  const [selectedTenant, setSelectedTenant] = useState('bank-retail-prod');

  // Realistic sample usage data metrics
  const sampleMetrics = {
    total_calls_24h: 142850,
    avg_latency_ms: 41.2,
    p95_latency_ms: 58.4,
    high_risk_flagged: 1240,
    blocked_calls: 312,
    hours: [
      { time: '00:00', calls: 3200, risk: 24 },
      { time: '04:00', calls: 1800, risk: 12 },
      { time: '08:00', calls: 8900, risk: 84 },
      { time: '12:00', calls: 14500, risk: 162 },
      { time: '16:00', calls: 16200, risk: 210 },
      { time: '20:00', calls: 9800, risk: 95 },
    ],
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-obsidian-700">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-forensic-amber" />
            <h1 className="font-serif text-3xl font-bold text-white">API Usage & Tenant Metering</h1>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Call volume, latency distribution, and risk flag breakdown for active API key
          </p>
        </div>

        {/* PROMINENT SAMPLE DATA BADGE (HARD RULE 3 REQUIREMENT) */}
        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-amber-950/80 text-amber-400 border border-amber-500/50 font-mono text-xs shadow-amber-glow animate-pulse">
          <AlertTriangle size={14} />
          <span>SAMPLE DATA / DEMO PREVIEW</span>
        </div>
      </div>

      {/* Honesty Explanatory Banner */}
      <div className="p-4 rounded-xl bg-obsidian-900 border border-amber-500/30 flex items-start gap-3">
        <Info className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 font-sans leading-relaxed">
          <strong>Backend Metering Note:</strong> The backend microservice architecture currently processes streaming calls in memory without writing persistent call metering records to a time-series database. The metrics shown below are <strong>simulated sample analytics</strong> to demonstrate the frontend telemetry dashboard layout.
        </div>
      </div>

      {/* Tenant Selector & Filter */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-lg bg-obsidian-900 border border-obsidian-700 font-mono text-xs">
        <div className="flex items-center gap-3">
          <span className="text-slate-400">Active Tenant ID:</span>
          <select
            value={selectedTenant}
            onChange={(e) => setSelectedTenant(e.target.value)}
            className="px-3 py-1.5 rounded bg-obsidian-850 border border-obsidian-700 text-white font-bold focus:outline-none focus:border-forensic-amber"
          >
            <option value="bank-retail-prod">bank-retail-prod (Primary Wire Transfer API Key)</option>
            <option value="cfo-executive-shield">cfo-executive-shield (VIP Voice Line)</option>
            <option value="callcenter-auth-gateway">callcenter-auth-gateway (Inbound IVR)</option>
          </select>
        </div>

        <span className="text-slate-400">Time Window: Last 24 Hours</span>
      </div>

      {/* Key Metric Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="p-5 rounded-xl bg-obsidian-900 border border-obsidian-700">
          <div className="text-xs font-mono text-slate-400 mb-1">Total Audio Processed (24h)</div>
          <div className="text-2xl font-bold font-serif text-white">{sampleMetrics.total_calls_24h.toLocaleString()}</div>
          <div className="text-[11px] font-mono text-emerald-400 mt-2">↑ 14.2% from previous day</div>
        </div>

        <div className="p-5 rounded-xl bg-obsidian-900 border border-obsidian-700">
          <div className="text-xs font-mono text-slate-400 mb-1">Average P50 Latency</div>
          <div className="text-2xl font-bold font-serif text-forensic-amber">{sampleMetrics.avg_latency_ms} ms</div>
          <div className="text-[11px] font-mono text-slate-400 mt-2">P95: {sampleMetrics.p95_latency_ms} ms</div>
        </div>

        <div className="p-5 rounded-xl bg-obsidian-900 border border-obsidian-700">
          <div className="text-xs font-mono text-slate-400 mb-1">High-Risk Fraud Flagged</div>
          <div className="text-2xl font-bold font-serif text-rose-400">{sampleMetrics.high_risk_flagged.toLocaleString()}</div>
          <div className="text-[11px] font-mono text-rose-400 mt-2">0.87% flag rate</div>
        </div>

        <div className="p-5 rounded-xl bg-obsidian-900 border border-obsidian-700">
          <div className="text-xs font-mono text-slate-400 mb-1">Auto-Blocked Calls</div>
          <div className="text-2xl font-bold font-serif text-purple-400">{sampleMetrics.blocked_calls.toLocaleString()}</div>
          <div className="text-[11px] font-mono text-slate-400 mt-2">Opt-in tenants only</div>
        </div>
      </div>

      {/* Hourly Call Volume Bar Visualizer */}
      <div className="rounded-xl border border-obsidian-700 bg-obsidian-900 p-6 shadow-card-glow space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-serif text-lg font-bold text-white">Hourly Request Volume & Risk Flags</h3>
          <span className="text-xs font-mono text-slate-400">Sample Histogram</span>
        </div>

        <div className="h-48 flex items-end justify-between gap-4 pt-8 pb-2 px-4 bg-obsidian-950 rounded-lg border border-obsidian-800">
          {sampleMetrics.hours.map((h, i) => {
            const barHeightPct = (h.calls / 18000) * 100;
            return (
              <div key={i} className="flex-1 flex flex-col items-center gap-2 h-full justify-end group">
                <div className="text-[10px] font-mono text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity">
                  {h.calls.toLocaleString()}
                </div>
                <div
                  className="w-full max-w-[40px] bg-amber-gradient rounded-t transition-all group-hover:brightness-125"
                  style={{ height: `${barHeightPct}%` }}
                ></div>
                <span className="text-[10px] font-mono text-slate-400">{h.time}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
