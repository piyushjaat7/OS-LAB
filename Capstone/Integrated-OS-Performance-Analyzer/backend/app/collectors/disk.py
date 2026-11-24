import os
from datetime import UTC, datetime
from typing import Any

import psutil

from app.schemas.metrics import (
    DiskIOCountersMetrics,
    DiskMetrics,
    DiskPartitionInfo,
    DiskPartitionMetrics,
    DiskUsageMetrics,
)

# Set of pseudo, virtual, or in-memory filesystem types to filter out
# on Linux/Unix systems if psutil's all=False does not exclude them.
PSEUDO_FS_TYPES = {
    "autofs",
    "binfmt_misc",
    "bpf",
    "cgroup",
    "cgroup2",
    "configfs",
    "debugfs",
    "devpts",
    "devtmpfs",
    "fusectl",
    "hugetlbfs",
    "mqueue",
    "overlay",
    "proc",
    "pstore",
    "ramfs",
    "securityfs",
    "sysfs",
    "tmpfs",
    "tracefs",
}


def _is_real_device(device: str) -> bool:
    """Check if a device string represents an identifiable hardware/block device."""
    if not device:
        return False
    dev_lower = device.lower().strip()
    return dev_lower not in ("none", "tmpfs", "rootfs", "overlay", "udev", "devtmpfs")


def _mountpoint_priority(mountpoint: str, opts: str | None) -> int:
    """Rank canonical significance of a mountpoint when grouping duplicate mounts."""
    score = 0
    if mountpoint == "/":
        score += 2000
    elif mountpoint.startswith(("/home", "/var", "/usr", "/opt", "/data", "/etc")):
        score += 500
    elif not mountpoint.startswith(("/mnt/wsl", "/mnt/wslg", "/run", "/var/lib")):
        score += 100

    if opts and "rw" in opts.split(","):
        score += 50

    score -= len(mountpoint)
    return score


