import React from 'react';
import { Activity, CheckCircle2, AlertTriangle, XCircle, Clock, Server } from 'lucide-react';

export default function StatusIndicator({ service, health, onRefresh }) {
  const isOnline = health?.status === 'online';
  const isDegraded = health?.status === 'degraded';

  let statusBadge = (
    <span className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono bg-emerald-950/60 text-emerald-400 border border-emerald-500/40">
      <CheckCircle2 size={13} /> ONLINE (200 OK)
    </span>
  );

  if (isDegraded) {
    statusBadge = (
      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono bg-amber-950/60 text-amber-400 border border-amber-500/40">
        <AlertTriangle size={13} /> DEGRADED ({health.statusCode})
      </span>
    );
  } else if (!isOnline) {
    statusBadge = (
      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono bg-rose-950/60 text-rose-400 border border-rose-500/40">
        <XCircle size={13} /> OFFLINE / UNREACHABLE
      </span>
    );
  }

  return (
    <div className="rounded-xl border border-obsidian-700 bg-obsidian-900 p-5 shadow-card-glow hover:border-obsidian-600 transition-all">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-obsidian-850 border border-obsidian-700 flex items-center justify-center">
            <Server className="w-5 h-5 text-forensic-amber" />
          </div>
          <div>
            <h4 className="font-mono text-sm font-bold text-white flex items-center gap-2">
              {service.name}
            </h4>
            <span className="text-[11px] font-mono text-slate-400">
              Port :{service.port} • {service.language}
            </span>
          </div>
        </div>
        {statusBadge}
      </div>

      <p className="text-xs text-slate-300 leading-relaxed mb-4 min-h-[36px]">
        {service.role}
      </p>

      <div className="pt-3 border-t border-obsidian-800 flex items-center justify-between text-xs font-mono text-slate-400">
        <span className="px-2 py-0.5 rounded bg-obsidian-850 border border-obsidian-800 text-[10px] text-slate-300">
          {service.tier}
        </span>
        <div className="flex items-center gap-1">
          <Clock size={12} className="text-slate-400" />
          <span>{health?.latencyMs !== undefined ? `${health.latencyMs} ms` : '—'}</span>
        </div>
      </div>
    </div>
  );
}
