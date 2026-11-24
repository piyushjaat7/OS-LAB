import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from '../services/api';

describe('Performance Analysis and CPU Scheduling API Client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('fetches health analysis via getHealthAnalysis', async () => {
    const mockHealth = {
      health_score: 95,
      health_status: 'EXCELLENT',
      cpu_classification: { status: 'OPTIMAL', details: 'Normal' },
      warnings: [],
      critical_alerts: [],
      suggested_actions: [],
      active_bottlenecks: [],
      timestamp: '2026-11-13T07:00:00Z',
    };

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockHealth,
    });
    global.fetch = mockFetch;

    const res = await api.getHealthAnalysis();
    expect(res.health_score).toBe(95);
    expect(res.health_status).toBe('EXCELLENT');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/analysis/health'),
      expect.any(Object)
    );
  });

  it('fetches bottlenecks via getBottlenecks', async () => {
    const mockBottlenecks = {
      active_bottlenecks: [],
      historical_pressure_detected: false,
      historical_summary: null,
      timestamp: '2026-11-13T07:00:00Z',
    };

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockBottlenecks,
    });
    global.fetch = mockFetch;

    const res = await api.getBottlenecks();
    expect(res.active_bottlenecks).toEqual([]);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/analysis/bottlenecks'),
      expect.any(Object)
    );
  });

  it('posts FCFS scheduling workload', async () => {
    const mockSimulation = {
      algorithm: 'First-Come First-Served (FCFS)',
      mode: 'non-preemptive',
      processes: [],
      gantt_chart: [],
      total_simulation_time: 10,
      idle_time: 0,
      cpu_utilization_percent: 100,
      throughput: 0.2,
      avg_waiting_time: 2.5,
      avg_turnaround_time: 5.0,
      avg_response_time: 2.5,
    };

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockSimulation,
    });
    global.fetch = mockFetch;

    const processes = [{ process_id: 'P1', arrival_time: 0, burst_time: 4 }];
    const res = await api.simulateFCFS(processes);

    expect(res.algorithm).toContain('FCFS');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/analysis/scheduling/fcfs'),
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ processes }),
      })
    );
  });

  it('posts multi-algorithm comparison workload', async () => {
    const mockComparison = {
      workload_size: 2,
      algorithms: {},
      summary_table: [],
      workload_analysis: 'SJF minimizes waiting time.',
    };

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockComparison,
    });
    global.fetch = mockFetch;

    const processes = [
      { process_id: 'P1', arrival_time: 0, burst_time: 4 },
      { process_id: 'P2', arrival_time: 1, burst_time: 2 },
    ];
    const res = await api.compareScheduling(processes, 2.5, 'lower_is_higher');

    expect(res.workload_size).toBe(2);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/analysis/scheduling/compare'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ processes, time_quantum: 2.5, priority_order: 'lower_is_higher' }),
      })
    );
  });
});
