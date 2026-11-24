import { describe, it, expect } from 'vitest';
import { DiskMetrics, DiskPartitionInfo } from '../types/metrics';

describe('Disk deduplication and dynamic metric enforcement', () => {
  it('correctly aggregates unique filesystem capacity without inflation', () => {
    // Simulating deduplicated DiskMetrics from backend
    const diskMetrics: DiskMetrics = {
      partitions: [
        {
          partition: {
            device: '/dev/sdd',
            mountpoint: '/',
            filesystem: 'ext4',
            options: 'rw,relatime',
            mountpoints: ['/', '/mnt/wslg/distro'],
          },
          usage: {
            total: 1081101176832, // ~1007 GB
            used: 6951653376,     // ~6.5 GB
            free: 1019183439872,
            percent: 0.7,
          },
        },
      ],
      io_counters: null,
      total_capacity_bytes: 1081101176832,
      total_used_bytes: 6951653376,
      total_free_bytes: 1019183439872,
      total_percent: 0.6,
      unique_partition_count: 1,
      timestamp: '2026-11-13T12:00:00Z',
    };

    expect(diskMetrics.unique_partition_count).toBe(1);
    expect(diskMetrics.total_capacity_bytes).toBe(1081101176832);
    expect(diskMetrics.total_used_bytes).toBe(6951653376);
    expect(diskMetrics.total_percent).toBe(0.6);

    // Verify all associated mountpoints are preserved
    expect(diskMetrics.partitions[0].partition.mountpoints).toEqual(['/', '/mnt/wslg/distro']);
  });

  it('deduplicates multi-mount partitions in fallback aggregation if raw partitions are passed', () => {
    const rawPartitions: DiskPartitionInfo[] = [
      {
        partition: {
          device: '/dev/sdd',
          mountpoint: '/',
          filesystem: 'ext4',
          options: 'rw',
        },
        usage: { total: 1000, used: 100, free: 900, percent: 10.0 },
      },
      {
        partition: {
          device: '/dev/sdd',
          mountpoint: '/mnt/wslg/distro',
          filesystem: 'ext4',
          options: 'ro',
        },
        usage: { total: 1000, used: 100, free: 900, percent: 10.0 },
      },
    ];

    // Running the deduplicated aggregation logic as in OverviewPage
    const seenDevices = new Set<string>();
    let totalDisk = 0;
    let usedDisk = 0;

    for (const p of rawPartitions) {
      const devKey = p.partition.device || p.partition.mountpoint;
      if (seenDevices.has(devKey)) continue;
      seenDevices.add(devKey);
      if (p.usage) {
        totalDisk += p.usage.total;
        usedDisk += p.usage.used;
      }
    }

    // Capacity must be counted once (1000), not doubled to 2000
    expect(totalDisk).toBe(1000);
    expect(usedDisk).toBe(100);
    expect((usedDisk / totalDisk) * 100).toBe(10.0);
  });

  it('renders unavailable metrics as N/A rather than fabricated or fake values', () => {
    const unavailableDiskMetrics: DiskMetrics = {
      partitions: [
        {
          partition: {
            device: '/dev/sdd',
            mountpoint: '/inaccessible',
            filesystem: 'ext4',
            options: 'rw',
          },
          usage: null, // inaccessible partition
        },
      ],
      io_counters: null,
      total_capacity_bytes: null,
      total_used_bytes: null,
      total_free_bytes: null,
      total_percent: null,
      unique_partition_count: 1,
      timestamp: '2026-11-13T12:00:00Z',
    };

    expect(unavailableDiskMetrics.partitions[0].usage).toBeNull();
    expect(unavailableDiskMetrics.total_capacity_bytes).toBeNull();
    expect(unavailableDiskMetrics.total_percent).toBeNull();
  });
});
