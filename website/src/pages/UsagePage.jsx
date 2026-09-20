import React, { useState, useEffect, useCallback } from 'react';
import { BarChart3, Key, Clock, ShieldCheck, ShieldAlert, Copy, Check, HelpCircle, Activity, RefreshCw } from 'lucide-react';
import UsageChart from '../components/UsageChart';
import ApiKeyManager from '../components/ApiKeyManager';
import { getUsage, getUsageHistory, getRecentDetections } from '../utils/api';

const DEFAULT_DEMO_KEY = 'pv_live_demo_000000000000000000000000';

const EMPTY_USAGE = {
  api_key_id: '',
  tier: 'free',
  detections_today: 0,
  detections_this_month: 0,
  daily_limit: 0,
  monthly_limit: 0,
  remaining_today: 0,
  avg_latency_ms: 0,
  verdicts: { real: 0, fake: 0, uncertain: 0 },
};

export default function UsagePage() {
  const [apiKey, setApiKey] = useState(DEFAULT_DEMO_KEY);
  const [usage, setUsage] = useState(EMPTY_USAGE);
  const [history, setHistory] = useState([]);
  const [detections, setDetections] = useState([]);
  const [isLive, setIsLive] = useState(false);
  const [copied, setCopied] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadData = useCallback(async () => {
    if (!apiKey) return;
    setRefreshing(true);
    const [usageRes, histRes, detRes] = await Promise.all([
      getUsage(apiKey),
      getUsageHistory(apiKey),
      getRecentDetections(apiKey, 30),
    ]);

    if (usageRes.success && usageRes.data) {
      setUsage(usageRes.data);
      setIsLive(true);
    } else {
      setUsage(EMPTY_USAGE);
      setIsLive(false);
    }

    if (histRes.success && histRes.data?.entries) {
      setHistory(histRes.data.entries);
    } else {
      setHistory([]);
    }

    if (detRes.success && detRes.data?.detections) {
      setDetections(detRes.data.detections);
    } else {
      setDetections([]);
    }

    setLastRefreshed(new Date().toLocaleTimeString());
    setRefreshing(false);
  }, [apiKey]);

  useEffect(() => {
    loadData();
    if (!autoRefresh) return;
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData, autoRefresh]);

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
              <span>Real-Time Analytics & Provisioning</span>
            </div>
            <h1 className="font-display text-4xl font-extrabold text-forest tracking-tight">
              Usage & Metering Dashboard
            </h1>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {isLive ? (
              <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-100 border border-emerald-300 text-emerald-900 font-mono text-xs font-semibold">
                <Activity size={14} className="animate-pulse text-emerald-600" />
                <span>LIVE — Gateway Connected</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-amber-100 border border-amber-300 text-amber-900 font-mono text-xs font-semibold">
                <HelpCircle size={14} />
                <span>OFFLINE — Gateway Unreachable</span>
              </div>
            )}

            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3 py-1.5 rounded-lg border font-mono text-xs font-bold transition-all cursor-pointer ${
                autoRefresh
                  ? 'bg-forest text-lemongrass border-forest'
                  : 'bg-sage-1 text-forest border-forest/20 hover:border-forest/40'
              }`}
            >
              {autoRefresh ? '⚡ Live 5s Sync ON' : 'Pause Live Sync'}
            </button>

            <button
              onClick={loadData}
              disabled={refreshing}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-sage-1 border border-forest/15 hover:border-forest/40 text-forest font-mono text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
              <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
            </button>

            {lastRefreshed && (
              <span className="text-[11px] font-mono text-forest/60 hidden sm:block">
                Updated: {lastRefreshed}
              </span>
            )}
          </div>
        </div>

        {/* API Key Input & Active Status Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-4 rounded-xl bg-sage-1 border border-forest/10 spade-cut-sm">
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <Key size={16} className="text-forest shrink-0" />
            <span className="text-xs font-mono font-bold text-forest whitespace-nowrap">Active API Key:</span>
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

        {/* API Key Generator & Manager Component */}
        <ApiKeyManager
          activeApiKey={apiKey}
          onSelectKey={(newKey) => setApiKey(newKey)}
        />

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

        {/* Real-Time Chart */}
        <div className="bg-white border border-forest/10 rounded-2xl p-6 sm:p-8 space-y-4 shadow-spade spade-cut-md">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-xl font-bold text-forest">Detection Stream Throughput (14 Days)</h3>
            <span className="text-xs font-mono text-forest/60">Dynamic Aggregates</span>
          </div>
          {history.length > 0 ? (
            <UsageChart data={history} />
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <BarChart3 size={40} className="text-forest/20 mb-3" />
              <p className="text-sm font-semibold text-forest/50">No usage history recorded</p>
              <p className="text-xs text-forest/40 mt-1">Detection data will populate in real-time as API calls execute</p>
            </div>
          )}
        </div>

        {/* Recent Detections Log Table */}
        <div className="bg-white border border-forest/10 rounded-2xl overflow-hidden shadow-spade spade-cut-md">
          <div className="px-6 py-4 bg-sage-1 border-b border-forest/10 flex items-center justify-between">
            <span className="font-mono text-xs font-bold text-forest uppercase tracking-wider">
              Recent Detection Logs ({detections.length})
            </span>
            <span className="text-xs font-mono text-forest/60">DhVani 2 Real-Time Engine</span>
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
                {detections.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center">
                      <div className="flex flex-col items-center">
                        <Activity size={32} className="text-forest/20 mb-2" />
                        <p className="text-sm font-semibold text-forest/50">No recent detection logs recorded</p>
                        <p className="text-xs text-forest/40 mt-1">Run voice detection requests via API or Live Detector to stream logs here</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  detections.map((det, i) => (
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
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
