import React, { useEffect, useState } from 'react';
import { HardDrive, ArrowDownToLine, ArrowUpFromLine, Layers } from 'lucide-react';
import { useMetrics } from '../context/MetricsContext';
import { MetricCard } from '../components/common/MetricCard';
import { PartitionUsageCard } from '../components/charts/PartitionUsageCard';
import { LiveAreaChart } from '../components/charts/LiveAreaChart';
import { api } from '../services/api';
import { HistoricalSystemMetrics } from '../types/metrics';
import { formatBytes, formatTime } from '../utils/formatters';

export const DiskPage: React.FC = () => {
  const { metrics, settings } = useMetrics();
  const [historyData, setHistoryData] = useState<any[]>([]);

  const disk = metrics?.disk;
  const partitions = disk?.partitions ?? [];
  const io = disk?.io_counters;

  let calcCapacity = 0;
  let calcUsed = 0;
  let calcFree = 0;
  for (const p of partitions) {
    if (p.usage) {
      calcCapacity += p.usage.total;
      calcUsed += p.usage.used;
      calcFree += p.usage.free;
    }
  }
  const calcPercent = calcCapacity > 0 ? (calcUsed / calcCapacity) * 100 : null;

  const totalCapacity = disk?.total_capacity_bytes ?? calcCapacity;
  const totalUsed = disk?.total_used_bytes ?? calcUsed;
  const totalFree = disk?.total_free_bytes ?? calcFree;
  const aggregatePercent = disk?.total_percent ?? calcPercent;
  const uniqueCount = disk?.unique_partition_count ?? partitions.length;

  useEffect(() => {
    let mounted = true;
    const loadDiskHistory = async () => {
      try {
        const docs = await api.getHistory({ limit: 40, order: 'desc' });
        if (mounted) {
          const formatted = docs.reverse().map((d: HistoricalSystemMetrics) => ({
            timeStr: formatTime(d.timestamp),
            usedBytesGB: d.disk?.used_bytes ? +(d.disk.used_bytes / (1024 * 1024 * 1024)).toFixed(2) : null,
          }));
          setHistoryData(formatted);
        }
      } catch {
        // Fallback
      }
    };

    loadDiskHistory();
    const timer = setInterval(loadDiskHistory, 20000);
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
          title="Aggregate Disk Used"
          value={formatBytes(totalUsed)}
          subtitle={`${formatBytes(totalFree)} remaining`}
          icon={HardDrive}
          percentage={aggregatePercent}
          warningThreshold={settings.diskWarning}
          criticalThreshold={settings.diskCritical}
          colorTheme="indigo"
        />

        <MetricCard
          title="Total Storage Capacity"
          value={formatBytes(totalCapacity)}
          subtitle={`${uniqueCount} unique ${uniqueCount === 1 ? 'filesystem' : 'filesystems'}`}
          icon={Layers}
          colorTheme="cyan"
        />

        <MetricCard
          title="Cumulative Reads"
          value={formatBytes(io?.read_bytes)}
          subtitle={`${io?.read_count?.toLocaleString() ?? 0} read operations`}
          icon={ArrowDownToLine}
          colorTheme="emerald"
        />

        <MetricCard
          title="Cumulative Writes"
          value={formatBytes(io?.write_bytes)}
          subtitle={`${io?.write_count?.toLocaleString() ?? 0} write operations`}
          icon={ArrowUpFromLine}
          colorTheme="amber"
        />
      </div>

      {/* Discovered Partitions Grid */}
      <div>
        <h3 className="font-semibold text-sm text-white mb-3">Mounted Partition Storage</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {partitions.map((p, idx) => (
            <PartitionUsageCard key={idx} partitionInfo={p} />
          ))}
        </div>
      </div>

      {/* Historical Storage Capacity Graph */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-sm text-white">Historical Storage Utilization (GB)</h3>
            <p className="text-xs text-gray-400">Total disk space consumed over persisted historical window</p>
          </div>
        </div>
        <LiveAreaChart
          data={historyData}
          series={[{ key: 'usedBytesGB', name: 'Used Storage (GB)', color: '#6366f1' }]}
          yDomain={['auto', 'auto']}
          valueFormatter={(val) => `${val} GB`}
        />
      </div>
    </div>
  );
};
