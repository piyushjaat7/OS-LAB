import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from '../services/api';

describe('api client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('calls getHealth on /health', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'healthy', database: 'connected' }),
    });
    global.fetch = mockFetch;

    const res = await api.getHealth();
    expect(res.status).toBe('healthy');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/health'),
      expect.any(Object)
    );
  });

  it('calls getSystemMetrics on /api/v1/system/metrics', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ timestamp: '2026-11-13T06:00:00Z', cpu: null }),
    });
    global.fetch = mockFetch;

    const res = await api.getSystemMetrics();
    expect(res.timestamp).toBe('2026-11-13T06:00:00Z');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/system/metrics'),
      expect.any(Object)
    );
  });

  it('formats query string properly for getHistory', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    });
    global.fetch = mockFetch;

    await api.getHistory({
      start_time: '2026-11-13T05:00:00Z',
      end_time: '2026-11-13T06:00:00Z',
      limit: 50,
      order: 'asc',
    });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringMatching(
        /\/api\/v1\/system\/history\?start_time=.*&end_time=.*&limit=50&order=asc/
      ),
      expect.any(Object)
    );
  });

  it('handles HTTP error responses with details', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ detail: 'Process not found' }),
    });
    global.fetch = mockFetch;

    await expect(api.getProcessByPid(99999)).rejects.toThrow('Process not found');
  });
});
