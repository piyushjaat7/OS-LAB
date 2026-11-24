"""System health scoring and resource classification engine.

Evaluates aggregated system telemetry and produces a unified health score (0-100),
overall operational status, resource state classifications, alerts, and remediation advice.
"""

from datetime import UTC, datetime

from app.analyzers.bottlenecks import detect_bottlenecks
from app.schemas.analysis import (
    BottleneckDetection,
    HealthStatus,
    ResourceClassification,
    ResourceState,
    SystemHealthAnalysis,
)
from app.schemas.metrics import SystemMetrics


def analyze_system_health(
    metrics: SystemMetrics,
    bottlenecks: list[BottleneckDetection] | None = None,
) -> SystemHealthAnalysis:
    """Compute overall system health score and subsystem classifications.

    Scoring model starts from 100 (optimal) and applies mathematically calibrated
    deductions for subsystem pressure, thrashing, and saturation.
    """
    now = metrics.timestamp if metrics.timestamp else datetime.now(UTC)

    if bottlenecks is None:
        bottleneck_res = detect_bottlenecks(metrics)
        bottlenecks = bottleneck_res.active_bottlenecks

    warnings: list[str] = []
    critical_alerts: list[str] = []
    suggested_actions: set[str] = set()

    # Base score
    score = 100

    # 1. CPU Classification & Scoring
    cpu_status = ResourceState.UNKNOWN
    cpu_percent = None
    cpu_details = "CPU telemetry unavailable."

    if metrics.cpu is not None and metrics.cpu.usage_percent is not None:
        cpu_percent = metrics.cpu.usage_percent
        per_core = metrics.cpu.per_core_usage or []
        max_core = max([c for c in per_core if c is not None], default=cpu_percent)

        if cpu_percent >= 90.0 or max_core >= 98.0:
            cpu_status = ResourceState.CRITICAL
            score -= 25
            critical_alerts.append(
                f"CPU utilization critically high at {round(cpu_percent, 1)}% "
                f"(peak core: {round(max_core, 1)}%)."
            )
            suggested_actions.add(
                "Inspect running processes with high CPU utilization and mitigate thread contention."
            )
        elif cpu_percent >= 75.0 or max_core >= 90.0:
            cpu_status = ResourceState.WARNING
            score -= 15
            warnings.append(
                f"CPU utilization is high at {round(cpu_percent, 1)}% "
                f"(peak core: {round(max_core, 1)}%)."
            )
            suggested_actions.add(
                "Review active compute jobs and verify CPU scheduling load distribution."
            )
        elif cpu_percent >= 60.0:
            cpu_status = ResourceState.ELEVATED
            score -= 8
            warnings.append(f"CPU utilization is elevated at {round(cpu_percent, 1)}%.")
        elif cpu_percent < 20.0:
            cpu_status = ResourceState.OPTIMAL
        else:
            cpu_status = ResourceState.NORMAL

        cpu_details = (
            f"Overall usage: {round(cpu_percent, 1)}%, logical cores: "
            f"{metrics.cpu.logical_cores or len(per_core)}, max core: {round(max_core, 1)}%."
        )

    cpu_classification = ResourceClassification(
        status=cpu_status,
        utilization_percent=round(cpu_percent, 1) if cpu_percent is not None else None,
        details=cpu_details,
    )

    # 2. Memory & Swap Classification & Scoring
    mem_status = ResourceState.UNKNOWN
    mem_percent = None
    mem_details = "Memory telemetry unavailable."

    if metrics.memory is not None:
        mem_percent = metrics.memory.virtual.percent
        avail_gb = round(metrics.memory.virtual.available / (1024**3), 2)
        total_gb = round(metrics.memory.virtual.total / (1024**3), 2)
        swap_percent = (
            metrics.memory.swap.percent if metrics.memory.swap is not None else 0.0
        )

        # Deductions
        if mem_percent >= 90.0:
            score -= 25
            critical_alerts.append(
                f"Physical RAM is critically saturated at {round(mem_percent, 1)}% "
                f"({avail_gb} GB free of {total_gb} GB)."
            )
            suggested_actions.add(
                "Terminate unneeded high-memory applications to avoid OS out-of-memory killing."
            )
        elif mem_percent >= 80.0:
            score -= 15
            warnings.append(
                f"Physical RAM usage is high at {round(mem_percent, 1)}% ({avail_gb} GB free)."
            )
            suggested_actions.add(
                "Investigate resident memory leaks and trim background caches."
            )
        elif mem_percent >= 70.0:
            score -= 8
            warnings.append(f"Physical RAM usage elevated at {round(mem_percent, 1)}%.")

        if swap_percent >= 50.0:
            score -= 20
            critical_alerts.append(
                f"Swap space usage critically elevated at {round(swap_percent, 1)}%."
            )
            suggested_actions.add(
                "Active swap thrashing detected; reduce resident memory workload immediately."
            )
        elif swap_percent >= 20.0:
            score -= 10
            warnings.append(f"Swap usage is elevated at {round(swap_percent, 1)}%.")
        elif swap_percent >= 5.0:
            score -= 5

        # Status categorization
        if mem_percent >= 90.0 or swap_percent >= 50.0:
            mem_status = ResourceState.CRITICAL
        elif mem_percent >= 80.0 or swap_percent >= 20.0:
            mem_status = ResourceState.WARNING
        elif mem_percent >= 70.0 or swap_percent >= 5.0:
            mem_status = ResourceState.ELEVATED
        elif mem_percent < 40.0 and swap_percent < 1.0:
            mem_status = ResourceState.OPTIMAL
        else:
            mem_status = ResourceState.NORMAL

        mem_details = (
            f"RAM: {round(mem_percent, 1)}% used ({avail_gb} GB free of {total_gb} GB). "
            f"Swap: {round(swap_percent, 1)}% used."
        )

    memory_classification = ResourceClassification(
        status=mem_status,
        utilization_percent=round(mem_percent, 1) if mem_percent is not None else None,
        details=mem_details,
    )

    # 3. Disk Classification & Scoring
    disk_status = ResourceState.UNKNOWN
    disk_percent = None
    disk_details = "Disk telemetry unavailable."

    if metrics.disk is not None and metrics.disk.partitions:
        max_part_pct = 0.0
        max_part_mount = "/"

        for part in metrics.disk.partitions:
            if part.usage is not None and part.usage.percent > max_part_pct:
                max_part_pct = part.usage.percent
                max_part_mount = part.partition.mountpoint

        disk_percent = max_part_pct

        if disk_percent >= 95.0:
            disk_status = ResourceState.CRITICAL
            score -= 25
            critical_alerts.append(
                f"Disk mount '{max_part_mount}' is {round(disk_percent, 1)}% full."
            )
            suggested_actions.add(
                f"Expand filesystem or purge unneeded files on '{max_part_mount}'."
            )
        elif disk_percent >= 85.0:
            disk_status = ResourceState.WARNING
            score -= 15
            warnings.append(
                f"Disk mount '{max_part_mount}' is {round(disk_percent, 1)}% full."
            )
            suggested_actions.add(f"Perform disk cleanup on mount '{max_part_mount}'.")
        elif disk_percent >= 75.0:
            disk_status = ResourceState.ELEVATED
            score -= 8
            warnings.append(
                f"Disk mount '{max_part_mount}' is at {round(disk_percent, 1)}% capacity."
            )
        elif disk_percent < 50.0:
            disk_status = ResourceState.OPTIMAL
        else:
            disk_status = ResourceState.NORMAL

        disk_details = (
            f"Peak partition '{max_part_mount}' at {round(disk_percent, 1)}% utilization "
            f"across {len(metrics.disk.partitions)} discovered partitions."
        )

    disk_classification = ResourceClassification(
        status=disk_status,
        utilization_percent=round(disk_percent, 1)
        if disk_percent is not None
        else None,
        details=disk_details,
    )

    # 4. Network Classification & Scoring
    net_status = ResourceState.OPTIMAL
    net_details = "Network metrics within normal parameters."

    if metrics.network is not None:
        total_drops = 0
        total_errs = 0
        for iface in metrics.network.interfaces:
            if iface.io_counters:
                total_drops += iface.io_counters.dropin + iface.io_counters.dropout
                total_errs += iface.io_counters.errin + iface.io_counters.errout

        if total_drops > 100 or total_errs > 50:
            net_status = ResourceState.WARNING
            score -= 10
            warnings.append(
                f"Network interfaces report {total_drops} dropped packets and {total_errs} errors."
            )
            suggested_actions.add(
                "Investigate network interface link negotiation, socket buffers, or duplex mismatches."
            )
            net_details = f"Packet drops: {total_drops}, errors: {total_errs}."
        elif total_drops > 0 or total_errs > 0:
            net_status = ResourceState.ELEVATED
            score -= 3
            net_details = (
                f"Minor packet drops ({total_drops}) or errors ({total_errs}) detected."
            )
        else:
            net_status = ResourceState.OPTIMAL
            net_details = f"All {len(metrics.network.interfaces)} interfaces reporting 0 errors/drops."

    network_classification = ResourceClassification(
        status=net_status,
        utilization_percent=None,
        details=net_details,
    )

    # Add recommended actions from active bottlenecks
    for b in bottlenecks:
        if b.recommended_action:
            suggested_actions.add(b.recommended_action)

    # Clamp health score between 0 and 100
    final_score = max(0, min(100, score))

    # Overall Health Status mapping
    if final_score >= 85:
        health_status = HealthStatus.EXCELLENT
    elif final_score >= 70:
        health_status = HealthStatus.GOOD
    elif final_score >= 50:
        health_status = HealthStatus.DEGRADED
    else:
        health_status = HealthStatus.CRITICAL

    return SystemHealthAnalysis(
        health_score=final_score,
        health_status=health_status,
        cpu_classification=cpu_classification,
        memory_classification=memory_classification,
        disk_classification=disk_classification,
        network_classification=network_classification,
        warnings=warnings,
        critical_alerts=critical_alerts,
        suggested_actions=sorted(suggested_actions),
        active_bottlenecks=bottlenecks,
        timestamp=now,
    )
