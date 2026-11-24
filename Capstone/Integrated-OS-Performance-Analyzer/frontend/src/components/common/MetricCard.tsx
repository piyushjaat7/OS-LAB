import React from 'react';
import { LucideIcon } from 'lucide-react';
import { getStatusColor } from '../../utils/formatters';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  subtitle?: string;
  icon: LucideIcon;
  percentage?: number | null;
  warningThreshold?: number;
  criticalThreshold?: number;
  trend?: 'up' | 'down' | 'neutral';
  colorTheme?: 'emerald' | 'cyan' | 'purple' | 'amber' | 'blue' | 'indigo';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  subtitle,
  icon: Icon,
  percentage,
  warningThreshold = 75,
  criticalThreshold = 90,
  colorTheme = 'cyan',
}) => {
  const statusColor = getStatusColor(percentage, warningThreshold, criticalThreshold);

  const themeBorder = {
    cyan: 'hover:border-cyan-500/30',
    emerald: 'hover:border-emerald-500/30',
    purple: 'hover:border-purple-500/30',
    amber: 'hover:border-amber-500/30',
    blue: 'hover:border-blue-500/30',
    indigo: 'hover:border-indigo-500/30',
  }[colorTheme];

  const themeIconBg = {
    cyan: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    blue: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    indigo: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  }[colorTheme];

  return (
    <div
      className={`relative overflow-hidden rounded-xl bg-gray-900/60 p-5 backdrop-blur-md border border-gray-800 transition-all duration-300 ${themeBorder} shadow-lg shadow-black/20`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
          {title}
        </span>
        <div className={`rounded-lg p-2.5 border ${themeIconBg}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="font-mono text-3xl font-extrabold tracking-tight text-white">
          {value}
        </span>
        {unit && <span className="text-sm font-medium text-gray-400">{unit}</span>}
      </div>

      {percentage !== null && percentage !== undefined && (
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Utilization</span>
            <span className={`font-mono font-semibold ${statusColor.text}`}>
              {percentage.toFixed(1)}%
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-800">
            <div
              className={`h-full transition-all duration-500 ${statusColor.bar}`}
              style={{ width: `${Math.min(Math.max(percentage, 0), 100)}%` }}
            />
          </div>
        </div>
      )}

      {subtitle && (
        <p className="mt-3 text-xs text-gray-400 truncate">
          {subtitle}
        </p>
      )}
    </div>
  );
};
