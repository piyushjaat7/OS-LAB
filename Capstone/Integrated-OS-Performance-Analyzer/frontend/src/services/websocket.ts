import { SystemMetrics } from '../types/metrics';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface WebSocketServiceOptions {
  interval?: number;
  onMessage: (data: SystemMetrics) => void;
  onStatusChange: (status: WebSocketStatus) => void;
  onError?: (error: Event) => void;
}

export class SystemWebSocket {
  private ws: WebSocket | null = null;
  private options: WebSocketServiceOptions;
  private reconnectTimeout: number | null = null;
  private reconnectAttempts = 0;
  private maxReconnectDelay = 10000;
  private baseReconnectDelay = 1000;
  private isExplicitlyClosed = false;

  constructor(options: WebSocketServiceOptions) {
    this.options = options;
  }

  public connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isExplicitlyClosed = false;
    this.options.onStatusChange('connecting');

    const baseHttp = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const wsProto = baseHttp.startsWith('https') ? 'wss' : 'ws';
    const host = baseHttp.replace(/^https?:\/\//, '');
    const interval = this.options.interval ?? 1.0;
    const url = `${wsProto}://${host}/api/v1/system/ws?interval=${interval}`;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.options.onStatusChange('connected');
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const parsed = JSON.parse(event.data);
          // Ignore server error frames or non-metric envelopes
          if (parsed && typeof parsed === 'object' && !parsed.error) {
            this.options.onMessage(parsed as SystemMetrics);
          }
        } catch {
          // Ignore non-json frames
        }
      };

      this.ws.onclose = () => {
        this.options.onStatusChange('disconnected');
        this.ws = null;
        if (!this.isExplicitlyClosed) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (err: Event) => {
        this.options.onStatusChange('error');
        if (this.options.onError) {
          this.options.onError(err);
        }
      };
    } catch {
      this.options.onStatusChange('error');
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimeout !== null || this.isExplicitlyClosed) return;

    this.reconnectAttempts++;
    const delay = Math.min(
      this.baseReconnectDelay * Math.pow(1.5, this.reconnectAttempts),
      this.maxReconnectDelay
    );

    this.reconnectTimeout = window.setTimeout(() => {
      this.reconnectTimeout = null;
      this.connect();
    }, delay);
  }

  public updateInterval(newInterval: number): void {
    if (this.options.interval === newInterval) return;
    this.options.interval = newInterval;
    // Reconnect with new query parameter
    if (this.ws) {
      this.disconnect();
      this.connect();
    }
  }

  public disconnect(): void {
    this.isExplicitlyClosed = true;
    if (this.reconnectTimeout !== null) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.options.onStatusChange('disconnected');
  }
}
