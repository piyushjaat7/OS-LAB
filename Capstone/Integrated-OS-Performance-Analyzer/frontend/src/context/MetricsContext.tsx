import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import { api } from '../services/api';
import { SystemWebSocket, WebSocketStatus } from '../services/websocket';
import { SystemMetrics, ThresholdSettings } from '../types/metrics';
import { formatTime } from '../utils/formatters';

export interface ChartPoint {
  timestamp: string;
  timeStr: string;
  cpuPercent: number | null;
  memoryPercent: number | null;
  netSentThroughput: number | null;
  netRecvThroughput: number | null;
}

const DEFAULT_SETTINGS: ThresholdSettings = {
  cpuWarning: 75,
  cpuCritical: 90,
  memoryWarning: 80,
  memoryCritical: 95,
  diskWarning: 80,
  diskCritical: 90,
  chartHistoryLength: 30,
  streamInterval: 1.0,
};

interface MetricsContextType {
  metrics: SystemMetrics | null;
  chartHistory: ChartPoint[];
  wsStatus: WebSocketStatus;
  restStatus: 'healthy' | 'unhealthy' | 'checking';
  lastUpdated: string | null;
  settings: ThresholdSettings;
  updateSettings: (newSettings: Partial<ThresholdSettings>) => void;
  refresh: () => Promise<void>;
  isLoading: boolean;
}

const MetricsContext = createContext<MetricsContextType | null>(null);

export const MetricsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [chartHistory, setChartHistory] = useState<ChartPoint[]>([]);
  const [wsStatus, setWsStatus] = useState<WebSocketStatus>('disconnected');
  const [restStatus, setRestStatus] = useState<'healthy' | 'unhealthy' | 'checking'>('checking');
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Settings from localStorage
  const [settings, setSettings] = useState<ThresholdSettings>(() => {
    try {
      const stored = localStorage.getItem('app_threshold_settings');
      if (stored) {
        return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
      }
    } catch {
      // Fallback
    }
    return DEFAULT_SETTINGS;
  });

  const wsRef = useRef<SystemWebSocket | null>(null);
  const maxHistoryRef = useRef(settings.chartHistoryLength);
  maxHistoryRef.current = settings.chartHistoryLength;

  const appendChartPoint = useCallback((newMetrics: SystemMetrics) => {
    const point: ChartPoint = {
      timestamp: newMetrics.timestamp,
      timeStr: formatTime(newMetrics.timestamp),
      cpuPercent: newMetrics.cpu?.usage_percent ?? null,
      memoryPercent: newMetrics.memory?.virtual?.percent ?? null,
      netSentThroughput: newMetrics.network?.throughput?.bytes_sent_per_sec ?? null,
      netRecvThroughput: newMetrics.network?.throughput?.bytes_recv_per_sec ?? null,
    };

    setChartHistory((prev) => {
      const updated = [...prev, point];
      if (updated.length > maxHistoryRef.current) {
        return updated.slice(updated.length - maxHistoryRef.current);
      }
      return updated;
    });
  }, []);

  const handleMetricUpdate = useCallback((newMetrics: SystemMetrics) => {
    setMetrics(newMetrics);
    setLastUpdated(newMetrics.timestamp);
    appendChartPoint(newMetrics);
    setIsLoading(false);
  }, [appendChartPoint]);

  // Initial REST fetch & health check
  const refresh = useCallback(async () => {
    try {
      const [healthRes, metricsRes] = await Promise.allSettled([
        api.getHealth(),
        api.getSystemMetrics(),
      ]);

      if (healthRes.status === 'fulfilled' && healthRes.value.status === 'healthy') {
        setRestStatus('healthy');
      } else {
        setRestStatus('unhealthy');
      }

      if (metricsRes.status === 'fulfilled') {
        handleMetricUpdate(metricsRes.value);
      }
    } catch {
      setRestStatus('unhealthy');
    }
  }, [handleMetricUpdate]);

  // WebSocket lifecycle
  useEffect(() => {
    refresh();

    const wsService = new SystemWebSocket({
      interval: settings.streamInterval,
      onMessage: (data) => {
        handleMetricUpdate(data);
      },
      onStatusChange: (status) => {
        setWsStatus(status);
        if (status === 'connected') {
          setRestStatus('healthy');
        }
      },
    });

    wsRef.current = wsService;
    wsService.connect();

    return () => {
      wsService.disconnect();
      wsRef.current = null;
    };
  }, [settings.streamInterval, refresh, handleMetricUpdate]);

  const updateSettings = useCallback((newValues: Partial<ThresholdSettings>) => {
    setSettings((prev) => {
      const updated = { ...prev, ...newValues };
      try {
        localStorage.setItem('app_threshold_settings', JSON.stringify(updated));
      } catch {
        // Storage unavailable
      }
      return updated;
    });

    if (newValues.streamInterval && wsRef.current) {
      wsRef.current.updateInterval(newValues.streamInterval);
    }
  }, []);

  return (
    <MetricsContext.Provider
      value={{
        metrics,
        chartHistory,
        wsStatus,
        restStatus,
        lastUpdated,
        settings,
        updateSettings,
        refresh,
        isLoading,
      }}
    >
      {children}
    </MetricsContext.Provider>
  );
};

export const useMetrics = (): MetricsContextType => {
  const context = useContext(MetricsContext);
  if (!context) {
    throw new Error('useMetrics must be used within a MetricsProvider');
  }
  return context;
};
