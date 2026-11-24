import React from 'react';

interface StatusPillProps {
  status: 'connected' | 'connecting' | 'disconnected' | 'error' | 'healthy' | 'unhealthy' | 'checking';
  label?: string;
  type?: 'ws' | 'rest';
}

export const StatusPill: React.FC<StatusPillProps> = ({ status, label, type = 'ws' }) => {
  const isHealthy = status === 'connected' || status === 'healthy';
  const isPending = status === 'connecting' || status === 'checking';

  const dotColor = isHealthy
    ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]'
    : isPending
    ? 'bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(251,191,36,0.6)]'
    : 'bg-rose-400 shadow-[0_0_8px_rgba(248,113,113,0.6)]';

  const containerStyle = isHealthy
    ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/40'
    : isPending
    ? 'bg-amber-950/40 text-amber-300 border-amber-800/40'
    : 'bg-rose-950/40 text-rose-300 border-rose-800/40';

  const defaultLabel = type === 'ws'
    ? status === 'connected' ? 'Live Stream' : status === 'connecting' ? 'Connecting WS...' : 'WS Offline'
    : status === 'healthy' ? 'Backend Ready' : status === 'checking' ? 'Checking API...' : 'API Offline';

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium border backdrop-blur-md transition-colors ${containerStyle}`}
    >
      <span className={`h-2 w-2 rounded-full ${dotColor}`} />
      <span>{label || defaultLabel}</span>
    </div>
  );
};
