"""System performance bottleneck detection engine.

Analyzes real-time metrics and historical telemetry across CPU, memory,
disk, and network subsystems to identify performance bottlenecks and saturation.
"""

from datetime import UTC, datetime
from typing import Any

from app.schemas.analysis import (
    BottleneckDetection,
    BottlenecksResponse,
    BottleneckType,
    ResourceSeverity,
)
from app.schemas.history import HistoricalSystemMetrics
from app.schemas.metrics import SystemMetrics


def detect_bottlenecks(
    metrics: SystemMetrics,
    history_docs: list[HistoricalSystemMetrics] | None = None,
) -> BottlenecksResponse:
    """Analyze system metrics snapshot and historical records to detect bottlenecks.

    Evaluates:
    - CPU: overall utilization, per-core saturation, top consuming processes.
    - Memory: RAM usage percentage, available memory, swap thrashing.
    - Disk: storage capacity exhaustion, partition saturation, I/O rates.
    - Network: packet drop rates, interface transmission errors.

    Correlates with recent historical records to determine if pressure is transient
    or sustained.
    """
    now = datetime.now(UTC)
    active_bottlenecks: list[BottleneckDetection] = []

    # 1. CPU Bottleneck Evaluation
    if metrics.cpu is not None and metrics.cpu.usage_percent is not None:
        cpu_pct = metrics.cpu.usage_percent
        per_core = metrics.cpu.per_core_usage or []
        max_core = max([c for c in per_core if c is not None], default=cpu_pct)

        # Identify top CPU processes if process telemetry is present
        top_cpu_procs: list[dict[str, Any]] = []
        if metrics.processes and metrics.processes.processes:
            sorted_by_cpu = sorted(
                metrics.processes.processes,
                key=lambda p: p.cpu_percent if p.cpu_percent is not None else -1.0,
                reverse=True,
            )
            top_cpu_procs = [
                {
                    "pid": p.pid,
                    "name": p.name,
                    "cpu_percent": round(p.cpu_percent, 1)
                    if p.cpu_percent is not None
                    else 0.0,
                }
                for p in sorted_by_cpu[:3]
                if p.cpu_percent is not None and p.cpu_percent > 10.0
            ]

        # Determine CPU severity
        if cpu_pct >= 90.0 or max_core >= 98.0:
            active_bottlenecks.append(
                BottleneckDetection(
                    type=BottleneckType.CPU,
                    severity=ResourceSeverity.CRITICAL,
                    evidence={
                        "overall_usage_percent": round(cpu_pct, 1),
                        "max_core_usage_percent": round(max_core, 1),
                        "top_processes": top_cpu_procs,
                    },
                    explanation=(
                        f"Critical CPU pressure detected: overall utilization is {round(cpu_pct, 1)}% "
                        f"with peak core saturation at {round(max_core, 1)}%. "
                        "Process thread execution is throttled by run-queue contention."
                    ),
                    recommended_action=(
                        "Inspect runaway processes, profile CPU-intensive threads, "
                        "or reassign affinity/niceness to balance workload."
                    ),
                    timestamp=now,
                )
            )
        elif cpu_pct >= 80.0 or max_core >= 92.0:
            active_bottlenecks.append(
                BottleneckDetection(
                    type=BottleneckType.CPU,
                    severity=ResourceSeverity.HIGH,
                    evidence={
                        "overall_usage_percent": round(cpu_pct, 1),
                        "max_core_usage_percent": round(max_core, 1),
                        "top_processes": top_cpu_procs,
                    },
                    explanation=(
                        f"Elevated CPU workload detected ({round(cpu_pct, 1)}% overall, "
                        f"peak core {round(max_core, 1)}%). Thread scheduling latency may increase."
                    ),
                    recommended_action=(
                        "Monitor sustained compute usage and prioritize critical processes."
                    ),
                    timestamp=now,
                )
            )
        elif cpu_pct >= 70.0:
            active_bottlenecks.append(
                BottleneckDetection(
                    type=BottleneckType.CPU,
                    severity=ResourceSeverity.MEDIUM,
                    evidence={
                        "overall_usage_percent": round(cpu_pct, 1),
                        "top_processes": top_cpu_procs,
                    },
                    explanation=(
                        f"Moderate CPU utilization observed ({round(cpu_pct, 1)}%). "
                        "System capacity is reaching the upper nominal threshold."
                    ),
                    recommended_action="Track background background jobs to prevent peak saturation.",
                    timestamp=now,
                )
            )

    # 2. Memory & Swap Bottleneck Evaluation
    if metrics.memory is not None:
        mem_pct = metrics.memory.virtual.percent
        avail_mb = round(metrics.memory.virtual.available / (1024 * 1024), 1)
        swap_pct = (
            metrics.memory.swap.percent if metrics.memory.swap is not None else 0.0
        )
        swap_used_mb = (
            round(metrics.memory.swap.used / (1024 * 1024), 1)
            if metrics.memory.swap is not None
            else 0.0
        )

        top_mem_procs: list[dict[str, Any]] = []
        if metrics.processes and metrics.processes.processes:
            sorted_by_mem = sorted(
                metrics.processes.processes,
                key=lambda p: (
                    p.memory_percent if p.memory_percent is not None else -1.0
                ),
                reverse=True,
            )
            top_mem_procs = [
                {
                    "pid": p.pid,
                    "name": p.name,
                    "memory_percent": round(p.memory_percent, 1)
                    if p.memory_percent is not None
                    else 0.0,
                    "memory_rss_mb": round(p.memory_rss / (1024 * 1024), 1),
                }
                for p in sorted_by_mem[:3]
                if p.memory_percent is not None and p.memory_percent > 5.0
            ]

        if mem_pct >= 90.0 or swap_pct >= 50.0:
            active_bottlenecks.append(
                BottleneckDetection(
                    type=BottleneckType.MEMORY,
                    severity=ResourceSeverity.CRITICAL,
                    evidence={
                        "ram_percent": round(mem_pct, 1),
                        "available_mb": avail_mb,
                        "swap_percent": round(swap_pct, 1),
                        "swap_used_mb": swap_used_mb,
                        "top_processes": top_mem_procs,
                    },
                    explanation=(
                        f"Critical memory exhaustion: RAM at {round(mem_pct, 1)}% ({avail_mb} MB available) "
                        f"and swap at {round(swap_pct, 1)}%. Severe risk of OOM killing and paging latency."
                    ),
                    recommended_action=(
                        "Immediately terminate non-critical high-memory tasks or allocate additional RAM."
                    ),
                    timestamp=now,
                )
            )
        elif mem_pct >= 80.0 or swap_pct >= 20.0:
            active_bottlenecks.append(
                BottleneckDetection(
                    type=BottleneckType.MEMORY,
                    severity=ResourceSeverity.HIGH,
                    evidence={
                        "ram_percent": round(mem_pct, 1),
                        "available_mb": avail_mb,
                        "swap_percent": round(swap_pct, 1),
                        "swap_used_mb": swap_used_mb,
                        "top_processes": top_mem_procs,
                    },
                    explanation=(
                        f"High memory consumption: RAM usage is {round(mem_pct, 1)}% with active swap paging "
                        f"({round(swap_pct, 1)}% used)."
                    ),
                    recommended_action=(
                        "Investigate memory retention in resident applications to prevent swap thrashing."
                    ),
                    timestamp=now,
                )
            )
        elif mem_pct >= 70.0 or swap_pct >= 5.0:
            active_bottlenecks.append(
                BottleneckDetection(
                    type=BottleneckType.MEMORY,
                    severity=ResourceSeverity.MEDIUM,
                    evidence={
                        "ram_percent": round(mem_pct, 1),
                        "available_mb": avail_mb,
                        "swap_percent": round(swap_pct, 1),
                        "top_processes": top_mem_procs,
                    },
                    explanation=(
                        f"Moderate memory pressure: RAM at {round(mem_pct, 1)}% with slight swap engagement."
                    ),
                    recommended_action="Audit background services and cache sizes.",
                    timestamp=now,
                )
            )

    # 3. Disk Bottleneck Evaluation
    if metrics.disk is not None:
        max_part_pct = 0.0
        saturated_mount = None
        saturated_free_gb = 0.0

        for part in metrics.disk.partitions:
            if part.usage is not None and part.usage.percent > max_part_pct:
                max_part_pct = part.usage.percent
                saturated_mount = part.partition.mountpoint
                saturated_free_gb = round(part.usage.free / (1024**3), 2)

        if max_part_pct >= 95.0:
            active_bottlenecks.append(
                BottleneckDetection(
                    type=BottleneckType.DISK,
                    severity=ResourceSeverity.CRITICAL,
                    evidence={
                        "max_partition_percent": round(max_part_pct, 1),
                        "mountpoint": saturated_mount,
                        "free_space_gb": saturated_free_gb,
                        "io_limitation_note": (
                            "Capacity bottleneck confirmed. Per-device disk await latency is an OS-kernel metric; "
                            "throughput rates reflect cumulative activity."
                        ),
                    },
                    explanation=(
                        f"Partition '{saturated_mount}' is {round(max_part_pct, 1)}% full with only "
                        f"{saturated_free_gb} GB remaining. Filesystem operations will fail if capacity is exhausted."
                    ),
                    recommended_action=(
                        "Clean up unneeded logs, temporary files, and expand disk volume immediately."
                    ),
                    timestamp=now,
                )
            )
        elif max_part_pct >= 85.0:
            active_bottlenecks.append(
                BottleneckDetection(
                    type=BottleneckType.DISK,
                    severity=ResourceSeverity.HIGH,
                    evidence={
                        "max_partition_percent": round(max_part_pct, 1),
                        "mountpoint": saturated_mount,
                        "free_space_gb": saturated_free_gb,
                    },
                    explanation=(
                        f"Partition '{saturated_mount}' is {round(max_part_pct, 1)}% full. "
                        "Filesystem fragmentation and write throttling risk are elevated."
                    ),
                    recommended_action="Prune obsolete caches and monitor partition growth.",
                    timestamp=now,
                )
            )
        elif max_part_pct >= 75.0:
            active_bottlenecks.append(
                BottleneckDetection(
                    type=BottleneckType.DISK,
                    severity=ResourceSeverity.MEDIUM,
                    evidence={
                        "max_partition_percent": round(max_part_pct, 1),
                        "mountpoint": saturated_mount,
                    },
                    explanation=f"Partition '{saturated_mount}' is {round(max_part_pct, 1)}% full.",
                    recommended_action="Schedule routine disk cleanup.",
                    timestamp=now,
                )
            )

    # 4. Network Bottleneck Evaluation
    if metrics.network is not None:
        total_drops = 0
        total_errs = 0
        for iface in metrics.network.interfaces:
            if iface.io_counters:
                total_drops += iface.io_counters.dropin + iface.io_counters.dropout
                total_errs += iface.io_counters.errin + iface.io_counters.errout

        if total_drops > 100 or total_errs > 50:
            active_bottlenecks.append(
                BottleneckDetection(
                    type=BottleneckType.NETWORK,
                    severity=ResourceSeverity.HIGH,
                    evidence={
                        "cumulative_packet_drops": total_drops,
                        "cumulative_packet_errors": total_errs,
                        "throughput_context": (
                            "Throughput volume alone does not signify congestion. "
                            "Packet drops and errors provide explicit evidence of buffer overrun."
                        ),
                    },
                    explanation=(
                        f"Network interface packet drop ({total_drops}) or error ({total_errs}) count is elevated. "
                        "Socket buffers may be overflowing or network medium is experiencing frame degradation."
                    ),
                    recommended_action=(
                        "Inspect interface MTU, network duplex settings, and kernel socket buffer backlog."
                    ),
                    timestamp=now,
                )
            )
        elif total_drops > 0 or total_errs > 0:
            active_bottlenecks.append(
                BottleneckDetection(
                    type=BottleneckType.NETWORK,
                    severity=ResourceSeverity.LOW,
                    evidence={
                        "cumulative_packet_drops": total_drops,
                        "cumulative_packet_errors": total_errs,
                    },
                    explanation=(
                        f"Minor packet drop ({total_drops}) or error ({total_errs}) activity observed."
                    ),
                    recommended_action="Verify physical cable connections and interface statistics.",
                    timestamp=now,
                )
            )

    # 5. Historical Telemetry Correlation
    historical_pressure = False
    historical_summary: dict[str, Any] | None = None

    if history_docs and len(history_docs) > 0:
        valid_cpu = [
            doc.cpu.usage_percent
            for doc in history_docs
            if doc.cpu and doc.cpu.usage_percent is not None
        ]
        valid_mem = [
            doc.memory.percent
            for doc in history_docs
            if doc.memory and doc.memory.percent is not None
        ]

        sample_count = len(history_docs)
        avg_cpu = sum(valid_cpu) / len(valid_cpu) if valid_cpu else None
        avg_mem = sum(valid_mem) / len(valid_mem) if valid_mem else None
        peak_cpu = max(valid_cpu, default=None)
        peak_mem = max(valid_mem, default=None)

        if (avg_cpu is not None and avg_cpu >= 70.0) or (
            avg_mem is not None and avg_mem >= 75.0
        ):
            historical_pressure = True

        historical_summary = {
            "samples_analyzed": sample_count,
            "avg_cpu_percent": round(avg_cpu, 1) if avg_cpu is not None else None,
            "avg_memory_percent": round(avg_mem, 1) if avg_mem is not None else None,
            "peak_cpu_percent": round(peak_cpu, 1) if peak_cpu is not None else None,
            "peak_memory_percent": round(peak_mem, 1) if peak_mem is not None else None,
            "sustained_pressure": historical_pressure,
        }

    return BottlenecksResponse(
        active_bottlenecks=active_bottlenecks,
        historical_pressure_detected=historical_pressure,
        historical_summary=historical_summary,
        timestamp=now,
    )
