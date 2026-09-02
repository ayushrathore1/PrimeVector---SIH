import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import barba from '@barba/core';
import Navigation from './components/Navigation';
import Footer from './components/Footer';

import HomePage from './pages/HomePage';
import StatusPage from './pages/StatusPage';
import LiveDemoPage from './pages/LiveDemoPage';
import ApiDocsPage from './pages/ApiDocsPage';
import UsagePage from './pages/UsagePage';
import AndroidPage from './pages/AndroidPage';
import AboutPage from './pages/AboutPage';

import { checkServiceHealth } from './utils/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [isLiveOnline, setIsLiveOnline] = useState(true);

  // Check orchestrator health on load
  useEffect(() => {
    async function initCheck() {
      const res = await checkServiceHealth(8080);
      setIsLiveOnline(res.status === 'online');
    }
    initCheck();
  }, []);

  // Barba.js Initialization
  useEffect(() => {
    try {
      barba.init({
        transitions: [
          {
            name: 'security-scan-transition',
            leave(data) {
              return new Promise((resolve) => {
                const overlay = document.createElement('div');
                overlay.className = 'barba-transition-overlay';
                document.body.appendChild(overlay);
                setTimeout(() => {
                  overlay.remove();
                  resolve();
                }, 300);
              });
            },
          },
        ],
      });
    } catch (e) {
      // Ignore fallback single page state if barba re-initializes
    }
  }, []);

  const renderPage = () => {
    switch (activeTab) {
      case 'home':
        return <HomePage setActiveTab={setActiveTab} />;
      case 'status':
        return <StatusPage />;
      case 'demo':
        return <LiveDemoPage />;
      case 'docs':
        return <ApiDocsPage />;
      case 'usage':
        return <UsagePage />;
      case 'android':
        return <AndroidPage />;
      case 'about':
        return <AboutPage />;
      default:
        return <HomePage setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-obsidian-950 text-slate-100 font-sans">
      <Navigation
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isLiveOnline={isLiveOnline}
      />

      <main className="flex-1" data-barba="container" data-barba-namespace={activeTab}>
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
          >
            {renderPage()}
          </motion.div>
        </AnimatePresence>
      </main>

      <Footer setActiveTab={setActiveTab} />
    </div>
  );
}
