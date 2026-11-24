import React, { useEffect, useState } from 'react';
import { Network, ArrowDownRight, ArrowUpRight, Activity, Radio } from 'lucide-react';
import { useMetrics } from '../context/MetricsContext';
import { MetricCard } from '../components/common/MetricCard';
import { LiveAreaChart } from '../components/charts/LiveAreaChart';
import { api } from '../services/api';
import { HistoricalSystemMetrics } from '../types/metrics';
import { formatBytes, formatThroughput, formatTime } from '../utils/formatters';

export const NetworkPage: React.FC = () => {
  const { metrics, chartHistory } = useMetrics();
  const [historyData, setHistoryData] = useState<any[]>([]);

  const net = metrics?.network;
  const interfaces = net?.interfaces ?? [];
  const io = net?.io_counters;
  const tp = net?.throughput;

  useEffect(() => {
    let mounted = true;
    const loadNetHistory = async () => {
      try {
        const docs = await api.getHistory({ limit: 40, order: 'desc' });
        if (mounted) {
          const formatted = docs.reverse().map((d: HistoricalSystemMetrics) => ({
            timeStr: formatTime(d.timestamp),
            netSentThroughput: d.network?.throughput_sent_bytes_per_sec ?? null,
            netRecvThroughput: d.network?.throughput_recv_bytes_per_sec ?? null,
          }));
          setHistoryData(formatted);
        }
      } catch {
        // Fallback
      }
    };

    loadNetHistory();
    const timer = setInterval(loadNetHistory, 15000);
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
          title="Download Throughput"
          value={formatThroughput(tp?.bytes_recv_per_sec)}
          subtitle={`Total received: ${formatBytes(io?.bytes_recv)}`}
          icon={ArrowDownRight}
          colorTheme="emerald"
        />

        <MetricCard
          title="Upload Throughput"
          value={formatThroughput(tp?.bytes_sent_per_sec)}
          subtitle={`Total transmitted: ${formatBytes(io?.bytes_sent)}`}
          icon={ArrowUpRight}
          colorTheme="amber"
        />

        <MetricCard
          title="Packets Transferred"
          value={(io?.packets_recv ?? 0).toLocaleString()}
          unit="rx"
          subtitle={`${(io?.packets_sent ?? 0).toLocaleString()} packets tx`}
          icon={Activity}
          colorTheme="cyan"
        />

        <MetricCard
          title="Interfaces Active"
          value={interfaces.filter((i) => i.is_up).length}
          unit={`/ ${interfaces.length}`}
          subtitle={`${(io?.errin ?? 0) + (io?.errout ?? 0)} transmission errors`}
          icon={Radio}
          colorTheme="purple"
        />
      </div>

      {/* Network Interfaces List */}
      <div>
        <h3 className="font-semibold text-sm text-white mb-3">Detected Network Interfaces</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {interfaces.map((nic) => (
            <div
              key={nic.name}
              className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md transition-all hover:border-gray-700 shadow-md flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`p-2 rounded-lg border ${
                        nic.is_up
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : 'bg-gray-800 text-gray-500 border-gray-700'
                      }`}
                    >
                      <Network className="h-4 w-4" />
                    </div>
                    <span className="font-mono font-bold text-sm text-white">{nic.name}</span>
                  </div>
                  <span
                    className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                      nic.is_up
                        ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/40'
                        : 'bg-gray-800 text-gray-400 border-gray-700'
                    }`}
                  >
                    <span className={`h-1.5 w-1.5 rounded-full ${nic.is_up ? 'bg-emerald-400' : 'bg-gray-500'}`} />
                    {nic.is_up ? 'UP' : 'DOWN'}
                  </span>
                </div>

                {/* Subnet / MAC addresses */}
                {nic.addresses && nic.addresses.length > 0 && (
                  <div className="mt-2 text-[11px] text-gray-400 font-mono space-y-0.5">
                    {nic.addresses.map((addr, idx) => (
                      <div key={idx} className="truncate">
                        • {addr}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-gray-800 grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-[10px] text-gray-500 font-semibold uppercase">Speed / MTU</span>
                  <p className="font-mono text-gray-300 mt-0.5">
                    {nic.speed ? `${nic.speed} Mbps` : 'N/A'} • MTU {nic.mtu ?? '-'}
                  </p>
                </div>
                <div>
                  <span className="text-[10px] text-gray-500 font-semibold uppercase">Instant Rate</span>
                  <p className="font-mono text-gray-300 mt-0.5">
                    ↓ {formatThroughput(nic.throughput?.bytes_recv_per_sec)}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Real-time vs Historical Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-sm text-white">Live Network Throughput</h3>
              <p className="text-xs text-gray-400">WebSocket live streaming upload and download rates</p>
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

        <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-sm text-white">Historical Network Activity</h3>
              <p className="text-xs text-gray-400">Persisted historical throughput records from MongoDB</p>
            </div>
          </div>
          <LiveAreaChart
            data={historyData}
            series={[
              { key: 'netRecvThroughput', name: 'Historical Download', color: '#34d399' },
              { key: 'netSentThroughput', name: 'Historical Upload', color: '#fbbf24' },
            ]}
            yDomain={['auto', 'auto']}
            valueFormatter={(val) => formatThroughput(val)}
          />
        </div>
      </div>
    </div>
  );
};
