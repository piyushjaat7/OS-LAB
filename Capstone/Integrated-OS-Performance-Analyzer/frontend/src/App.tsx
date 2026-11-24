import React, { useState } from 'react';
import { MetricsProvider } from './context/MetricsContext';
import { Sidebar, PageId } from './components/layout/Sidebar';
import { TopNav } from './components/layout/TopNav';
import { OverviewPage } from './pages/OverviewPage';
import { CPUPage } from './pages/CPUPage';
import { MemoryPage } from './pages/MemoryPage';
import { DiskPage } from './pages/DiskPage';
import { NetworkPage } from './pages/NetworkPage';
import { ProcessPage } from './pages/ProcessPage';
import { AnalysisPage } from './pages/AnalysisPage';
import { SchedulingPage } from './pages/SchedulingPage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsPage } from './pages/SettingsPage';

const pageTitles: Record<PageId, string> = {
  overview: 'System Overview Dashboard',
  cpu: 'CPU Performance & Core Metrics',
  memory: 'Memory & Swap Utilization',
  disk: 'Disk Partitions & Storage I/O',
  network: 'Network Interfaces & Throughput',
  processes: 'Running System Processes',
  analysis: 'System Health & Bottleneck Analysis',
  scheduling: 'CPU Scheduling Simulator & Benchmark',
  history: 'MongoDB Historical Analytics',
  settings: 'Configuration & Settings',
};

export const AppContent: React.FC = () => {
  const [activePage, setActivePage] = useState<PageId>('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const renderActivePage = () => {
    switch (activePage) {
      case 'overview':
        return <OverviewPage />;
      case 'cpu':
        return <CPUPage />;
      case 'memory':
        return <MemoryPage />;
      case 'disk':
        return <DiskPage />;
      case 'network':
        return <NetworkPage />;
      case 'processes':
        return <ProcessPage />;
      case 'analysis':
        return <AnalysisPage />;
      case 'scheduling':
        return <SchedulingPage />;
      case 'history':
        return <HistoryPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <OverviewPage />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-gray-100 flex">
      {/* Navigation Sidebar */}
      <Sidebar
        activePage={activePage}
        onPageChange={setActivePage}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col min-h-screen transition-all duration-300 ${
          sidebarCollapsed ? 'pl-20' : 'pl-64'
        }`}
      >
        <TopNav pageTitle={pageTitles[activePage]} />

        <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
          {renderActivePage()}
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <MetricsProvider>
      <AppContent />
    </MetricsProvider>
  );
};

export default App;
