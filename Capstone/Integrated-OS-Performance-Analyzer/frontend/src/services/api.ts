import {
  BottlenecksResponse,
  CPUMetrics,
  DiskMetrics,
  HealthResponse,
  HistoricalMetricsSummary,
  HistoricalSystemMetrics,
  MemoryMetrics,
  NetworkMetrics,
  ProcessCollectionMetrics,
  ProcessMetrics,
  ProcessWorkload,
  SchedulingComparison,
  SimulationResult,
  SystemHealthAnalysis,
  SystemMetrics,
} from '../types/metrics';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      Accept: 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status} ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        if (typeof errorJson.detail === 'string') {
          errorDetail = errorJson.detail;
        } else if (Array.isArray(errorJson.detail)) {
          errorDetail = errorJson.detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join('; ');
        } else {
          errorDetail = JSON.stringify(errorJson.detail);
        }
      }
    } catch {
      // Non-JSON response
    }
    throw new Error(errorDetail);
  }

  return response.json() as Promise<T>;
}

export const api = {
  getHealth: () => fetchJson<HealthResponse>('/health'),

  getSystemMetrics: () => fetchJson<SystemMetrics>('/api/v1/system/metrics'),

  getCPU: () => fetchJson<CPUMetrics>('/api/v1/system/cpu'),

  getMemory: () => fetchJson<MemoryMetrics>('/api/v1/system/memory'),

  getDisk: () => fetchJson<DiskMetrics>('/api/v1/system/disk'),

  getNetwork: () => fetchJson<NetworkMetrics>('/api/v1/system/network'),

  getProcesses: () => fetchJson<ProcessCollectionMetrics>('/api/v1/system/processes'),

  getProcessByPid: (pid: number) => fetchJson<ProcessMetrics>(`/api/v1/system/processes/${pid}`),

  getHistory: (params?: {
    start_time?: string;
    end_time?: string;
    limit?: number;
    order?: 'asc' | 'desc';
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.start_time) searchParams.append('start_time', params.start_time);
    if (params?.end_time) searchParams.append('end_time', params.end_time);
    if (params?.limit) searchParams.append('limit', String(params.limit));
    if (params?.order) searchParams.append('order', params.order);
    const queryString = searchParams.toString();
    return fetchJson<HistoricalSystemMetrics[]>(`/api/v1/system/history${queryString ? `?${queryString}` : ''}`);
  },

  getHistorySummary: (params?: { start_time?: string; end_time?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.start_time) searchParams.append('start_time', params.start_time);
    if (params?.end_time) searchParams.append('end_time', params.end_time);
    const queryString = searchParams.toString();
    return fetchJson<HistoricalMetricsSummary>(`/api/v1/system/history/summary${queryString ? `?${queryString}` : ''}`);
  },

  // Analysis endpoints
  getHealthAnalysis: () => fetchJson<SystemHealthAnalysis>('/api/v1/analysis/health'),

  getBottlenecks: () => fetchJson<BottlenecksResponse>('/api/v1/analysis/bottlenecks'),

  // Scheduling endpoints
  simulateFCFS: (processes: ProcessWorkload[]) =>
    fetchJson<SimulationResult>('/api/v1/analysis/scheduling/fcfs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ processes }),
    }),

  simulateSJF: (processes: ProcessWorkload[]) =>
    fetchJson<SimulationResult>('/api/v1/analysis/scheduling/sjf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ processes }),
    }),

  simulateSRTF: (processes: ProcessWorkload[]) =>
    fetchJson<SimulationResult>('/api/v1/analysis/scheduling/srtf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ processes }),
    }),

  simulatePriority: (processes: ProcessWorkload[], preemptive = false, priorityOrder = 'lower_is_higher') =>
    fetchJson<SimulationResult>('/api/v1/analysis/scheduling/priority', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ processes, preemptive, priority_order: priorityOrder }),
    }),

  simulateRoundRobin: (processes: ProcessWorkload[], timeQuantum = 2.0) =>
    fetchJson<SimulationResult>('/api/v1/analysis/scheduling/round-robin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ processes, time_quantum: timeQuantum }),
    }),

  compareScheduling: (processes: ProcessWorkload[], timeQuantum = 2.0, priorityOrder = 'lower_is_higher') =>
    fetchJson<SchedulingComparison>('/api/v1/analysis/scheduling/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ processes, time_quantum: timeQuantum, priority_order: priorityOrder }),
    }),
};
