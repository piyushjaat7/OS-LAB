import React, { useEffect, useState } from 'react';
import { Cpu, Zap, Activity, Hash } from 'lucide-react';
import { useMetrics } from '../context/MetricsContext';
import { MetricCard } from '../components/common/MetricCard';
import { CoreUsageGrid } from '../components/charts/CoreUsageGrid';
import { LiveAreaChart } from '../components/charts/LiveAreaChart';
import { api } from '../services/api';
import { HistoricalSystemMetrics } from '../types/metrics';
import { formatFrequency, formatTime } from '../utils/formatters';

export const CPUPage: React.FC = () => {
  const { metrics, chartHistory, settings } = useMetrics();
  const [historyData, setHistoryData] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const cpu = metrics?.cpu;
  const cpuPercent = cpu?.usage_percent;

  // Fetch recent historical trend for comparison
  useEffect(() => {
    let mounted = true;
    const loadCpuHistory = async () => {
      setLoadingHistory(true);
      try {
        const docs = await api.getHistory({ limit: 40, order: 'desc' });
        if (mounted) {
          // Reverse so chronological order (left to right)
          const formatted = docs.reverse().map((d: HistoricalSystemMetrics) => ({
            timeStr: formatTime(d.timestamp),
            usagePercent: d.cpu?.usage_percent ?? null,
          }));
          setHistoryData(formatted);
        }
      } catch {
        // Fallback or empty
      } finally {
        if (mounted) setLoadingHistory(false);
      }
    };

    loadCpuHistory();
    const timer = setInterval(loadCpuHistory, 15000); // refresh history every 15s
    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Overall CPU Usage"
          value={cpuPercent !== null && cpuPercent !== undefined ? cpuPercent.toFixed(1) : 'Init'}
          unit="%"
          subtitle="Non-blocking interval sample"
          icon={Cpu}
          percentage={cpuPercent}
          warningThreshold={settings.cpuWarning}
          criticalThreshold={settings.cpuCritical}
          colorTheme="cyan"
        />

        <MetricCard
          title="Operating Frequency"
          value={formatFrequency(cpu?.frequency?.current)}
          unit=""
          subtitle={`Min: ${formatFrequency(cpu?.frequency?.min)} • Max: ${formatFrequency(cpu?.frequency?.max)}`}
          icon={Zap}
          colorTheme="amber"
        />

        <MetricCard
          title="Physical Cores"
          value={cpu?.physical_cores ?? '-'}
          unit="cores"
          subtitle="Hardware CPU execution cores"
          icon={Hash}
          colorTheme="purple"
        />

        <MetricCard
          title="Logical Threads"
          value={cpu?.logical_cores ?? '-'}
          unit="vCPUs"
          subtitle="Hyper-threaded / virtual processors"
          icon={Activity}
          colorTheme="emerald"
        />
      </div>

      {/* Per-Core Breakdown Grid */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-sm text-white">Per-Core Workload Distribution</h3>
            <p className="text-xs text-gray-400">Independent logical processor utilization telemetry</p>
          </div>
          <span className="text-xs font-mono text-gray-400">
            {cpu?.per_core_usage?.length ?? 0} Cores Active
          </span>
        </div>
        <CoreUsageGrid perCoreUsage={cpu?.per_core_usage} />
      </div>

      {/* Real-time vs Historical Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Real-Time Area Chart */}
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-sm text-white">Live CPU Utilization</h3>
              <p className="text-xs text-gray-400">Continuous 1 Hz telemetry window</p>
            </div>
            <span className="text-xs font-semibold text-cyan-400 flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" /> Live Stream
            </span>
          </div>
          <LiveAreaChart
            data={chartHistory}
            series={[{ key: 'cpuPercent', name: 'CPU Usage', color: '#22d3ee' }]}
            yDomain={[0, 100]}
          />
        </div>

        {/* Historical Trend from MongoDB */}
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-sm text-white">MongoDB Historical CPU Trend</h3>
              <p className="text-xs text-gray-400">Persisted 5s interval historical snapshots</p>
            </div>
            {loadingHistory && <span className="text-xs text-gray-500">Syncing DB...</span>}
          </div>
          <LiveAreaChart
            data={historyData}
            series={[{ key: 'usagePercent', name: 'Historical CPU %', color: '#818cf8' }]}
            yDomain={[0, 100]}
          />
        </div>
      </div>
    </div>
  );
};
