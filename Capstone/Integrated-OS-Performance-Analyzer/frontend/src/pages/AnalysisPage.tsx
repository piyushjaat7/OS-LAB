import React, { useEffect, useState, useCallback } from 'react';
import {
  Activity,
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  Cpu,
  Database,
  HardDrive,
  Network,
  RefreshCw,
  Clock,
  Lightbulb,
} from 'lucide-react';
import { api } from '../services/api';
import {
  BottleneckDetection,
  BottlenecksResponse,
  HealthStatus,
  ResourceState,
  SystemHealthAnalysis,
} from '../types/metrics';

function getHealthStatusColor(status: HealthStatus) {
  switch (status) {
    case 'EXCELLENT':
      return { text: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', ring: 'ring-emerald-500/20' };
    case 'GOOD':
      return { text: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30', ring: 'ring-blue-500/20' };
    case 'DEGRADED':
      return { text: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30', ring: 'ring-amber-500/20' };
    case 'CRITICAL':
      return { text: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/30', ring: 'ring-rose-500/20' };
    default:
      return { text: 'text-neutral-400', bg: 'bg-neutral-800', border: 'border-neutral-700', ring: 'ring-neutral-700' };
  }
}

function getResourceStateBadge(state: ResourceState) {
  switch (state) {
    case 'OPTIMAL':
      return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">OPTIMAL</span>;
    case 'NORMAL':
      return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">NORMAL</span>;
    case 'ELEVATED':
      return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">ELEVATED</span>;
    case 'WARNING':
      return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">WARNING</span>;
    case 'CRITICAL':
      return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse">CRITICAL</span>;
    default:
      return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-neutral-800 text-neutral-400 border border-neutral-700">UNKNOWN</span>;
  }
}

function getSeverityBadge(severity: string) {
  switch (severity) {
    case 'CRITICAL':
      return <span className="px-2.5 py-1 text-xs font-bold rounded bg-rose-500/20 text-rose-400 border border-rose-500/40">CRITICAL</span>;
    case 'HIGH':
      return <span className="px-2.5 py-1 text-xs font-bold rounded bg-orange-500/20 text-orange-400 border border-orange-500/40">HIGH</span>;
    case 'MEDIUM':
      return <span className="px-2.5 py-1 text-xs font-bold rounded bg-amber-500/20 text-amber-400 border border-amber-500/40">MEDIUM</span>;
    case 'LOW':
      return <span className="px-2.5 py-1 text-xs font-bold rounded bg-sky-500/20 text-sky-400 border border-sky-500/40">LOW</span>;
    default:
      return null;
  }
}

function getSubsystemIcon(type: string) {
  switch (type) {
    case 'CPU':
      return <Cpu className="w-5 h-5 text-indigo-400" />;
    case 'MEMORY':
      return <Database className="w-5 h-5 text-emerald-400" />;
    case 'DISK':
      return <HardDrive className="w-5 h-5 text-amber-400" />;
    case 'NETWORK':
      return <Network className="w-5 h-5 text-cyan-400" />;
    default:
      return <Activity className="w-5 h-5 text-neutral-400" />;
  }
}

export const AnalysisPage: React.FC = () => {
  const [health, setHealth] = useState<SystemHealthAnalysis | null>(null);
  const [bottlenecks, setBottlenecks] = useState<BottlenecksResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [healthData, bottlenecksData] = await Promise.all([
        api.getHealthAnalysis(),
        api.getBottlenecks(),
      ]);
      setHealth(healthData);
      setBottlenecks(bottlenecksData);
      setError(null);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch performance analysis data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    if (!autoRefresh) return;
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, [fetchData, autoRefresh]);

  if (loading && !health) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 text-sky-500 animate-spin" />
          <p className="text-neutral-400 text-sm">Evaluating system health & detecting bottlenecks...</p>
        </div>
      </div>
    );
  }

  const healthColors = health ? getHealthStatusColor(health.health_status) : getHealthStatusColor('EXCELLENT');

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-800">
        <div>
          <h1 className="text-2xl font-bold text-neutral-100 flex items-center gap-2">
            <Activity className="w-6 h-6 text-sky-400" />
            Performance Analysis & Bottlenecks
          </h1>
          <p className="text-sm text-neutral-400">
            Automated heuristic diagnosis, live subsystem classification, and historical saturation correlation.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
              autoRefresh
                ? 'bg-sky-500/10 border-sky-500/30 text-sky-400'
                : 'bg-neutral-800 border-neutral-700 text-neutral-400'
            }`}
          >
            {autoRefresh ? 'Auto-refresh: 4s' : 'Auto-refresh: Paused'}
          </button>
          <button
            onClick={fetchData}
            className="p-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 text-neutral-300 transition-colors"
            title="Refresh Analysis"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center gap-3">
          <AlertOctagon className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {health && (
        <>
          {/* Top Section: Health Score & Subsystems */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            {/* Health Score Gauge Card */}
            <div className={`p-6 rounded-xl border ${healthColors.border} ${healthColors.bg} flex flex-col items-center justify-center text-center relative overflow-hidden`}>
              <span className="text-xs uppercase tracking-wider font-semibold text-neutral-400 mb-2">
                System Health Score
              </span>
              <div className="relative flex items-center justify-center">
                <span className={`text-6xl font-black ${healthColors.text} tracking-tight font-mono`}>
                  {health.health_score}
                </span>
                <span className="text-lg font-bold text-neutral-500 ml-1">/100</span>
              </div>
              <div className="mt-3">
                <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide border ${healthColors.border} ${healthColors.text}`}>
                  {health.health_status}
                </span>
              </div>
              <p className="text-[11px] text-neutral-400 mt-3 max-w-[200px]">
                Calculated via real-time utilization penalties and pressure indicators.
              </p>
            </div>

            {/* Subsystem Classifications */}
            <div className="lg:col-span-3 grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* CPU */}
              <div className="p-4 rounded-xl bg-neutral-900 border border-neutral-800 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-neutral-200 flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-indigo-400" /> CPU Telemetry
                    </span>
                    {getResourceStateBadge(health.cpu_classification.status)}
                  </div>
                  <p className="text-xs text-neutral-400">{health.cpu_classification.details}</p>
                </div>
                {health.cpu_classification.utilization_percent !== null && (
                  <div className="mt-3">
                    <div className="flex justify-between text-xs font-mono text-neutral-400 mb-1">
                      <span>Overall Load</span>
                      <span className="text-neutral-200 font-semibold">{health.cpu_classification.utilization_percent}%</span>
                    </div>
                    <div className="w-full bg-neutral-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-indigo-500 h-1.5 rounded-full"
                        style={{ width: `${Math.min(100, health.cpu_classification.utilization_percent)}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Memory */}
              <div className="p-4 rounded-xl bg-neutral-900 border border-neutral-800 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-neutral-200 flex items-center gap-2">
                      <Database className="w-4 h-4 text-emerald-400" /> Memory & Swap
                    </span>
                    {getResourceStateBadge(health.memory_classification.status)}
                  </div>
                  <p className="text-xs text-neutral-400">{health.memory_classification.details}</p>
                </div>
                {health.memory_classification.utilization_percent !== null && (
                  <div className="mt-3">
                    <div className="flex justify-between text-xs font-mono text-neutral-400 mb-1">
                      <span>RAM Utilization</span>
                      <span className="text-neutral-200 font-semibold">{health.memory_classification.utilization_percent}%</span>
                    </div>
                    <div className="w-full bg-neutral-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-emerald-500 h-1.5 rounded-full"
                        style={{ width: `${Math.min(100, health.memory_classification.utilization_percent)}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Disk */}
              <div className="p-4 rounded-xl bg-neutral-900 border border-neutral-800 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-neutral-200 flex items-center gap-2">
                      <HardDrive className="w-4 h-4 text-amber-400" /> Storage Subsystem
                    </span>
                    {getResourceStateBadge(health.disk_classification.status)}
                  </div>
                  <p className="text-xs text-neutral-400">{health.disk_classification.details}</p>
                </div>
                {health.disk_classification.utilization_percent !== null && (
                  <div className="mt-3">
                    <div className="flex justify-between text-xs font-mono text-neutral-400 mb-1">
                      <span>Max Partition Full</span>
                      <span className="text-neutral-200 font-semibold">{health.disk_classification.utilization_percent}%</span>
                    </div>
                    <div className="w-full bg-neutral-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-amber-500 h-1.5 rounded-full"
                        style={{ width: `${Math.min(100, health.disk_classification.utilization_percent)}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Network */}
              <div className="p-4 rounded-xl bg-neutral-900 border border-neutral-800 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-neutral-200 flex items-center gap-2">
                      <Network className="w-4 h-4 text-cyan-400" /> Network Interfaces
                    </span>
                    {getResourceStateBadge(health.network_classification.status)}
                  </div>
                  <p className="text-xs text-neutral-400">{health.network_classification.details}</p>
                </div>
                <div className="mt-3 text-xs text-neutral-500 italic">
                  Interface drops & transmission error monitoring active.
                </div>
              </div>
            </div>
          </div>

          {/* Historical Pressure Correlation Banner */}
          {bottlenecks?.historical_summary && (
            <div className="p-4 rounded-xl bg-neutral-900 border border-neutral-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-purple-400 flex-shrink-0" />
                <div>
                  <h3 className="text-sm font-semibold text-neutral-200">
                    Historical Telemetry Correlation (MongoDB Persistence)
                  </h3>
                  <p className="text-xs text-neutral-400">
                    Analyzed {bottlenecks.historical_summary.samples_analyzed} recent snapshots.{' '}
                    {bottlenecks.historical_pressure_detected ? (
                      <span className="text-amber-400 font-medium">Sustained pressure trend confirmed across sampling window.</span>
                    ) : (
                      <span className="text-emerald-400 font-medium">No sustained historical pressure detected.</span>
                    )}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4 text-xs font-mono">
                <div>
                  <span className="text-neutral-500 block">Avg CPU</span>
                  <span className="text-neutral-200 font-semibold">{bottlenecks.historical_summary.avg_cpu_percent ?? 'N/A'}%</span>
                </div>
                <div>
                  <span className="text-neutral-500 block">Peak CPU</span>
                  <span className="text-neutral-200 font-semibold">{bottlenecks.historical_summary.peak_cpu_percent ?? 'N/A'}%</span>
                </div>
                <div>
                  <span className="text-neutral-500 block">Avg RAM</span>
                  <span className="text-neutral-200 font-semibold">{bottlenecks.historical_summary.avg_memory_percent ?? 'N/A'}%</span>
                </div>
                <div>
                  <span className="text-neutral-500 block">Peak RAM</span>
                  <span className="text-neutral-200 font-semibold">{bottlenecks.historical_summary.peak_memory_percent ?? 'N/A'}%</span>
                </div>
              </div>
            </div>
          )}

          {/* Active Bottlenecks Section */}
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-neutral-100 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" /> Active Bottlenecks & Saturation Analysis
            </h2>

            {health.active_bottlenecks.length === 0 ? (
              <div className="p-6 rounded-xl bg-emerald-950/20 border border-emerald-500/20 text-center space-y-2">
                <div className="inline-flex p-3 rounded-full bg-emerald-500/10 text-emerald-400 mb-1">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h3 className="text-base font-semibold text-emerald-300">All Subsystems Operating Normally</h3>
                <p className="text-xs text-neutral-400 max-w-lg mx-auto">
                  No resource constraints, memory thrashing, partition exhaustion, or network packet drop conditions currently detected.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {health.active_bottlenecks.map((bottleneck: BottleneckDetection, idx: number) => (
                  <div
                    key={`bn-${bottleneck.type}-${idx}`}
                    className="p-5 rounded-xl bg-neutral-900 border border-neutral-800 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getSubsystemIcon(bottleneck.type)}
                        <span className="text-sm font-bold text-neutral-200">
                          {bottleneck.type} Constraint
                        </span>
                      </div>
                      {getSeverityBadge(bottleneck.severity)}
                    </div>

                    <p className="text-xs text-neutral-300 leading-relaxed">
                      {bottleneck.explanation}
                    </p>

                    {/* Evidence summary */}
                    <div className="p-2.5 rounded bg-neutral-950/60 border border-neutral-800 text-xs font-mono space-y-1">
                      <span className="text-neutral-400 block font-sans font-semibold text-[11px]">Measured Evidence:</span>
                      {Object.entries(bottleneck.evidence).map(([k, v]) => {
                        if (typeof v === 'object' && v !== null) {
                          return null;
                        }
                        return (
                          <div key={k} className="flex justify-between text-neutral-300">
                            <span className="text-neutral-500">{k}:</span>
                            <span>{String(v)}</span>
                          </div>
                        );
                      })}
                    </div>

                    {/* Recommended Action */}
                    <div className="p-3 rounded-lg bg-sky-950/30 border border-sky-800/40 flex items-start gap-2.5">
                      <Lightbulb className="w-4 h-4 text-sky-400 flex-shrink-0 mt-0.5" />
                      <p className="text-xs text-sky-200">
                        <strong className="text-sky-300">Remediation:</strong> {bottleneck.recommended_action}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Alerts & Suggested Actions Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Warnings and Critical Alerts */}
            <div className="p-5 rounded-xl bg-neutral-900 border border-neutral-800 space-y-3">
              <h3 className="text-sm font-bold text-neutral-200 flex items-center gap-2">
                <AlertOctagon className="w-4 h-4 text-rose-400" /> Active Warnings & Critical Alerts
              </h3>
              {health.critical_alerts.length === 0 && health.warnings.length === 0 ? (
                <p className="text-xs text-neutral-500 italic">No alerts or warnings active.</p>
              ) : (
                <div className="space-y-2">
                  {health.critical_alerts.map((alert: string, idx: number) => (
                    <div
                      key={`crit-${idx}`}
                      className="p-2.5 rounded bg-rose-950/30 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2"
                    >
                      <AlertOctagon className="w-4 h-4 text-rose-400 flex-shrink-0" />
                      <span>{alert}</span>
                    </div>
                  ))}
                  {health.warnings.map((warn: string, idx: number) => (
                    <div
                      key={`warn-${idx}`}
                      className="p-2.5 rounded bg-amber-950/30 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2"
                    >
                      <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                      <span>{warn}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Suggested Actions */}
            <div className="p-5 rounded-xl bg-neutral-900 border border-neutral-800 space-y-3">
              <h3 className="text-sm font-bold text-neutral-200 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Recommended System Actions
              </h3>
              {health.suggested_actions.length === 0 ? (
                <p className="text-xs text-neutral-500 italic">No remediation steps currently required.</p>
              ) : (
                <ul className="space-y-2">
                  {health.suggested_actions.map((action: string, idx: number) => (
                    <li
                      key={`act-${idx}`}
                      className="text-xs text-neutral-300 flex items-start gap-2"
                    >
                      <span className="text-emerald-400 font-bold">•</span>
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
