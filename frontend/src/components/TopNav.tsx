import React from 'react';

interface TopNavProps {
  activePage: string;
  onNavigate: (page: string) => void;
  healthyCount: number;
  totalCount: number;
}

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'enrollment', label: 'Enrollment' },
  { id: 'policy', label: 'Policy' },
  { id: 'architecture', label: 'Architecture' },
  { id: 'docs', label: 'API' },
];

export const TopNav: React.FC<TopNavProps> = ({ activePage, onNavigate, healthyCount, totalCount }) => {
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--line)]" style={{
      background: 'rgba(246,246,242,0.94)',
      backdropFilter: 'blur(12px)',
      boxShadow: '0 8px 30px rgba(17,19,16,0.035)',
    }}>
      <div className="w-[min(1280px,calc(100%-64px))] mx-auto h-[72px] flex items-center justify-between">
        {/* Logo */}
        <button onClick={() => onNavigate('dashboard')} className="flex items-center gap-3 font-semibold tracking-tight cursor-pointer group">
          <div className="w-7 h-7 border-[1.5px] border-[var(--ink)] grid place-items-center font-mono text-xs transition-all duration-300 group-hover:rotate-[-8deg] group-hover:bg-[var(--ink)] group-hover:text-white">
            S
          </div>
          <span className="text-[var(--ink)]">Satya</span>
        </button>

        {/* Nav Links */}
        <nav className="hidden md:flex gap-6 text-sm text-[var(--muted)]">
          {NAV_ITEMS.map(item => (
            <button key={item.id} onClick={() => onNavigate(item.id)}
              className={`transition-colors duration-200 cursor-pointer hover:text-[var(--ink)] ${activePage === item.id ? 'text-[var(--ink)] font-medium' : ''}`}>
              {item.label}
            </button>
          ))}
        </nav>

        {/* System Status */}
        <div className="flex items-center gap-2 font-mono text-[11px] whitespace-nowrap" style={{ color: healthyCount === totalCount ? 'var(--success)' : healthyCount > 0 ? 'var(--warning)' : 'var(--danger)' }}>
          <span className="status-dot" style={{ background: healthyCount === totalCount ? 'var(--success)' : healthyCount > 0 ? 'var(--warning)' : 'var(--danger)' }} />
          {healthyCount === totalCount ? 'SYSTEM ONLINE' : `${healthyCount}/${totalCount} ONLINE`}
        </div>
      </div>
    </header>
  );
};
