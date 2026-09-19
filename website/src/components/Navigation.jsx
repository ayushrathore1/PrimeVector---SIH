import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Mic, Radio, Activity, FileCode, Info, ChevronRight, Menu, X, BarChart3, Smartphone } from 'lucide-react';

export default function Navigation({ activeTab, setActiveTab }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 15);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { id: 'home', label: 'Overview', icon: Shield },
    { id: 'detect', label: 'Detector', icon: Mic },
    { id: 'stream', label: 'Live Stream', icon: Radio },
    { id: 'status', label: 'Status', icon: Activity },
    { id: 'docs', label: 'Docs', icon: FileCode },
    { id: 'about', label: 'Architecture', icon: Info },
  ];

  const extraMobileItems = [
    { id: 'usage', label: 'Usage', icon: BarChart3 },
    { id: 'android', label: 'Mobile App', icon: Smartphone }
  ];

  const handleNavClick = (id) => {
    setActiveTab(id);
    setMobileMenuOpen(false);
  };

  return (
    <header className={`sticky top-0 z-50 transition-all duration-200 ${
      scrolled 
        ? 'bg-white/90 backdrop-blur-md border-b border-forest/10 py-3 shadow-xs' 
        : 'bg-white/70 backdrop-blur-sm border-b border-transparent py-4'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          
          {/* Logo */}
          <div
            onClick={() => handleNavClick('home')}
            className="flex items-center gap-2.5 cursor-pointer group select-none"
          >
            <div className="w-7 h-7 rounded-md bg-forest flex items-center justify-center text-lemongrass shadow-xs group-hover:scale-105 transition-transform">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L3 9V20C3 20.5523 3.44772 21 4 21H20C20.5523 21 21 20.5523 21 20V9L12 2Z" fill="currentColor" fillOpacity="0.2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M12 6L16 11H8L12 6Z" fill="currentColor"/>
                <path d="M12 11V17" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
            <span className="font-display text-lg font-bold tracking-tight text-forest">
              PRIME<span className="text-forest/60 font-medium">VECTOR</span>
            </span>
          </div>

          {/* Minimal Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-7">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  className={`relative text-xs font-semibold tracking-wide transition-colors py-1 cursor-pointer select-none ${
                    isActive ? 'text-forest font-bold' : 'text-forest/60 hover:text-forest'
                  }`}
                >
                  {item.label}
                  {isActive && (
                    <motion.span
                      layoutId="minimalNavDot"
                      className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-forest rounded-full"
                      transition={{ type: "spring", stiffness: 500, damping: 35 }}
                    />
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right Action */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => handleNavClick('detect')}
              className="group inline-flex items-center gap-1.5 bg-forest text-lemongrass hover:bg-forest-hover font-semibold text-xs px-3.5 py-1.5 rounded-md shadow-xs transition-all active:scale-95 cursor-pointer"
            >
              <span>Test Detector</span>
              <ChevronRight size={13} className="group-hover:translate-x-0.5 transition-transform" />
            </button>

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-1.5 text-forest/70 hover:text-forest transition-colors cursor-pointer"
              aria-label="Toggle Menu"
            >
              {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {/* Mobile Menu Drawer */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.15 }}
              className="overflow-hidden md:hidden pt-3 pb-1 border-t border-forest/10 mt-3"
            >
              <div className="grid grid-cols-2 gap-1.5">
                {[...navItems, ...extraMobileItems].map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => handleNavClick(item.id)}
                      className={`flex items-center gap-2 px-3 py-2 rounded-md text-xs font-semibold transition-colors cursor-pointer text-left ${
                        isActive ? 'bg-forest text-lemongrass font-bold' : 'text-forest/70 hover:bg-sage-1 hover:text-forest'
                      }`}
                    >
                      <Icon size={14} />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
}



