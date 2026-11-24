import React, { useEffect, useState } from 'react';
import { Database, HardDriveDownload, Layers, PieChart } from 'lucide-react';
import { useMetrics } from '../context/MetricsContext';
import { MetricCard } from '../components/common/MetricCard';
import { LiveAreaChart } from '../components/charts/LiveAreaChart';
import { ProgressBar } from '../components/common/ProgressBar';
import { api } from '../services/api';
import { HistoricalSystemMetrics } from '../types/metrics';
import { formatBytes, formatTime } from '../utils/formatters';

export const MemoryPage: React.FC = () => {
  const { metrics, chartHistory, settings } = useMetrics();
  const [historyData, setHistoryData] = useState<any[]>([]);

  const vm = metrics?.memory?.virtual;
  const sm = metrics?.memory?.swap;

  useEffect(() => {
    let mounted = true;
    const loadMemHistory = async () => {
      try {
        const docs = await api.getHistory({ limit: 40, order: 'desc' });
        if (mounted) {
          const formatted = docs.reverse().map((d: HistoricalSystemMetrics) => ({
            timeStr: formatTime(d.timestamp),
            memoryPercent: d.memory?.percent ?? null,
            swapPercent: d.memory?.swap_percent ?? null,
          }));
          setHistoryData(formatted);
        }
      } catch {
        // Fallback
      }
    };

    loadMemHistory();
    const timer = setInterval(loadMemHistory, 15000);
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
          title="Virtual RAM Used"
          value={formatBytes(vm?.used)}
          subtitle={`${formatBytes(vm?.available)} available`}
          icon={Database}
          percentage={vm?.percent}
          warningThreshold={settings.memoryWarning}
          criticalThreshold={settings.memoryCritical}
          colorTheme="purple"
        />

        <MetricCard
          title="Total Physical RAM"
          value={formatBytes(vm?.total)}
          subtitle="Installed hardware capacity"
          icon={Layers}
          colorTheme="cyan"
        />

        <MetricCard
          title="Swap Memory Used"
          value={formatBytes(sm?.used)}
          subtitle={`${formatBytes(sm?.free)} free`}
          icon={HardDriveDownload}
          percentage={sm?.percent}
          warningThreshold={75}
          criticalThreshold={90}
          colorTheme="amber"
        />

        <MetricCard
          title="Total Swap Capacity"
          value={formatBytes(sm?.total)}
          subtitle="Paging file / partition capacity"
          icon={PieChart}
          colorTheme="emerald"
        />
      </div>

      {/* Memory Allocation Detailed Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Virtual RAM Breakdown */}
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-sm text-white">Physical Memory (RAM) Allocation</h3>
            <span className="font-mono text-sm font-bold text-purple-400">
              {vm?.percent !== undefined ? `${vm.percent.toFixed(1)}%` : 'N/A'}
            </span>
          </div>

          <ProgressBar
            value={vm?.percent}
            warningThreshold={settings.memoryWarning}
            criticalThreshold={settings.memoryCritical}
            heightClass="h-3"
            showPercent={false}
          />

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
            <div className="p-3 rounded-lg bg-gray-800/40 border border-gray-800">
              <span className="text-[10px] text-gray-400 uppercase font-semibold">Total</span>
              <p className="font-mono text-sm font-bold text-white mt-0.5">{formatBytes(vm?.total)}</p>
            </div>
            <div className="p-3 rounded-lg bg-gray-800/40 border border-gray-800">
              <span className="text-[10px] text-gray-400 uppercase font-semibold">Used</span>
              <p className="font-mono text-sm font-bold text-purple-400 mt-0.5">{formatBytes(vm?.used)}</p>
            </div>
            <div className="p-3 rounded-lg bg-gray-800/40 border border-gray-800">
              <span className="text-[10px] text-gray-400 uppercase font-semibold">Available</span>
              <p className="font-mono text-sm font-bold text-emerald-400 mt-0.5">{formatBytes(vm?.available)}</p>
            </div>
            <div className="p-3 rounded-lg bg-gray-800/40 border border-gray-800">
              <span className="text-[10px] text-gray-400 uppercase font-semibold">Free</span>
              <p className="font-mono text-sm font-bold text-gray-300 mt-0.5">{formatBytes(vm?.free)}</p>
            </div>
          </div>
        </div>

        {/* Swap Memory Breakdown */}
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-sm text-white">Swap File Allocation</h3>
            <span className="font-mono text-sm font-bold text-amber-400">
              {sm?.percent !== undefined ? `${sm.percent.toFixed(1)}%` : 'N/A'}
            </span>
          </div>

          <ProgressBar
            value={sm?.percent}
            warningThreshold={75}
            criticalThreshold={90}
            heightClass="h-3"
            showPercent={false}
          />

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
            <div className="p-3 rounded-lg bg-gray-800/40 border border-gray-800">
              <span className="text-[10px] text-gray-400 uppercase font-semibold">Total</span>
              <p className="font-mono text-sm font-bold text-white mt-0.5">{formatBytes(sm?.total)}</p>
            </div>
            <div className="p-3 rounded-lg bg-gray-800/40 border border-gray-800">
              <span className="text-[10px] text-gray-400 uppercase font-semibold">Used</span>
              <p className="font-mono text-sm font-bold text-amber-400 mt-0.5">{formatBytes(sm?.used)}</p>
            </div>
            <div className="p-3 rounded-lg bg-gray-800/40 border border-gray-800">
              <span className="text-[10px] text-gray-400 uppercase font-semibold">Free</span>
              <p className="font-mono text-sm font-bold text-gray-300 mt-0.5">{formatBytes(sm?.free)}</p>
            </div>
            <div className="p-3 rounded-lg bg-gray-800/40 border border-gray-800">
              <span className="text-[10px] text-gray-400 uppercase font-semibold">In / Out</span>
              <p className="font-mono text-sm font-bold text-gray-300 mt-0.5">{formatBytes(sm?.sin)} / {formatBytes(sm?.sout)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Real-time vs Historical Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-sm text-white">Live RAM Utilization</h3>
              <p className="text-xs text-gray-400">Continuous WebSocket memory telemetry</p>
            </div>
          </div>
          <LiveAreaChart
            data={chartHistory}
            series={[{ key: 'memoryPercent', name: 'RAM Usage %', color: '#c084fc' }]}
            yDomain={[0, 100]}
          />
        </div>

        <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-sm text-white">MongoDB Historical Memory Trends</h3>
              <p className="text-xs text-gray-400">RAM and Swap utilization over historical window</p>
            </div>
          </div>
          <LiveAreaChart
            data={historyData}
            series={[
              { key: 'memoryPercent', name: 'RAM %', color: '#c084fc' },
              { key: 'swapPercent', name: 'Swap %', color: '#fbbf24' },
            ]}
            yDomain={[0, 100]}
          />
        </div>
      </div>
    </div>
  );
};
