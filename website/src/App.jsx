import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Navigation from './components/Navigation';
import Footer from './components/Footer';

import HomePage from './pages/HomePage';
import DetectPage from './pages/DetectPage';
import ApiDocsPage from './pages/ApiDocsPage';
import PricingPage from './pages/PricingPage';
import UsagePage from './pages/UsagePage';
import AboutPage from './pages/AboutPage';
import StatusPage from './pages/StatusPage';
import LiveStreamPage from './pages/LiveStreamPage';
import AndroidPage from './pages/AndroidPage';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');

  const renderPage = () => {
    switch (activeTab) {
      case 'home':
        return <HomePage setActiveTab={setActiveTab} />;
      case 'detect':
        return <DetectPage />;
      case 'docs':
        return <ApiDocsPage />;
      case 'pricing':
        return <PricingPage />;
      case 'usage':
        return <UsagePage />;
      case 'about':
        return <AboutPage />;
      case 'status':
        return <StatusPage />;
      case 'stream':
        return <LiveStreamPage />;
      case 'android':
        return <AndroidPage />;
      default:
        return <HomePage setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-white text-forest font-sans">
      <Navigation
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <main className="flex-1 bg-white">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.2 }}
          >
            {renderPage()}
          </motion.div>
        </AnimatePresence>
      </main>

      <Footer setActiveTab={setActiveTab} />
    </div>
  );
}
