import React, { useState } from 'react';
import {
  BarChart3,
  Check,
  Cpu,
  Layers,
  Play,
  Plus,
  RefreshCw,
  RotateCcw,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { GanttChart } from '../components/charts/GanttChart';
import { api } from '../services/api';
import {
  ProcessWorkload,
  SchedulingComparison,
  SimulationResult,
} from '../types/metrics';

const PRESETS: Record<string, ProcessWorkload[]> = {
  'Standard Mixed': [
    { process_id: 'P1', arrival_time: 0, burst_time: 4, priority: 2 },
    { process_id: 'P2', arrival_time: 1, burst_time: 3, priority: 1 },
    { process_id: 'P3', arrival_time: 2, burst_time: 1, priority: 3 },
    { process_id: 'P4', arrival_time: 3, burst_time: 2, priority: 2 },
  ],
  'CPU Bound (Long Burst)': [
    { process_id: 'P1', arrival_time: 0, burst_time: 8, priority: 1 },
    { process_id: 'P2', arrival_time: 1, burst_time: 4, priority: 2 },
    { process_id: 'P3', arrival_time: 2, burst_time: 9, priority: 3 },
    { process_id: 'P4', arrival_time: 3, burst_time: 5, priority: 1 },
  ],
  'SJF Advantage': [
    { process_id: 'P1', arrival_time: 0, burst_time: 7, priority: 3 },
    { process_id: 'P2', arrival_time: 2, burst_time: 4, priority: 1 },
    { process_id: 'P3', arrival_time: 4, burst_time: 1, priority: 2 },
    { process_id: 'P4', arrival_time: 5, burst_time: 4, priority: 3 },
  ],
  'Simultaneous Arrivals': [
    { process_id: 'P1', arrival_time: 0, burst_time: 5, priority: 2 },
    { process_id: 'P2', arrival_time: 0, burst_time: 3, priority: 1 },
    { process_id: 'P3', arrival_time: 0, burst_time: 8, priority: 3 },
  ],
};

type AlgorithmKey = 'fcfs' | 'sjf' | 'srtf' | 'priority' | 'round-robin';

export const SchedulingPage: React.FC = () => {
  const [workload, setWorkload] = useState<ProcessWorkload[]>(PRESETS['Standard Mixed']);
  const [selectedAlgo, setSelectedAlgo] = useState<AlgorithmKey>('fcfs');
  const [timeQuantum, setTimeQuantum] = useState<number>(2.0);
  const [priorityPreemptive, setPriorityPreemptive] = useState<boolean>(false);
  const [priorityOrder, setPriorityOrder] = useState<string>('lower_is_higher');

  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [comparisonResult, setComparisonResult] = useState<SchedulingComparison | null>(null);
  const [activeTab, setActiveTab] = useState<'single' | 'compare'>('single');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Add process row
  const addProcess = () => {
    const nextNum = workload.length + 1;
    setWorkload([
      ...workload,
      {
        process_id: `P${nextNum}`,
        arrival_time: 0,
        burst_time: 2,
        priority: 1,
      },
    ]);
  };

  // Remove process row
  const removeProcess = (idx: number) => {
    if (workload.length <= 1) return;
    setWorkload(workload.filter((_, i) => i !== idx));
  };

  // Update process fields
  const updateProcess = (idx: number, field: keyof ProcessWorkload, value: any) => {
    const updated = [...workload];
    updated[idx] = { ...updated[idx], [field]: value };
    setWorkload(updated);
  };

  // Run single algorithm simulation
  const runSingleSimulation = async () => {
    setLoading(true);
    setError(null);
    setComparisonResult(null);
    setActiveTab('single');
    try {
      let res: SimulationResult;
      switch (selectedAlgo) {
        case 'fcfs':
          res = await api.simulateFCFS(workload);
          break;
        case 'sjf':
          res = await api.simulateSJF(workload);
          break;
        case 'srtf':
          res = await api.simulateSRTF(workload);
          break;
        case 'priority':
          res = await api.simulatePriority(workload, priorityPreemptive, priorityOrder);
          break;
        case 'round-robin':
          res = await api.simulateRoundRobin(workload, timeQuantum);
          break;
      }
      setSimulationResult(res);
    } catch (err: any) {
      setError(err?.message || 'Simulation execution failed');
    } finally {
      setLoading(false);
    }
  };

  // Run multi-algorithm comparison
  const runComparison = async () => {
    setLoading(true);
    setError(null);
    try {
      const comp = await api.compareScheduling(workload, timeQuantum, priorityOrder);
      setComparisonResult(comp);
      setActiveTab('compare');
    } catch (err: any) {
      setError(err?.message || 'Comparative benchmark execution failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-800">
        <div>
          <h1 className="text-2xl font-bold text-neutral-100 flex items-center gap-2">
            <Cpu className="w-6 h-6 text-indigo-400" />
            CPU Scheduling Simulator & Comparative Analysis
          </h1>
          <p className="text-sm text-neutral-400">
            Interactive multi-algorithm operating system scheduling simulation with interactive Gantt timeline visualization.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Main Grid: Workload Editor & Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Workload Editor (2 cols on lg) */}
        <div className="lg:col-span-2 p-5 rounded-xl bg-neutral-900 border border-neutral-800 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h2 className="text-base font-bold text-neutral-200 flex items-center gap-2">
              <Layers className="w-4 h-4 text-sky-400" /> Process Workload Editor
            </h2>

            {/* Presets */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-neutral-400">Presets:</span>
              <select
                onChange={(e) => {
                  if (PRESETS[e.target.value]) {
                    setWorkload(PRESETS[e.target.value]);
                  }
                }}
                className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-sky-500"
              >
                {Object.keys(PRESETS).map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Processes Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-neutral-950 text-neutral-400 font-semibold border-b border-neutral-800">
                <tr>
                  <th className="py-2.5 px-3">Process ID</th>
                  <th className="py-2.5 px-3">Arrival Time</th>
                  <th className="py-2.5 px-3">Burst Time</th>
                  <th className="py-2.5 px-3">Priority</th>
                  <th className="py-2.5 px-3 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-800/60 font-mono">
                {workload.map((p, idx) => (
                  <tr key={idx} className="hover:bg-neutral-800/30">
                    <td className="py-2 px-3">
                      <input
                        type="text"
                        value={p.process_id}
                        onChange={(e) => updateProcess(idx, 'process_id', e.target.value)}
                        className="w-20 bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-neutral-200 focus:outline-none focus:border-sky-500"
                      />
                    </td>
                    <td className="py-2 px-3">
                      <input
                        type="number"
                        min="0"
                        step="0.5"
                        value={p.arrival_time}
                        onChange={(e) => updateProcess(idx, 'arrival_time', parseFloat(e.target.value) || 0)}
                        className="w-20 bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-neutral-200 focus:outline-none focus:border-sky-500"
                      />
                    </td>
                    <td className="py-2 px-3">
                      <input
                        type="number"
                        min="0.5"
                        step="0.5"
                        value={p.burst_time}
                        onChange={(e) => updateProcess(idx, 'burst_time', parseFloat(e.target.value) || 1)}
                        className="w-20 bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-neutral-200 focus:outline-none focus:border-sky-500"
                      />
                    </td>
                    <td className="py-2 px-3">
                      <input
                        type="number"
                        min="1"
                        step="1"
                        value={p.priority ?? 1}
                        onChange={(e) => updateProcess(idx, 'priority', parseInt(e.target.value, 10) || 1)}
                        className="w-20 bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-neutral-200 focus:outline-none focus:border-sky-500"
                      />
                    </td>
                    <td className="py-2 px-3 text-center">
                      <button
                        onClick={() => removeProcess(idx)}
                        disabled={workload.length <= 1}
                        className="p-1 rounded text-neutral-500 hover:text-rose-400 disabled:opacity-30 disabled:cursor-not-allowed"
                        title="Remove Process"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-neutral-800">
            <button
              onClick={addProcess}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-200 text-xs font-medium border border-neutral-700 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" /> Add Process
            </button>
            <button
              onClick={() => setWorkload(PRESETS['Standard Mixed'])}
              className="inline-flex items-center gap-1 text-neutral-400 hover:text-neutral-200 text-xs"
            >
              <RotateCcw className="w-3 h-3" /> Reset Workload
            </button>
          </div>
        </div>

        {/* Algorithm Configuration & Execution Card */}
        <div className="p-5 rounded-xl bg-neutral-900 border border-neutral-800 space-y-5 flex flex-col justify-between">
          <div className="space-y-4">
            <h2 className="text-base font-bold text-neutral-200 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" /> Algorithm Settings
            </h2>

            {/* Algorithm Select */}
            <div className="space-y-1.5">
              <label className="text-xs text-neutral-400 font-medium">Scheduling Algorithm</label>
              <select
                value={selectedAlgo}
                onChange={(e) => setSelectedAlgo(e.target.value as AlgorithmKey)}
                className="w-full bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs rounded-lg p-2.5 focus:outline-none focus:border-sky-500"
              >
                <option value="fcfs">First-Come First-Served (FCFS)</option>
                <option value="sjf">Shortest Job First (SJF - Non-Preemptive)</option>
                <option value="srtf">Shortest Remaining Time First (SRTF - Preemptive)</option>
                <option value="priority">Priority Scheduling</option>
                <option value="round-robin">Round Robin (RR)</option>
              </select>
            </div>

            {/* Algorithm Specific Settings */}
            {selectedAlgo === 'round-robin' && (
              <div className="p-3 rounded-lg bg-neutral-950/70 border border-neutral-800 space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-neutral-300 font-medium">Time Quantum:</span>
                  <span className="font-mono text-sky-400 font-bold">{timeQuantum}s</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="10"
                  step="0.5"
                  value={timeQuantum}
                  onChange={(e) => setTimeQuantum(parseFloat(e.target.value))}
                  className="w-full accent-sky-500 h-1.5 bg-neutral-800 rounded-lg cursor-pointer"
                />
              </div>
            )}

            {selectedAlgo === 'priority' && (
              <div className="p-3 rounded-lg bg-neutral-950/70 border border-neutral-800 space-y-3">
                <label className="flex items-center gap-2 cursor-pointer text-xs text-neutral-300">
                  <input
                    type="checkbox"
                    checked={priorityPreemptive}
                    onChange={(e) => setPriorityPreemptive(e.target.checked)}
                    className="accent-indigo-500 rounded"
                  />
                  <span>Preemptive Priority Mode</span>
                </label>

                <div className="space-y-1 text-xs">
                  <span className="text-neutral-400">Priority Interpretation:</span>
                  <select
                    value={priorityOrder}
                    onChange={(e) => setPriorityOrder(e.target.value)}
                    className="w-full bg-neutral-800 border border-neutral-700 text-neutral-200 rounded p-1.5 text-xs"
                  >
                    <option value="lower_is_higher">Lower number = Higher priority (1 is highest)</option>
                    <option value="higher_is_higher">Higher number = Higher priority</option>
                  </select>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="space-y-2.5 pt-4 border-t border-neutral-800">
            <button
              onClick={runSingleSimulation}
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
            >
              {loading && activeTab === 'single' ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4 fill-current" />
              )}
              Run Single Simulation
            </button>

            <button
              onClick={runComparison}
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-200 border border-neutral-700 font-semibold text-xs flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              {loading && activeTab === 'compare' ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <BarChart3 className="w-4 h-4 text-purple-400" />
              )}
              Compare All Schedulers
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      {(simulationResult || comparisonResult) && (
        <div className="flex border-b border-neutral-800 gap-4">
          {simulationResult && (
            <button
              onClick={() => setActiveTab('single')}
              className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
                activeTab === 'single'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-neutral-400 hover:text-neutral-200'
              }`}
            >
              Simulation Results ({simulationResult.algorithm})
            </button>
          )}
          {comparisonResult && (
            <button
              onClick={() => setActiveTab('compare')}
              className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
                activeTab === 'compare'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-neutral-400 hover:text-neutral-200'
              }`}
            >
              Multi-Algorithm Comparison ({comparisonResult.workload_size} Processes)
            </button>
          )}
        </div>
      )}

      {/* Single Simulation View */}
      {activeTab === 'single' && simulationResult && (
        <div className="space-y-6">
          {/* High-Level Simulation Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3.5 rounded-xl bg-neutral-900 border border-neutral-800">
              <span className="text-[11px] text-neutral-400 block mb-1">Avg Waiting Time</span>
              <span className="text-xl font-bold font-mono text-emerald-400">
                {simulationResult.avg_waiting_time}s
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-neutral-900 border border-neutral-800">
              <span className="text-[11px] text-neutral-400 block mb-1">Avg Turnaround</span>
              <span className="text-xl font-bold font-mono text-blue-400">
                {simulationResult.avg_turnaround_time}s
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-neutral-900 border border-neutral-800">
              <span className="text-[11px] text-neutral-400 block mb-1">Avg Response</span>
              <span className="text-xl font-bold font-mono text-purple-400">
                {simulationResult.avg_response_time}s
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-neutral-900 border border-neutral-800">
              <span className="text-[11px] text-neutral-400 block mb-1">CPU Utilization</span>
              <span className="text-xl font-bold font-mono text-sky-400">
                {simulationResult.cpu_utilization_percent}%
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-neutral-900 border border-neutral-800">
              <span className="text-[11px] text-neutral-400 block mb-1">Throughput</span>
              <span className="text-xl font-bold font-mono text-amber-400">
                {simulationResult.throughput}/s
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-neutral-900 border border-neutral-800">
              <span className="text-[11px] text-neutral-400 block mb-1">Total Duration</span>
              <span className="text-xl font-bold font-mono text-neutral-200">
                {simulationResult.total_simulation_time}s
              </span>
            </div>
          </div>

          {/* Gantt Chart Section */}
          <div className="p-5 rounded-xl bg-neutral-900 border border-neutral-800 space-y-3">
            <h3 className="text-sm font-bold text-neutral-200">Execution Timeline (Gantt Chart)</h3>
            <GanttChart
              segments={simulationResult.gantt_chart}
              totalTime={simulationResult.total_simulation_time}
            />
          </div>

          {/* Process Completion Metrics Table */}
          <div className="p-5 rounded-xl bg-neutral-900 border border-neutral-800 space-y-3">
            <h3 className="text-sm font-bold text-neutral-200">Process Execution Breakdown</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-neutral-950 text-neutral-400 font-semibold border-b border-neutral-800">
                  <tr>
                    <th className="py-2.5 px-3">Process</th>
                    <th className="py-2.5 px-3">Arrival</th>
                    <th className="py-2.5 px-3">Burst</th>
                    <th className="py-2.5 px-3">Priority</th>
                    <th className="py-2.5 px-3">Completion (CT)</th>
                    <th className="py-2.5 px-3">Turnaround (TAT)</th>
                    <th className="py-2.5 px-3">Waiting (WT)</th>
                    <th className="py-2.5 px-3">Response (RT)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-800 font-mono">
                  {simulationResult.processes.map((p) => (
                    <tr key={p.process_id} className="hover:bg-neutral-800/30">
                      <td className="py-2.5 px-3 font-bold text-neutral-200">{p.process_id}</td>
                      <td className="py-2.5 px-3">{p.arrival_time}s</td>
                      <td className="py-2.5 px-3">{p.burst_time}s</td>
                      <td className="py-2.5 px-3">{p.priority}</td>
                      <td className="py-2.5 px-3 text-sky-400 font-semibold">{p.completion_time}s</td>
                      <td className="py-2.5 px-3 text-blue-400">{p.turnaround_time}s</td>
                      <td className="py-2.5 px-3 text-emerald-400">{p.waiting_time}s</td>
                      <td className="py-2.5 px-3 text-purple-400">{p.response_time}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Comparison View */}
      {activeTab === 'compare' && comparisonResult && (
        <div className="space-y-6">
          {/* Comparative Summary Table */}
          <div className="p-5 rounded-xl bg-neutral-900 border border-neutral-800 space-y-4">
            <h3 className="text-base font-bold text-neutral-200 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-purple-400" /> Multi-Algorithm Performance Benchmark
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-neutral-950 text-neutral-400 font-semibold border-b border-neutral-800">
                  <tr>
                    <th className="py-2.5 px-3">Algorithm</th>
                    <th className="py-2.5 px-3">Mode</th>
                    <th className="py-2.5 px-3">Avg Turnaround</th>
                    <th className="py-2.5 px-3">Avg Waiting</th>
                    <th className="py-2.5 px-3">Avg Response</th>
                    <th className="py-2.5 px-3">CPU Utilization</th>
                    <th className="py-2.5 px-3">Throughput</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-800 font-mono">
                  {comparisonResult.summary_table.map((row) => (
                    <tr key={`${row.algorithm}-${row.mode}`} className="hover:bg-neutral-800/30">
                      <td className="py-3 px-3 font-sans font-bold text-neutral-200">
                        {row.algorithm}
                      </td>
                      <td className="py-3 px-3 text-neutral-400 font-sans">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-neutral-800 border border-neutral-700">
                          {row.mode ?? 'standard'}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-semibold text-blue-400">{row.avg_turnaround_time}s</td>
                      <td className="py-3 px-3 font-semibold text-emerald-400">{row.avg_waiting_time}s</td>
                      <td className="py-3 px-3 font-semibold text-purple-400">{row.avg_response_time}s</td>
                      <td className="py-3 px-3 text-sky-400">{row.cpu_utilization_percent}%</td>
                      <td className="py-3 px-3 text-amber-400">{row.throughput}/s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Educational Workload Analysis Card */}
          <div className="p-5 rounded-xl bg-neutral-900 border border-neutral-800 space-y-3">
            <h3 className="text-sm font-bold text-neutral-200 flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-400" /> Algorithmic Workload Analysis & Trade-offs
            </h3>
            <p className="text-xs text-neutral-300 leading-relaxed bg-neutral-950/70 p-4 rounded-lg border border-neutral-800 font-sans">
              {comparisonResult.workload_analysis}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
