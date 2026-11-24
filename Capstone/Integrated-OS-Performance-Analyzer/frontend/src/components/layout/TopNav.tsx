import React, { useState } from 'react';
import { RefreshCw, Clock } from 'lucide-react';
import { useMetrics } from '../../context/MetricsContext';
import { StatusPill } from '../common/StatusPill';
import { formatTime } from '../../utils/formatters';

interface TopNavProps {
  pageTitle: string;
}

export const TopNav: React.FC<TopNavProps> = ({ pageTitle }) => {
  const { wsStatus, restStatus, lastUpdated, refresh } = useMetrics();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refresh();
    } finally {
      setTimeout(() => setIsRefreshing(false), 500);
    }
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-gray-800/80 bg-[#0B0F19]/80 px-6 backdrop-blur-md">
      {/* Page Title */}
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-bold text-white tracking-tight">{pageTitle}</h1>
      </div>

      {/* Connection & Telemetry Status */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* WebSocket Stream Indicator */}
        <StatusPill status={wsStatus} type="ws" />

        {/* REST API Status */}
        <StatusPill status={restStatus} type="rest" />

        {/* Timestamp & Refresh Button */}
        <div className="hidden sm:flex items-center gap-2 pl-2 border-l border-gray-800 text-xs text-gray-400">
          <Clock className="h-3.5 w-3.5 text-gray-500" />
          <span className="font-mono">{formatTime(lastUpdated)}</span>
        </div>

        <button
          onClick={handleManualRefresh}
          disabled={isRefreshing}
          title="Manual refresh from REST endpoint"
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-gray-800 bg-gray-900/60 text-gray-400 hover:text-white hover:border-gray-700 hover:bg-gray-800/60 transition-all active:scale-95 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
        </button>
      </div>
    </header>
  );
};
