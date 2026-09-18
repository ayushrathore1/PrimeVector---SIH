import React from 'react';
import { Shield, Mic, FileCode, CreditCard, BarChart3, Info, Sparkles, ChevronRight } from 'lucide-react';

export default function Navigation({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'home', label: 'Overview', icon: Shield },
    { id: 'detect', label: 'Detector', icon: Mic },
    { id: 'docs', label: 'API & Docs', icon: FileCode },
    { id: 'pricing', label: 'Pricing', icon: CreditCard },
    { id: 'usage', label: 'Usage', icon: BarChart3 },
    { id: 'about', label: 'Architecture', icon: Info },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-forest/15 transition-all shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-18 py-3">
          {/* Logo */}
          <div
            onClick={() => setActiveTab('home')}
            className="flex items-center gap-3 cursor-pointer group select-none"
          >
            <div className="w-9 h-9 rounded-lg bg-forest flex items-center justify-center text-lemongrass shadow-sm group-hover:scale-105 transition-transform">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L3 9V20C3 20.5523 3.44772 21 4 21H20C20.5523 21 21 20.5523 21 20V9L12 2Z" fill="currentColor" fillOpacity="0.2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M12 6L16 11H8L12 6Z" fill="currentColor"/>
                <path d="M12 11V17" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
            <div className="flex items-center gap-2.5">
              <span className="font-display text-xl font-extrabold tracking-tight text-forest">
                PRIME<span className="text-forest/70 font-semibold">VECTOR</span>
              </span>
              <span className="hidden sm:inline-flex items-center gap-1 bg-sage-1 border border-forest/15 px-2.5 py-0.5 rounded text-[11px] font-mono text-forest font-bold">
                <Sparkles size={11} className="text-forest" />
                Dhwani 2 Engine
              </span>
            </div>
          </div>

          {/* Main Nav Items */}
          <nav className="hidden lg:flex items-center gap-8">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`relative text-sm font-semibold transition-colors py-1 cursor-pointer ${
                    isActive
                      ? 'text-forest font-bold'
                      : 'text-forest/80 hover:text-forest'
                  }`}
                >
                  {item.label}
                  {isActive && (
                    <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-forest rounded-full" />
                  )}
                </button>
              );
            })}
          </nav>

          {/* Action CTAs */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setActiveTab('docs')}
              className="hidden sm:inline-flex text-xs font-bold text-forest hover:text-forest-dark px-3.5 py-2 rounded-md hover:bg-sage-1 transition-colors cursor-pointer"
            >
              API Key & Docs
            </button>

            <button
              onClick={() => setActiveTab('detect')}
              className="group relative inline-flex items-center gap-2 bg-forest text-lemongrass hover:bg-forest-hover font-bold text-xs sm:text-sm px-4.5 py-2.5 rounded-md shadow-spade transition-all transform active:scale-95 cursor-pointer"
            >
              <Mic size={15} />
              <span>Test Detector</span>
              <ChevronRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>
        </div>

        {/* Mobile Nav strip */}
        <div className="lg:hidden flex items-center justify-between py-2.5 border-t border-forest/10 overflow-x-auto gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold whitespace-nowrap transition-colors cursor-pointer ${
                  isActive ? 'bg-forest text-lemongrass' : 'text-forest/80 hover:text-forest bg-sage-1'
                }`}
              >
                <Icon size={14} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
}
