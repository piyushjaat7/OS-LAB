export function formatBytes(bytes: number | null | undefined, decimals = 1): string {
  if (bytes === null || bytes === undefined || isNaN(bytes)) return 'N/A';
  if (bytes === 0) return '0 B';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(k));
  const safeI = Math.min(i, sizes.length - 1);

  return `${parseFloat((bytes / Math.pow(k, safeI)).toFixed(dm))} ${sizes[safeI]}`;
}

export function formatThroughput(bytesPerSec: number | null | undefined, decimals = 1): string {
  if (bytesPerSec === null || bytesPerSec === undefined || isNaN(bytesPerSec)) return '0.0 B/s';
  return `${formatBytes(bytesPerSec, decimals)}/s`;
}

export function formatPercent(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined || isNaN(value)) return 'N/A';
  return `${value.toFixed(decimals)}%`;
}

export function formatFrequency(mhz: number | null | undefined): string {
  if (mhz === null || mhz === undefined || isNaN(mhz)) return 'N/A';
  if (mhz >= 1000) {
    return `${(mhz / 1000).toFixed(2)} GHz`;
  }
  return `${Math.round(mhz)} MHz`;
}

export function formatTime(isoString: string | null | undefined): string {
  if (!isoString) return '--:--:--';
  try {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return '--:--:--';
  }
}

export function formatDateTime(isoString: string | null | undefined): string {
  if (!isoString) return 'N/A';
  try {
    const d = new Date(isoString);
    return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour12: false })}`;
  } catch {
    return 'N/A';
  }
}

export function getStatusColor(
  value: number | null | undefined,
  warning = 75,
  critical = 90
): { text: string; bg: string; border: string; bar: string } {
  if (value === null || value === undefined) {
    return {
      text: 'text-gray-400',
      bg: 'bg-gray-800/40',
      border: 'border-gray-700/50',
      bar: 'bg-gray-500',
    };
  }
  if (value >= critical) {
    return {
      text: 'text-rose-400',
      bg: 'bg-rose-950/30',
      border: 'border-rose-800/40',
      bar: 'bg-rose-500',
    };
  }
  if (value >= warning) {
    return {
      text: 'text-amber-400',
      bg: 'bg-amber-950/30',
      border: 'border-amber-800/40',
      bar: 'bg-amber-500',
    };
  }
  return {
    text: 'text-emerald-400',
    bg: 'bg-emerald-950/30',
    border: 'border-emerald-800/40',
    bar: 'bg-emerald-500',
  };
}
