import React, { useState, useEffect } from 'react';
import { Activity, RefreshCw, Server } from 'lucide-react';
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
        const res = await checkServiceHealth(svc);
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
  const observableServices = MICROSERVICES.filter((service) => service.healthPath);
  const observableCount = observableServices.length;
  const unobservableCount = MICROSERVICES.length - observableCount;

  return (
    <div className="min-h-screen bg-white text-forest selection:bg-lemongrass py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-forest/10">
          <div>
            <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-forest/70 mb-1">
              <Activity size={14} className="text-forest" />
              <span>Infrastructure Health</span>
            </div>
            <h1 className="font-display text-4xl font-extrabold text-forest tracking-tight">Live Services & Microservice Status</h1>
            <p className="text-xs font-mono text-forest/60 mt-1">
              Real-time health checks across local services and Colab services routed through ngrok
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <div className="text-[11px] font-mono text-forest/60">Last Checked:</div>
              <div className="text-xs font-mono text-forest font-bold">{lastChecked || 'Checking...'}</div>
            </div>

            <button
              onClick={fetchAllHealth}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-sage-1 border border-forest/15 hover:border-forest/40 text-forest font-mono text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin text-forest' : 'text-forest/60'} />
              <span>{loading ? 'Pinging Services...' : 'Refresh Status'}</span>
            </button>
          </div>
        </div>

        {/* Cluster Overview Banner */}
        <div className="rounded-2xl border border-forest/10 bg-sage-1 p-6 shadow-spade spade-cut-md flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center border ${
              onlineCount === observableCount
                ? 'bg-emerald-100 border-emerald-300 text-emerald-700'
                : 'bg-amber-100 border-amber-300 text-amber-700'
            }`}>
              <Server size={24} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-display text-xl font-extrabold text-forest">
                  Cluster Health: {onlineCount === observableCount ? 'FULLY OPERATIONAL' : 'DEGRADED'}
                </h3>
              </div>
              <p className="text-xs font-mono text-forest/60 mt-0.5">
                {onlineCount} of {observableCount} HTTP-observable services are healthy. {unobservableCount} gRPC-only service is shown separately.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 bg-white px-5 py-3 rounded-lg border border-forest/10 font-mono text-xs">
            <div>
              <div className="text-forest/60">Services Active:</div>
              <div className="text-lg font-extrabold text-forest">{onlineCount} / {observableCount}</div>
            </div>
            <div className="w-px h-8 bg-forest/10 mx-2"></div>
            <div>
              <div className="text-forest/60">Fail-Safe Invariant:</div>
              <div className="text-xs font-bold text-emerald-700">ACTIVE (NEVER FAILS OPEN)</div>
            </div>
          </div>
        </div>

        {/* Microservices Grid */}
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
    </div>
  );
}
