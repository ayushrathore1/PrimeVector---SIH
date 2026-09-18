import React from 'react';

export default function UsageChart({ data = [], maxValue }) {
  if (!data.length) {
    return (
      <div className="h-48 flex items-center justify-center text-sm font-mono text-slate-500">
        No usage data yet
      </div>
    );
  }

  const max = maxValue || Math.max(...data.map(d => d.detections), 1);

  return (
    <div className="space-y-2">
      <div className="h-48 flex items-end gap-[3px] pt-8 pb-2 px-2 bg-obsidian-950 rounded-lg border border-obsidian-800 overflow-x-auto">
        {data.map((entry, i) => {
          const heightPct = (entry.detections / max) * 100;
          const realPct = entry.detections > 0 ? (entry.real_count / entry.detections) * 100 : 0;
          const fakePct = entry.detections > 0 ? (entry.fake_count / entry.detections) * 100 : 0;

          return (
            <div
              key={i}
              className="flex-1 min-w-[18px] flex flex-col items-center gap-1 h-full justify-end group relative"
            >
              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 hidden group-hover:block z-10">
                <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg px-3 py-2 text-[10px] font-mono text-slate-200 whitespace-nowrap shadow-lg">
                  <div className="text-white font-bold">{entry.detections.toLocaleString()} detections</div>
                  <div className="text-emerald-400">✓ {entry.real_count} real</div>
                  <div className="text-rose-400">✗ {entry.fake_count} fake</div>
                  {entry.uncertain_count > 0 && (
                    <div className="text-amber-400">? {entry.uncertain_count} uncertain</div>
                  )}
                  <div className="text-slate-400 mt-1">{entry.date}</div>
                </div>
              </div>

              {/* Stacked bar */}
              <div
                className="w-full rounded-t overflow-hidden transition-all group-hover:brightness-125"
                style={{ height: `${Math.max(2, heightPct)}%` }}
              >
                {/* Fake portion (top) */}
                <div
                  className="w-full bg-rose-500/80"
                  style={{ height: `${fakePct}%` }}
                />
                {/* Uncertain */}
                <div
                  className="w-full bg-amber-500/60"
                  style={{ height: `${100 - realPct - fakePct}%` }}
                />
                {/* Real portion (bottom) */}
                <div
                  className="w-full bg-emerald-500/70"
                  style={{ height: `${realPct}%` }}
                />
              </div>

              {/* Date label — show every few */}
              {(i === 0 || i === data.length - 1 || i % Math.ceil(data.length / 7) === 0) && (
                <span className="text-[9px] font-mono text-slate-500 whitespace-nowrap">
                  {entry.date?.slice(5)}
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 text-[10px] font-mono text-slate-400">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-sm bg-emerald-500/70" /> Real
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-sm bg-rose-500/80" /> Fake
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-sm bg-amber-500/60" /> Uncertain
        </span>
      </div>
    </div>
  );
}
