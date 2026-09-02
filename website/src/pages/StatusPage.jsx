import React, { useState, useEffect } from 'react';
import { Activity, RefreshCw, CheckCircle2, AlertTriangle, ShieldCheck, Server } from 'lucide-react';
import StatusIndicator from '../components/StatusIndicator';
import { MICROSERVICES, checkServiceHealth } from '../utils/api';

export default function StatusPage() {
  const [healthMap, setHealthMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState(null);

  const fetchAllHealth = async () => {
    setLoading(true);
    const newHealthMap = {};
    
    // Ping all services in parallel
    await Promise.all(
      MICROSERVICES.map(async (svc) => {
        const res = await checkServiceHealth(svc.port);
        newHealthMap[svc.id] = res;
      })
    );

    setHealthMap(newHealthMap);
    setLastChecked(new Date().toLocaleTimeString());
    setLoading(false);
  };

  useEffect(() => {
    fetchAllHealth();
    const interval = setInterval(fetchAllHealth, 15000); // refresh every 15s
    return () => clearInterval(interval);
  }, []);

  const onlineCount = Object.values(healthMap).filter((h) => h?.status === 'online').length;
  const totalCount = MICROSERVICES.length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-obsidian-700">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-6 h-6 text-forensic-amber" />
            <h1 className="font-serif text-3xl font-bold text-white">Live Services & Microservice Status</h1>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Real-time health check pings across the 8 containerized platform microservices
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right hidden sm:block">
            <div className="text-xs font-mono text-slate-400">Last Checked:</div>
            <div className="text-xs font-mono text-slate-200 font-bold">{lastChecked || 'Checking...'}</div>
          </div>

          <button
            onClick={fetchAllHealth}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-obsidian-850 border border-obsidian-700 hover:border-forensic-amber text-slate-200 font-mono text-xs transition-colors disabled:opacity-50"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin text-forensic-amber' : 'text-slate-400'} />
            <span>{loading ? 'Pinging Services...' : 'Refresh Status'}</span>
          </button>
        </div>
      </div>

      {/* Cluster Overview Banner */}
      <div className="rounded-xl border border-obsidian-700 bg-obsidian-900 p-6 shadow-card-glow flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center border ${
            onlineCount === totalCount
              ? 'bg-emerald-950/50 border-emerald-500/40 text-emerald-400 shadow-emerald-glow'
              : 'bg-amber-950/50 border-amber-500/40 text-amber-400 shadow-amber-glow'
          }`}>
            <Server size={24} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-serif text-xl font-bold text-white">
                Cluster Health Status: {onlineCount === totalCount ? 'FULLY OPERATIONAL' : 'DEGRADED'}
              </h3>
            </div>
            <p className="text-xs font-mono text-slate-400 mt-0.5">
              {onlineCount} of {totalCount} platform microservices responding with healthy HTTP status on local gateway.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 bg-obsidian-850 px-5 py-3 rounded-lg border border-obsidian-700 font-mono text-xs">
          <div>
            <div className="text-slate-400">Services Active:</div>
            <div className="text-lg font-bold text-white">{onlineCount} / {totalCount}</div>
          </div>
          <div className="w-px h-8 bg-obsidian-700 mx-2"></div>
          <div>
            <div className="text-slate-400">Fail-Safe Invariant:</div>
            <div className="text-xs font-bold text-emerald-400">ACTIVE (NEVER FAILS OPEN)</div>
          </div>
        </div>
      </div>

      {/* 8 Microservices Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {MICROSERVICES.map((svc) => (
          <StatusIndicator
            key={svc.id}
            service={svc}
            health={healthMap[svc.id]}
            onRefresh={fetchAllHealth}
          />
        ))}
      </div>
    </div>
  );
}
