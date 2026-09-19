import React from 'react';

export default function UsageChart({ data = [], maxValue }) {
  if (!data.length) {
    return (
      <div className="h-48 flex items-center justify-center text-xs font-mono text-forest/60">
        No usage data yet
      </div>
    );
  }

  const max = maxValue || Math.max(...data.map(d => d.detections), 1);

  return (
    <div className="space-y-3">
      <div className="h-48 flex items-end gap-[4px] pt-8 pb-3 px-3 bg-sage-1 rounded-xl border border-forest/15 overflow-x-auto">
        {data.map((entry, i) => {
          const heightPct = (entry.detections / max) * 100;
          const realPct = entry.detections > 0 ? (entry.real_count / entry.detections) * 100 : 0;
          const fakePct = entry.detections > 0 ? (entry.fake_count / entry.detections) * 100 : 0;

          return (
            <div
              key={i}
              className="flex-1 min-w-[20px] flex flex-col items-center gap-1.5 h-full justify-end group relative"
            >
              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 hidden group-hover:block z-20 pointer-events-none">
                <div className="bg-forest border border-forest-dark text-white rounded-lg px-3 py-2 text-[10px] font-mono whitespace-nowrap shadow-spade-lg">
                  <div className="font-extrabold text-lemongrass">{entry.detections.toLocaleString()} detections</div>
                  <div className="text-emerald-300">✓ {entry.real_count} real human</div>
                  <div className="text-rose-300">✗ {entry.fake_count} synthetic</div>
                  {entry.uncertain_count > 0 && (
                    <div className="text-amber-300">? {entry.uncertain_count} uncertain</div>
                  )}
                  <div className="text-white/60 pt-1 border-t border-white/10 mt-1">{entry.date}</div>
                </div>
              </div>

              {/* Stacked bar */}
              <div
                className="w-full rounded-t-sm overflow-hidden transition-all group-hover:brightness-110 shadow-sm"
                style={{ height: `${Math.max(4, heightPct)}%` }}
              >
                {/* Fake portion (top) */}
                <div
                  className="w-full bg-rose-600"
                  style={{ height: `${fakePct}%` }}
                />
                {/* Uncertain */}
                <div
                  className="w-full bg-amber-500"
                  style={{ height: `${100 - realPct - fakePct}%` }}
                />
                {/* Real portion (bottom) */}
                <div
                  className="w-full bg-forest"
                  style={{ height: `${realPct}%` }}
                />
              </div>

              {/* Date label */}
              {(i === 0 || i === data.length - 1 || i % Math.ceil(data.length / 7) === 0) && (
                <span className="text-[9px] font-mono text-forest/70 font-bold whitespace-nowrap">
                  {entry.date?.slice(5)}
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-5 text-xs font-mono font-bold text-forest/80 pt-1">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-forest" /> Real Human Speech
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-rose-600" /> Synthetic Deepfake
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-amber-500" /> Uncertain Score
        </span>
      </div>
    </div>
  );
}

