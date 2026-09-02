import React from 'react';
import { ShieldCheck, Activity, Radio, FileCode, BarChart3, Smartphone, Info, ShieldAlert } from 'lucide-react';

export default function Navigation({ activeTab, setActiveTab, isLiveOnline }) {
  const navItems = [
    { id: 'home', label: 'Overview', icon: ShieldCheck },
    { id: 'status', label: 'System Status', icon: Activity },
    { id: 'demo', label: 'Live Stream', icon: Radio },
    { id: 'docs', label: 'API Docs', icon: FileCode },
    { id: 'usage', label: 'Usage', icon: BarChart3 },
    { id: 'android', label: 'Android Client', icon: Smartphone },
    { id: 'about', label: 'About', icon: Info },
  ];

  return (
    <header className="sticky top-0 z-50 bg-obsidian-950/90 backdrop-blur-md border-b border-obsidian-700/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div 
            onClick={() => setActiveTab('home')}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-9 h-9 rounded-lg bg-obsidian-800 border border-forensic-amber/40 flex items-center justify-center group-hover:border-forensic-amber transition-colors shadow-amber-glow">
              <ShieldAlert className="w-5 h-5 text-forensic-amber" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-serif text-lg font-bold tracking-tight text-white group-hover:text-forensic-amber transition-colors">
                  PRIME<span className="text-forensic-amber">VECTOR</span>
                </span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-obsidian-800 text-slate-400 border border-obsidian-700">
                  SIH 2026
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono hidden sm:block">
                Voice Integrity & Risk Fusion Engine
              </p>
            </div>
          </div>

          {/* Nav Links */}
          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-obsidian-800 text-forensic-amber border border-forensic-amber/30 shadow-amber-glow'
                      : 'text-slate-300 hover:text-white hover:bg-obsidian-850'
                  }`}
                >
                  <Icon size={16} className={isActive ? 'text-forensic-amber' : 'text-slate-400'} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Status Indicator Pill */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setActiveTab('status')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-mono transition-all ${
                isLiveOnline
                  ? 'bg-emerald-950/40 text-emerald-400 border-emerald-500/30 hover:border-emerald-500'
                  : 'bg-amber-950/40 text-amber-400 border-amber-500/30 hover:border-amber-500'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${isLiveOnline ? 'bg-emerald-400 animate-ping' : 'bg-amber-400'}`}></span>
              <span className="hidden sm:inline">{isLiveOnline ? '8/8 SERVICES ONLINE' : 'SYSTEM DEGRADED'}</span>
              <span className="sm:hidden">{isLiveOnline ? 'LIVE' : 'DEGRADED'}</span>
            </button>
          </div>
        </div>

        {/* Mobile Navigation Bar */}
        <div className="lg:hidden flex items-center justify-between py-2 border-t border-obsidian-800 overflow-x-auto gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex flex-col items-center gap-1 px-3 py-1.5 rounded text-xs font-mono whitespace-nowrap ${
                  isActive ? 'text-forensic-amber bg-obsidian-800' : 'text-slate-400'
                }`}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
}
