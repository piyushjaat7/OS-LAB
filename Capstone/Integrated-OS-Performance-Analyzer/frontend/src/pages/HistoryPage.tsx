import React, { useEffect, useState, useCallback } from 'react';
import {
  History,
  Cpu,
  Database,
  Network,
  Calendar,
  RefreshCw,
  Layers,
} from 'lucide-react';
import { api } from '../services/api';
import { HistoricalMetricsSummary, HistoricalSystemMetrics } from '../types/metrics';
import { MetricCard } from '../components/common/MetricCard';
import { LiveAreaChart } from '../components/charts/LiveAreaChart';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { formatPercent, formatThroughput, formatTime, formatDateTime } from '../utils/formatters';

type TimeRangePreset = '15m' | '1h' | '6h' | '24h' | 'all';

export const HistoryPage: React.FC = () => {
  const [rangePreset, setRangePreset] = useState<TimeRangePreset>('1h');
  const [historyDocs, setHistoryDocs] = useState<HistoricalSystemMetrics[]>([]);
  const [summary, setSummary] = useState<HistoricalMetricsSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const calculateTimeRange = useCallback((): { start_time?: string; end_time?: string } => {
    if (rangePreset === 'all') return {};
    const now = new Date();
    let past = new Date();

    switch (rangePreset) {
      case '15m':
        past = new Date(now.getTime() - 15 * 60 * 1000);
        break;
      case '1h':
        past = new Date(now.getTime() - 60 * 60 * 1000);
        break;
      case '6h':
        past = new Date(now.getTime() - 6 * 60 * 60 * 1000);
        break;
      case '24h':
        past = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        break;
    }

    return {
      start_time: past.toISOString(),
      end_time: now.toISOString(),
    };
  }, [rangePreset]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    const timeFilter = calculateTimeRange();

    try {
      const [docsRes, summaryRes] = await Promise.all([
        api.getHistory({ ...timeFilter, limit: 100, order: 'desc' }),
        api.getHistorySummary(timeFilter),
      ]);

      setHistoryDocs(docsRes);
      setSummary(summaryRes);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch historical analytics from MongoDB.');
    } finally {
      setLoading(false);
    }
  }, [calculateTimeRange]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Transform docs for charts in chronological order (left to right)
  const chartPoints = [...historyDocs].reverse().map((d) => ({
    timeStr: formatTime(d.timestamp),
    fullTime: formatDateTime(d.timestamp),
    cpuPercent: d.cpu?.usage_percent ?? null,
    memoryPercent: d.memory?.percent ?? null,
    swapPercent: d.memory?.swap_percent ?? null,
    netSent: d.network?.throughput_sent_bytes_per_sec ?? null,
    netRecv: d.network?.throughput_recv_bytes_per_sec ?? null,
  }));

  return (
    <div className="space-y-6">
      {/* Range Controls Header */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 rounded-xl border border-gray-800 bg-gray-900/60 p-4 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <History className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-white">MongoDB Historical Intelligence</h3>
            <p className="text-xs text-gray-400">Aggregated long-term performance telemetry</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 bg-gray-800/80 p-1 rounded-xl border border-gray-700/60">
            {(['15m', '1h', '6h', '24h', 'all'] as TimeRangePreset[]).map((preset) => (
              <button
                key={preset}
                onClick={() => setRangePreset(preset)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  rangePreset === preset
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {preset === 'all' ? 'All' : preset.toUpperCase()}
              </button>
            ))}
          </div>

          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold border border-gray-700 bg-gray-800/80 text-gray-300 hover:text-white transition-all disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
            <span>Reload</span>
          </button>
        </div>
      </div>

      {loading && historyDocs.length === 0 ? (
        <LoadingSpinner message="Querying MongoDB historical collection & pipeline aggregates..." size="lg" />
      ) : error ? (
        <div className="p-4 rounded-xl border border-rose-800/40 bg-rose-950/20 text-rose-300 text-xs">
          {error}
        </div>
      ) : historyDocs.length === 0 ? (
        <EmptyState
          title="No Historical Records"
          description="The background persistence service is currently accumulating snapshots. Please allow a few seconds for new data to persist."
        />
      ) : (
        <>
          {/* Summary KPI Cards from MongoDB Pipeline */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <MetricCard
              title="Average CPU Load"
              value={formatPercent(summary?.cpu_avg_percent)}
              subtitle={`Peak: ${formatPercent(summary?.cpu_max_percent)}`}
              icon={Cpu}
              colorTheme="cyan"
            />

            <MetricCard
              title="Average Memory (RAM)"
              value={formatPercent(summary?.memory_avg_percent)}
              subtitle={`Peak: ${formatPercent(summary?.memory_max_percent)}`}
              icon={Database}
              colorTheme="purple"
            />

            <MetricCard
              title="Average Network Rx"
              value={formatThroughput(summary?.network_avg_bytes_recv_per_sec)}
              subtitle={`Tx: ${formatThroughput(summary?.network_avg_bytes_sent_per_sec)}`}
              icon={Network}
              colorTheme="emerald"
            />

            <MetricCard
              title="Stored Sample Count"
              value={(summary?.sample_count ?? 0).toLocaleString()}
              unit="snapshots"
              subtitle="Aggregated in window"
              icon={Layers}
              colorTheme="amber"
            />

            <MetricCard
              title="Sample Window"
              value={summary?.start_time ? formatTime(summary.start_time) : '-'}
              subtitle={summary?.end_time ? `to ${formatTime(summary.end_time)}` : '-'}
              icon={Calendar}
              colorTheme="blue"
            />
          </div>

          {/* Historical Trends Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* CPU Historical Timeline */}
            <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-sm text-white">Historical Processor Utilization (%)</h3>
                  <p className="text-xs text-gray-400">Computed over {historyDocs.length} stored samples</p>
                </div>
              </div>
              <LiveAreaChart
                data={chartPoints}
                series={[{ key: 'cpuPercent', name: 'CPU %', color: '#22d3ee' }]}
                yDomain={[0, 100]}
              />
            </div>

            {/* Memory Historical Timeline */}
            <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-sm text-white">Historical Memory (RAM & Swap)</h3>
                  <p className="text-xs text-gray-400">Physical RAM and Swap utilization trajectories</p>
                </div>
              </div>
              <LiveAreaChart
                data={chartPoints}
                series={[
                  { key: 'memoryPercent', name: 'RAM %', color: '#c084fc' },
                  { key: 'swapPercent', name: 'Swap %', color: '#fbbf24' },
                ]}
                yDomain={[0, 100]}
              />
            </div>
          </div>

          {/* Historical Network Throughput */}
          <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold text-sm text-white">Historical Network Traffic Rates</h3>
                <p className="text-xs text-gray-400">Upload vs Download throughput history</p>
              </div>
            </div>
            <LiveAreaChart
              data={chartPoints}
              series={[
                { key: 'netRecv', name: 'Download (B/s)', color: '#34d399' },
                { key: 'netSent', name: 'Upload (B/s)', color: '#fbbf24' },
              ]}
              yDomain={['auto', 'auto']}
              valueFormatter={(val) => formatThroughput(val)}
            />
          </div>
        </>
      )}
    </div>
  );
};