class DiskCollector:
    """Cross-platform collector for storage partitions, disk usage, and I/O counters using psutil."""

    def __init__(self) -> None:
        self.initialized_at: datetime = datetime.now(UTC)
        self.last_sampled_at: datetime | None = None
        self._sample_count: int = 0

    def _collect_partitions(self) -> list[DiskPartitionMetrics]:
        """Internal helper to discover, deduplicate, and filter mounted physical partitions.

        Filtering Strategy:
        1. Query physical partitions via psutil.disk_partitions(all=False).
        2. Filter known in-memory/pseudo filesystems via PSEUDO_FS_TYPES.
        3. Filesystem Deduplication: In virtualized, containerized, or WSL2 environments,
           the exact same physical device (e.g. /dev/sdd) may be mounted concurrently at
           multiple mountpoints (e.g. '/' and '/mnt/wslg/distro'). We group partition entries
           sharing the same underlying physical device or kernel filesystem device ID (st_dev).
        4. Canonical Mountpoint Selection: The most canonical mountpoint (e.g. root '/' or primary
           path) is selected as the primary mountpoint, while all associated mountpoints are preserved
           in the `mountpoints` list to avoid losing visibility.
        """
        try:
            raw_partitions = psutil.disk_partitions(all=False)
        except (psutil.Error, OSError, PermissionError):
            return []

        if not raw_partitions:
            return []

        fs_groups: list[dict[str, Any]] = []

        for part in raw_partitions:
            mountpoint = getattr(part, "mountpoint", None)
            if not mountpoint:
                continue

            fstype = getattr(part, "fstype", "") or ""
            if fstype.lower() in PSEUDO_FS_TYPES:
                continue

            device = str(getattr(part, "device", "") or "").strip()

            st_dev = None
            try:
                st = os.stat(mountpoint)
                st_dev = st.st_dev
            except (OSError, PermissionError, ValueError):
                st_dev = None

            # Match against existing filesystem groups
            matched_group = None
            for group in fs_groups:
                group_has_real_dev = _is_real_device(group["device"])
                part_has_real_dev = _is_real_device(device)

                if group_has_real_dev and part_has_real_dev:
                    # Both report real block devices: they match if and only if device names match
                    if group["device"] == device:
                        matched_group = group
                        break
                elif st_dev is not None and group["st_dev"] is not None:
                    # At least one device is generic/unspecified: match by kernel filesystem device ID
                    if group["st_dev"] == st_dev:
                        matched_group = group
                        break
                elif (
                    not group_has_real_dev
                    and not part_has_real_dev
                    and getattr(group["partitions"][0], "mountpoint", None)
                    == mountpoint
                ):
                    matched_group = group
                    break

            if matched_group is not None:
                matched_group["partitions"].append(part)
                if matched_group["st_dev"] is None and st_dev is not None:
                    matched_group["st_dev"] = st_dev
                if not _is_real_device(matched_group["device"]) and _is_real_device(
                    device
                ):
                    matched_group["device"] = device
            else:
                fs_groups.append(
                    {
                        "device": device,
                        "st_dev": st_dev,
                        "partitions": [part],
                    }
                )

        partitions: list[DiskPartitionMetrics] = []

        for group in fs_groups:
            parts = group["partitions"]
            parts.sort(
                key=lambda p: _mountpoint_priority(
                    getattr(p, "mountpoint", ""),
                    getattr(p, "opts", None),
                ),
                reverse=True,
            )
            primary = parts[0]
            primary_mount = str(getattr(primary, "mountpoint", ""))

            all_mountpoints: list[str] = []
            seen_mounts: set[str] = set()
            for p in parts:
                m = str(getattr(p, "mountpoint", "") or "")
                if m and m not in seen_mounts:
                    seen_mounts.add(m)
                    all_mountpoints.append(m)

            if primary_mount in all_mountpoints:
                all_mountpoints.remove(primary_mount)
                all_mountpoints.insert(0, primary_mount)

            partitions.append(
                DiskPartitionMetrics(
                    device=str(getattr(primary, "device", "") or ""),
                    mountpoint=primary_mount,
                    filesystem=str(getattr(primary, "fstype", "") or ""),
                    options=str(getattr(primary, "opts", None))
                    if getattr(primary, "opts", None)
                    else None,
                    mountpoints=all_mountpoints,
                )
            )

        return partitions

    def _collect_usage(self, mountpoint: str) -> DiskUsageMetrics | None:
        """Internal helper to sample and validate disk usage for a mountpoint.

        Returns None if the partition is inaccessible, unmounted, unready,
        or if permissions are denied (e.g. Windows CD-ROM drive without media,
        disconnected network mount, or restricted root-only mount on Linux).
        """
        if not mountpoint:
            return None

        try:
            usage = psutil.disk_usage(mountpoint)
            if usage is None:
                return None

            return DiskUsageMetrics(
                total=max(0, int(usage.total)),
                used=max(0, int(usage.used)),
                free=max(0, int(usage.free)),
                percent=max(0.0, min(100.0, float(usage.percent))),
            )
        except (psutil.Error, OSError, PermissionError, ValueError):
            return None

    def _collect_io_counters(self) -> DiskIOCountersMetrics | None:
        """Internal helper to retrieve cumulative disk I/O performance counters.

        Disk I/O Strategy:
        We query psutil.disk_io_counters(perdisk=False) to obtain system-wide
        cumulative counters aggregated by the kernel. On Linux, psutil parses
        /proc/diskstats and filters out partition slices (e.g., sda1, nvme0n1p1)
        to aggregate whole physical disks. This avoids the severe double-counting
        issue caused by naively summing perdisk=True entries across physical
        drives, partition slices, loop devices, and device mapper targets.

        If I/O statistics are unavailable on the current platform (e.g. certain
        virtualized hosts, containers, or restricted environments), None is
        returned rather than inventing arbitrary zero counters.
        """
        try:
            counters = psutil.disk_io_counters(perdisk=False)
            if counters is None:
                return None

            return DiskIOCountersMetrics(
                read_count=max(0, int(counters.read_count)),
                write_count=max(0, int(counters.write_count)),
                read_bytes=max(0, int(counters.read_bytes)),
                write_bytes=max(0, int(counters.write_bytes)),
                read_time=max(0, int(getattr(counters, "read_time", 0) or 0)),
                write_time=max(0, int(getattr(counters, "write_time", 0) or 0)),
            )
        except (psutil.Error, OSError, AttributeError):
            return None

    def get_disk_partitions(self) -> list[DiskPartitionMetrics]:
        """Discover mounted physical disk partitions on the host system.

        Returns:
            list[DiskPartitionMetrics]: List of filtered and deduplicated partitions.
        """
        now = datetime.now(UTC)
        partitions = self._collect_partitions()
        self.last_sampled_at = now
        self._sample_count += 1
        return partitions

    def get_disk_usage(self, mountpoint: str) -> DiskUsageMetrics | None:
        """Collect storage capacity and utilization for a specific mountpoint.

        Args:
            mountpoint: The directory path or drive letter of the mounted partition.

        Returns:
            DiskUsageMetrics | None: Validated usage metrics, or None if inaccessible.
        """
        now = datetime.now(UTC)
        usage = self._collect_usage(mountpoint)
        self.last_sampled_at = now
        self._sample_count += 1
        return usage

    def get_disk_io_counters(self) -> DiskIOCountersMetrics | None:
        """Collect system-wide cumulative disk I/O counters.

        Returns:
            DiskIOCountersMetrics | None: Cumulative I/O counters, or None if unsupported.
        """
        now = datetime.now(UTC)
        counters = self._collect_io_counters()
        self.last_sampled_at = now
        self._sample_count += 1
        return counters

    def get_disk_metrics(self) -> DiskMetrics:
        """Collect a unified, timestamped snapshot of disk partitions, usage, and I/O.

        Each discovered partition is represented by a DiskPartitionInfo pairing
        partition metadata with its DiskUsageMetrics (or None if inaccessible).

        Returns:
            DiskMetrics: Unified disk telemetry container with a shared UTC timestamp.
        """
        now = datetime.now(UTC)
        partitions = self._collect_partitions()

        partition_infos: list[DiskPartitionInfo] = []
        total_cap = 0
        total_used = 0
        total_free = 0
        has_accessible_usage = False

        for part in partitions:
            usage = self._collect_usage(part.mountpoint)
            partition_infos.append(
                DiskPartitionInfo(
                    partition=part,
                    usage=usage,
                )
            )
            if usage is not None:
                has_accessible_usage = True
                total_cap += usage.total
                total_used += usage.used
                total_free += usage.free

        total_percent = (
            round((total_used / total_cap) * 100.0, 1)
            if has_accessible_usage and total_cap > 0
            else None
        )

        io_counters = self._collect_io_counters()

        self.last_sampled_at = now
        self._sample_count += 1

        return DiskMetrics(
            partitions=partition_infos,
            io_counters=io_counters,
            total_capacity_bytes=total_cap if has_accessible_usage else None,
            total_used_bytes=total_used if has_accessible_usage else None,
            total_free_bytes=total_free if has_accessible_usage else None,
            total_percent=total_percent,
            unique_partition_count=len(partition_infos),
            timestamp=now,
        )
