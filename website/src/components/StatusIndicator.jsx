import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Clock, Server } from 'lucide-react';

export default function StatusIndicator({ service, health, onRefresh }) {
  const isOnline = health?.status === 'online';
  const isDegraded = health?.status === 'degraded';
  const isUnobservable = health?.status === 'unobservable';

  let statusBadge = (
    <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-emerald-100 text-emerald-900 border border-emerald-300 shadow-sm">
      <CheckCircle2 size={13} /> ONLINE (200 OK)
    </span>
  );

  if (isUnobservable) {
    statusBadge = (
      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-slate-100 text-slate-800 border border-slate-300 shadow-sm">
        <AlertTriangle size={13} /> gRPC HEALTH UNAVAILABLE
      </span>
    );
  } else if (isDegraded) {
    statusBadge = (
      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300 shadow-sm">
        <AlertTriangle size={13} /> DEGRADED ({health.statusCode})
      </span>
    );
  } else if (!isOnline) {
    statusBadge = (
      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-rose-100 text-rose-900 border border-rose-300 shadow-sm">
        <XCircle size={13} /> OFFLINE
      </span>
    );
  }

  return (
    <div className="rounded-xl border border-forest/15 bg-sage-1 p-5 spade-cut-sm shadow-spade hover:border-forest/30 transition-all">
      <div className="flex items-start justify-between mb-3 gap-2">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-forest text-lemongrass flex items-center justify-center font-bold shadow-sm shrink-0">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-display text-sm font-bold text-forest">
              {service.name}
            </h4>
            <span className="text-[11px] font-mono font-semibold text-forest/70">
              {service.location === 'colab' ? 'Google Colab via ngrok' : 'Local PC'} • Port :{service.port}
            </span>
          </div>
        </div>
        {statusBadge}
      </div>

      <p className="text-xs text-forest/80 leading-relaxed mb-4 min-h-[36px] font-normal">
        {service.desc}
      </p>

      <div className="pt-3 border-t border-forest/10 flex items-center justify-between text-xs font-mono text-forest/70 font-semibold">
        <span className="px-2 py-0.5 rounded bg-white border border-forest/15 text-[10px] text-forest font-bold">
          {service.location === 'colab' ? 'COLAB / NGROK' : 'LOCAL'}
        </span>
        <div className="flex items-center gap-1">
          <Clock size={12} className="text-forest/60" />
          <span>{typeof health?.latencyMs === 'number' ? `${health.latencyMs} ms` : 'not measured'}</span>
        </div>
      </div>
    </div>
  );
}

