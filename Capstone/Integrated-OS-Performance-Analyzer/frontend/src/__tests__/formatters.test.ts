import { describe, it, expect } from 'vitest';
import {
  formatBytes,
  formatThroughput,
  formatPercent,
  formatFrequency,
  getStatusColor,
} from '../utils/formatters';

describe('formatters', () => {
  it('formats bytes correctly', () => {
    expect(formatBytes(0)).toBe('0 B');
    expect(formatBytes(1024)).toBe('1 KB');
    expect(formatBytes(1048576)).toBe('1 MB');
    expect(formatBytes(1073741824)).toBe('1 GB');
    expect(formatBytes(null)).toBe('N/A');
    expect(formatBytes(undefined)).toBe('N/A');
  });

  it('formats throughput correctly', () => {
    expect(formatThroughput(0)).toBe('0 B/s');
    expect(formatThroughput(1024)).toBe('1 KB/s');
    expect(formatThroughput(null)).toBe('0.0 B/s');
  });

  it('formats percent correctly', () => {
    expect(formatPercent(45.67)).toBe('45.7%');
    expect(formatPercent(0)).toBe('0.0%');
    expect(formatPercent(null)).toBe('N/A');
  });

  it('formats frequency correctly', () => {
    expect(formatFrequency(800)).toBe('800 MHz');
    expect(formatFrequency(2400)).toBe('2.40 GHz');
    expect(formatFrequency(null)).toBe('N/A');
  });

  it('returns appropriate status color maps', () => {
    const normal = getStatusColor(50, 75, 90);
    expect(normal.text).toContain('emerald');

    const warning = getStatusColor(80, 75, 90);
    expect(warning.text).toContain('amber');

    const critical = getStatusColor(95, 75, 90);
    expect(critical.text).toContain('rose');
  });
});
