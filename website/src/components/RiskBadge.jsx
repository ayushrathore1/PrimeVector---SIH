import React from 'react';

export default function RiskBadge({ score, label, className = '' }) {
  let colorStyle = 'bg-emerald-100 text-emerald-900 border-emerald-300 shadow-sm';
  let badgeLabel = label || 'LOW RISK';

  if (score >= 0.7) {
    colorStyle = 'bg-rose-100 text-rose-900 border-rose-300 shadow-sm animate-pulse';
    badgeLabel = label || 'HIGH RISK';
  } else if (score >= 0.4) {
    colorStyle = 'bg-amber-100 text-amber-900 border-amber-300 shadow-sm';
    badgeLabel = label || 'MEDIUM RISK';
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-mono font-bold tracking-wider uppercase ${colorStyle} ${className}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {badgeLabel} {score !== undefined && `(${score.toFixed(2)})`}
    </span>
  );
}

