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
import AndroidPage from './pages/AndroidPage';

export default function App() {
  const [activeTab, setActiveTab] = useState('detect');

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
      case 'android':
        return <AndroidPage />;
      default:
        return <HomePage setActiveTab={setActiveTab} />;
    }
  };

  const isDetect = activeTab === 'detect';

  return (
    <div className="min-h-screen flex flex-col bg-[#F3F6EE] text-[#0B150A] font-sans antialiased selection:bg-[#C5FF34] selection:text-[#0B150A]">
      <Navigation
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <main className={`flex-1 ${isDetect ? 'bg-[#F3F6EE]' : 'bg-white'}`}>
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 3 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -3 }}
            transition={{ duration: 0.15 }}
            className="h-full"
          >
            {renderPage()}
          </motion.div>
        </AnimatePresence>
      </main>

      {!isDetect && <Footer setActiveTab={setActiveTab} />}
    </div>
  );
}


