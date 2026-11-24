import React from 'react';
import {
  Cpu,
  Database,
  HardDrive,
  Network,
  Layers,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  ShieldCheck,
} from 'lucide-react';
import { useMetrics } from '../context/MetricsContext';
import { MetricCard } from '../components/common/MetricCard';
import { LiveAreaChart } from '../components/charts/LiveAreaChart';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { formatBytes, formatThroughput } from '../utils/formatters';

export const OverviewPage: React.FC = () => {
  const { metrics, chartHistory, settings, isLoading } = useMetrics();

  if (isLoading && !metrics) {
    return <LoadingSpinner message="Connecting to system telemetry stream..." size="lg" />;
  }

  const cpuPercent = metrics?.cpu?.usage_percent;
  const memPercent = metrics?.memory?.virtual?.percent;

  // Aggregate disk usage across unique filesystems
  let totalDisk = 0;
  let usedDisk = 0;
  let diskPercent: number | null = null;
  if (metrics?.disk) {
    if (metrics.disk.total_capacity_bytes !== undefined && metrics.disk.total_capacity_bytes !== null) {
      totalDisk = metrics.disk.total_capacity_bytes;
      usedDisk = metrics.disk.total_used_bytes ?? 0;
      diskPercent = metrics.disk.total_percent ?? null;
    } else if (metrics.disk.partitions) {
      const seenDevices = new Set<string>();
      for (const p of metrics.disk.partitions) {
        const devKey = p.partition.device || p.partition.mountpoint;
        if (seenDevices.has(devKey)) continue;
        seenDevices.add(devKey);
        if (p.usage) {
          totalDisk += p.usage.total;
          usedDisk += p.usage.used;
        }
      }
      if (totalDisk > 0) {
        diskPercent = (usedDisk / totalDisk) * 100;
      }
    }
  }

  const netSentRate = metrics?.network?.throughput?.bytes_sent_per_sec;
  const netRecvRate = metrics?.network?.throughput?.bytes_recv_per_sec;
  const totalProcesses = metrics?.processes?.total_processes ?? 0;

  // Alerts
  const alerts: { title: string; desc: string; type: 'warning' | 'critical' }[] = [];
  if (cpuPercent && cpuPercent >= settings.cpuCritical) {
    alerts.push({ title: 'Critical CPU Load', desc: `CPU utilization is at ${cpuPercent.toFixed(1)}%`, type: 'critical' });
  } else if (cpuPercent && cpuPercent >= settings.cpuWarning) {
    alerts.push({ title: 'High CPU Load', desc: `CPU utilization is at ${cpuPercent.toFixed(1)}%`, type: 'warning' });
  }

  if (memPercent && memPercent >= settings.memoryCritical) {
    alerts.push({ title: 'Critical RAM Usage', desc: `Memory utilization is at ${memPercent.toFixed(1)}%`, type: 'critical' });
  } else if (memPercent && memPercent >= settings.memoryWarning) {
    alerts.push({ title: 'High RAM Usage', desc: `Memory utilization is at ${memPercent.toFixed(1)}%`, type: 'warning' });
  }

  if (diskPercent && diskPercent >= settings.diskCritical) {
    alerts.push({ title: 'Critical Disk Capacity', desc: `Storage utilization is at ${diskPercent.toFixed(1)}%`, type: 'critical' });
  }

  // Top 5 processes by CPU
  const topProcesses = [...(metrics?.processes?.processes ?? [])]
    .sort((a, b) => (b.cpu_percent ?? 0) - (a.cpu_percent ?? 0))
    .slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Active Health Alert Banners */}
      {alerts.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {alerts.map((alert, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-3 p-4 rounded-xl border backdrop-blur-md ${
                alert.type === 'critical'
                  ? 'bg-rose-950/40 border-rose-800/60 text-rose-200'
                  : 'bg-amber-950/40 border-amber-800/60 text-amber-200'
              }`}
            >
              <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5 text-amber-400" />
              <div>
                <h4 className="font-semibold text-sm">{alert.title}</h4>
                <p className="text-xs text-gray-300 mt-0.5">{alert.desc}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex items-center gap-3 p-3.5 rounded-xl border border-emerald-800/30 bg-emerald-950/20 text-emerald-300 text-xs font-medium">
          <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0" />
          <span>All monitored subsystems are operating within configured healthy thresholds.</span>
        </div>
      )}

      {/* Main KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="CPU Usage"
          value={cpuPercent !== null && cpuPercent !== undefined ? cpuPercent.toFixed(1) : 'Init'}
          unit="%"
          subtitle={`${metrics?.cpu?.logical_cores ?? '-'} Cores (${metrics?.cpu?.frequency?.current?.toFixed(0) ?? '-'} MHz)`}
          icon={Cpu}
          percentage={cpuPercent}
          warningThreshold={settings.cpuWarning}
          criticalThreshold={settings.cpuCritical}
          colorTheme="cyan"
        />

        <MetricCard
          title="Memory (RAM)"
          value={memPercent !== null && memPercent !== undefined ? memPercent.toFixed(1) : 'N/A'}
          unit="%"
          subtitle={`${formatBytes(metrics?.memory?.virtual?.used)} / ${formatBytes(metrics?.memory?.virtual?.total)}`}
          icon={Database}
          percentage={memPercent}
          warningThreshold={settings.memoryWarning}
          criticalThreshold={settings.memoryCritical}
          colorTheme="purple"
        />

        <MetricCard
          title="Disk Capacity"
          value={diskPercent !== null ? diskPercent.toFixed(1) : 'N/A'}
          unit="%"
          subtitle={`${formatBytes(usedDisk)} / ${formatBytes(totalDisk)} used`}
          icon={HardDrive}
          percentage={diskPercent}
          warningThreshold={settings.diskWarning}
          criticalThreshold={settings.diskCritical}
          colorTheme="indigo"
        />

        <MetricCard
          title="Network Throughput"
          value={formatThroughput(netRecvRate)}
          unit=""
          subtitle={`↑ ${formatThroughput(netSentRate)}`}
          icon={Network}
          colorTheme="emerald"
        />

        <MetricCard
          title="Running Tasks"
          value={totalProcesses}
          unit="procs"
          subtitle={`${metrics?.processes?.processes?.filter((p) => p.status === 'running').length ?? 0} active threads`}
          icon={Layers}
          colorTheme="amber"
        />
      </div>

      {/* Real-time Trend Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU & Memory Utilization Timeline */}
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-sm text-white">Live Resource Utilization</h3>
              <p className="text-xs text-gray-400">Continuous CPU and Memory telemetry</p>
            </div>
            <div className="flex items-center gap-4 text-xs font-medium">
              <span className="flex items-center gap-1.5 text-cyan-400">
                <span className="h-2 w-2 rounded-full bg-cyan-400" /> CPU
              </span>
              <span className="flex items-center gap-1.5 text-purple-400">
                <span className="h-2 w-2 rounded-full bg-purple-400" /> RAM
              </span>
            </div>
          </div>
          <LiveAreaChart
            data={chartHistory}
            series={[
              { key: 'cpuPercent', name: 'CPU Usage', color: '#22d3ee' },
              { key: 'memoryPercent', name: 'RAM Usage', color: '#c084fc' },
            ]}
            yDomain={[0, 100]}
          />
        </div>

        {/* Network Throughput Timeline */}
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-sm text-white">Real-Time Network Activity</h3>
              <p className="text-xs text-gray-400">Instantaneous transfer rates (Upload vs Download)</p>
            </div>
            <div className="flex items-center gap-4 text-xs font-medium">
              <span className="flex items-center gap-1.5 text-emerald-400">
                <ArrowDownRight className="h-3.5 w-3.5" /> Download
              </span>
              <span className="flex items-center gap-1.5 text-amber-400">
                <ArrowUpRight className="h-3.5 w-3.5" /> Upload
              </span>
            </div>
          </div>
          <LiveAreaChart
            data={chartHistory}
            series={[
              { key: 'netRecvThroughput', name: 'Download', color: '#34d399' },
              { key: 'netSentThroughput', name: 'Upload', color: '#fbbf24' },
            ]}
            yDomain={['auto', 'auto']}
            valueFormatter={(val) => formatThroughput(val)}
          />
        </div>
      </div>

      {/* Top Processes Table Preview */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-sm text-white">Highest CPU Processes</h3>
            <p className="text-xs text-gray-400">Top executing processes by processor load</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-gray-800 text-gray-400 font-semibold uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-2.5 px-3">PID</th>
                <th className="py-2.5 px-3">Process Name</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">CPU %</th>
                <th className="py-2.5 px-3 text-right">Memory (RSS)</th>
                <th className="py-2.5 px-3 text-right">Threads</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60 font-mono text-gray-300">
              {topProcesses.map((proc) => (
                <tr key={proc.pid} className="hover:bg-gray-800/40 transition-colors">
                  <td className="py-2.5 px-3 font-semibold text-gray-400">{proc.pid}</td>
                  <td className="py-2.5 px-3 font-sans font-medium text-white">{proc.name}</td>
                  <td className="py-2.5 px-3">
                    <span className="inline-flex items-center rounded-md bg-gray-800 px-2 py-0.5 text-[10px] text-gray-300 capitalize font-sans">
                      {proc.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right text-cyan-400 font-semibold">
                    {proc.cpu_percent !== null && proc.cpu_percent !== undefined
                      ? `${proc.cpu_percent.toFixed(1)}%`
                      : '0.0%'}
                  </td>
                  <td className="py-2.5 px-3 text-right">{formatBytes(proc.memory_rss)}</td>
                  <td className="py-2.5 px-3 text-right text-gray-400">{proc.num_threads}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
