import React, { useEffect, useState, useCallback } from 'react';
import { TopNav } from './components/TopNav';
import { DashboardPage } from './pages/DashboardPage';
import { PipelinePage } from './pages/PipelinePage';
import { EnrollmentPage } from './pages/EnrollmentPage';
import { PolicyPage } from './pages/PolicyPage';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { DocsPage } from './pages/DocsPage';
import { checkAllHealth, PipelineResponse } from './api';

const PAGES = ['dashboard', 'pipeline', 'enrollment', 'policy', 'architecture', 'docs'] as const;
type Page = typeof PAGES[number];

const DEFAULT_TENANT = 'demo-tenant';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<Page>('dashboard');
  const [healthCount, setHealthCount] = useState({ healthy: 0, total: 7 });
  const [recentResults, setRecentResults] = useState<PipelineResponse[]>([]);
  const [transitioning, setTransitioning] = useState(false);

  useEffect(() => {
    const handleHash = () => {
      const hash = window.location.hash.replace('#', '') || 'dashboard';
      if (PAGES.includes(hash as Page)) setActivePage(hash as Page);
    };
    handleHash();
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, []);

  const navigate = useCallback((page: string) => {
    setTransitioning(true);
    setTimeout(() => {
      window.location.hash = page;
      setActivePage(page as Page);
      window.scrollTo({ top: 0, behavior: 'smooth' });
      setTimeout(() => setTransitioning(false), 50);
    }, 200);
  }, []);

  useEffect(() => {
    const poll = async () => {
      const results = await checkAllHealth();
      setHealthCount({ healthy: results.filter(r => r.status === 'healthy').length, total: results.length });
    };
    poll();
    const iv = setInterval(poll, 15000);
    return () => clearInterval(iv);
  }, []);

  const handlePipelineResult = useCallback((r: PipelineResponse) => {
    setRecentResults(prev => [...prev, r]);
  }, []);

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard': return <DashboardPage tenantId={DEFAULT_TENANT} recentResults={recentResults} onNavigate={navigate} />;
      case 'pipeline': return <PipelinePage tenantId={DEFAULT_TENANT} onResult={handlePipelineResult} />;
      case 'enrollment': return <EnrollmentPage tenantId={DEFAULT_TENANT} />;
      case 'policy': return <PolicyPage tenantId={DEFAULT_TENANT} />;
      case 'architecture': return <ArchitecturePage />;
      case 'docs': return <DocsPage />;
      default: return <DashboardPage tenantId={DEFAULT_TENANT} recentResults={recentResults} onNavigate={navigate} />;
    }
  };

  return (
    <div className="min-h-screen" style={{ background: 'inherit' }}>
      <TopNav activePage={activePage} onNavigate={navigate} healthyCount={healthCount.healthy} totalCount={healthCount.total} />
      <main className={`transition-all duration-300 ${transitioning ? 'opacity-0 translate-y-3' : 'opacity-100 translate-y-0'}`}>
        {renderPage()}
      </main>
      {/* Footer */}
      <footer className="border-t border-[var(--line)] relative overflow-hidden">
        <div className="absolute left-0 right-0 top-0 h-px" style={{ background: 'linear-gradient(90deg, transparent, var(--accent), var(--cyan), transparent)', opacity: 0.45 }} />
        <div className="w-[min(1280px,calc(100%-64px))] mx-auto py-10 flex justify-between text-[var(--muted)] text-[13px]">
          <div>© 2026 Prime Vector / Satya</div>
          <div className="font-mono text-xs transition-colors hover:text-[var(--accent)]">THREE SIGNALS · EIGHT SERVICES · FAIL SAFE</div>
        </div>
      </footer>
    </div>
  );
};

export default App;
