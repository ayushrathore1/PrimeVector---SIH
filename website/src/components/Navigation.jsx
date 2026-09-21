import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronRight, 
  Menu, 
  X, 
  User, 
  Shield, 
  Mic, 
  Radio, 
  Activity, 
  FileCode, 
  Info,
  BarChart3,
  Smartphone
} from 'lucide-react';

export default function Navigation({ activeTab, setActiveTab }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: 'home', label: 'Overview' },
    { id: 'detect', label: 'Detector' },
    { id: 'status', label: 'Status' },
    { id: 'docs', label: 'Docs' },
    { id: 'about', label: 'Architecture' },
  ];

  const extraMobileItems = [
    { id: 'usage', label: 'Usage', icon: BarChart3 },
    { id: 'android', label: 'Mobile App', icon: Smartphone }
  ];

  const handleNavClick = (id) => {
    setActiveTab(id);
    setMobileMenuOpen(false);
  };

  const isDetect = activeTab === 'detect';

  return (
    <header className="sticky top-0 z-40 bg-[#F3F6EE]/90 backdrop-blur-md border-b border-[#E5EAE0] transition-all duration-150 py-3 select-none">
      <div className="w-full px-4 sm:px-8">
        <div className="flex items-center justify-between">
          
          {/* Left: Logo */}
          <div
            onClick={() => handleNavClick('home')}
            className="flex items-center gap-2.5 cursor-pointer group select-none"
          >
            <div className="w-8 h-8 rounded-lg bg-[#0F1C0B] flex items-center justify-center text-[#C5FF34] shadow-sm group-hover:scale-105 transition-transform">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L3 9V20C3 20.5523 3.44772 21 4 21H20C20.5523 21 21 20.5523 21 20V9L12 2Z" fill="currentColor" fillOpacity="0.2" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M12 6L16 11H8L12 6Z" fill="currentColor"/>
                <path d="M12 11V17" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"/>
              </svg>
            </div>
            <span className="font-display text-base sm:text-lg font-black tracking-wider text-[#0B150A]">
              PRIMEVECTOR
            </span>
          </div>

          {/* Center: Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-7 lg:gap-8">
            {navItems.map((item, idx) => {
              const isActive = (item.label === 'Detector' && activeTab === 'detect') ||
                               (item.label === 'Overview' && activeTab === 'home') ||
                               (item.label === 'Status' && activeTab === 'status') ||
                               (item.label === 'Docs' && activeTab === 'docs') ||
                               (item.label === 'Architecture' && activeTab === 'about');
              return (
                <button
                  key={`${item.id}-${idx}`}
                  onClick={() => handleNavClick(item.id)}
                  className={`relative text-xs font-mono font-bold tracking-wide transition-colors py-1 cursor-pointer select-none ${
                    isActive ? 'text-[#0B150A]' : 'text-[#5A6556] hover:text-[#0B150A]'
                  }`}
                >
                  {item.label}
                  {isActive && (
                    <motion.span
                      layoutId="navActiveLine"
                      className="absolute -bottom-1 left-0 right-0 h-[2px] bg-[#0B150A] rounded-full"
                      transition={{ type: "spring", stiffness: 500, damping: 35 }}
                    />
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right Action: Pill Status + User Avatar */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => handleNavClick('detect')}
              className="inline-flex items-center gap-2 bg-[#0F1C0B] text-[#C5FF34] hover:bg-[#182C13] font-mono font-bold text-xs px-4 py-2 rounded-full shadow-xs transition-all active:scale-95 cursor-pointer border border-[#182C13]"
            >
              <span className="w-2 h-2 rounded-full bg-[#C5FF34] shadow-[0_0_8px_#C5FF34]"></span>
              <span>Live Sentinel Active</span>
              <ChevronRight size={13} className="text-[#C5FF34]" />
            </button>

            {/* User Avatar Circle */}
            <div 
              onClick={() => handleNavClick('about')}
              className="w-8 h-8 sm:w-9 sm:h-9 rounded-full border border-[#D5DDCF] bg-white flex items-center justify-center text-[#0B150A] hover:bg-[#EAEFE3] transition-all cursor-pointer shadow-2xs"
              title="User Profile & Security"
            >
              <User size={15} />
            </div>

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-1.5 text-[#0B150A] hover:bg-black/5 rounded-lg transition-colors cursor-pointer"
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
              className="overflow-hidden md:hidden pt-3 pb-2 border-t border-forest/10 mt-3 bg-white"
            >
              <div className="grid grid-cols-2 gap-1.5">
                {[...navItems, ...extraMobileItems].map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => handleNavClick(item.id)}
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold font-mono transition-colors cursor-pointer text-left ${
                        isActive ? 'bg-forest text-lemongrass' : 'text-forest/70 hover:bg-sage-1 hover:text-forest'
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



