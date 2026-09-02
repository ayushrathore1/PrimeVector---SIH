import React from 'react';

export default function RiskBadge({ score, label, className = '' }) {
  let colorStyle = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 glow-emerald-sm';
  let badgeLabel = label || 'LOW RISK';

  if (score >= 0.7) {
    colorStyle = 'bg-rose-500/15 text-rose-400 border-rose-500/40 glow-crimson-sm animate-pulse';
    badgeLabel = label || 'HIGH RISK';
  } else if (score >= 0.4) {
    colorStyle = 'bg-amber-500/15 text-amber-400 border-amber-500/40 glow-amber-sm';
    badgeLabel = label || 'MEDIUM RISK';
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-mono font-medium tracking-wider uppercase ${colorStyle} ${className}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
      {badgeLabel} {score !== undefined && `(${score.toFixed(2)})`}
    </span>
  );
}
