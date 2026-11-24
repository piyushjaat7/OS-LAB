"""Tests for performance analysis engine, bottleneck detector, and analysis REST endpoints."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.analyzers.bottlenecks import detect_bottlenecks
from app.analyzers.health import analyze_system_health
from app.api.dependencies import get_system_collector, reset_system_collector
from app.main import app
from app.schemas.analysis import (
    BottleneckType,
    HealthStatus,
    ResourceSeverity,
    ResourceState,
)
from app.schemas.history import (
    HistoricalCPUInfo,
    HistoricalMemoryInfo,
    HistoricalSystemMetrics,
)
from app.schemas.metrics import (
    CPUMetrics,
    DiskMetrics,
    DiskPartitionInfo,
    DiskPartitionMetrics,
    DiskUsageMetrics,
    MemoryMetrics,
    NetworkInterfaceMetrics,
    NetworkIOCountersMetrics,
    NetworkMetrics,
    ProcessCollectionMetrics,
    ProcessMetrics,
    SwapMemoryMetrics,
    SystemMetrics,
    VirtualMemoryMetrics,
)


def _build_metrics(
    cpu_usage: float = 15.0,
    per_core: list[float] | None = None,
    ram_percent: float = 35.0,
    swap_percent: float = 0.0,
    disk_percent: float = 40.0,
    net_drops: int = 0,
    net_errs: int = 0,
) -> SystemMetrics:
    """Helper to build calibrated SystemMetrics for analysis test cases."""
    if per_core is None:
        per_core = [cpu_usage, cpu_usage]

    cpu = CPUMetrics(
        usage_percent=cpu_usage,
        per_core_usage=per_core,
        physical_cores=2,
        logical_cores=2,
    )
    mem = MemoryMetrics(
        virtual=VirtualMemoryMetrics(
            total=16 * 1024**3,
            available=int(16 * 1024**3 * (1 - ram_percent / 100)),
            used=int(16 * 1024**3 * (ram_percent / 100)),
            free=int(16 * 1024**3 * (1 - ram_percent / 100)),
            percent=ram_percent,
        ),
        swap=SwapMemoryMetrics(
            total=4 * 1024**3,
            used=int(4 * 1024**3 * (swap_percent / 100)),
            free=int(4 * 1024**3 * (1 - swap_percent / 100)),
            percent=swap_percent,
            sin=0,
            sout=0,
        ),
    )
    part = DiskPartitionInfo(
        partition=DiskPartitionMetrics(
            device="/dev/sda1",
            mountpoint="/",
            filesystem="ext4",
        ),
        usage=DiskUsageMetrics(
            total=100 * 1024**3,
            used=int(100 * 1024**3 * (disk_percent / 100)),
            free=int(100 * 1024**3 * (1 - disk_percent / 100)),
            percent=disk_percent,
        ),
    )
    disk = DiskMetrics(partitions=[part], io_counters=None)
    iface = NetworkInterfaceMetrics(
        name="eth0",
        is_up=True,
        io_counters=NetworkIOCountersMetrics(
            bytes_sent=10000,
            bytes_recv=20000,
            packets_sent=100,
            packets_recv=200,
            errin=net_errs,
            errout=0,
            dropin=net_drops,
            dropout=0,
        ),
    )
    network = NetworkMetrics(interfaces=[iface])
    procs = ProcessCollectionMetrics(
        processes=[
            ProcessMetrics(
                pid=100,
                name="daemon_app",
                status="running",
                cpu_percent=12.0,
                memory_rss=200 * 1024**2,
                memory_vms=500 * 1024**2,
                memory_percent=1.2,
                num_threads=4,
                create_time=1700000000.0,
                username="root",
            )
        ],
        total_processes=1,
    )
    return SystemMetrics(
        cpu=cpu,
        memory=mem,
        disk=disk,
        network=network,
        processes=procs,
    )


def test_health_scoring_optimal():
    """Verify health score is 100 and EXCELLENT on a healthy system."""
    metrics = _build_metrics(
        cpu_usage=15.0, ram_percent=35.0, swap_percent=0.0, disk_percent=30.0
    )
    analysis = analyze_system_health(metrics)

    assert analysis.health_score == 100
    assert analysis.health_status == HealthStatus.EXCELLENT
    assert analysis.cpu_classification.status == ResourceState.OPTIMAL
    assert analysis.memory_classification.status == ResourceState.OPTIMAL
    assert analysis.disk_classification.status == ResourceState.OPTIMAL
    assert len(analysis.critical_alerts) == 0


def test_health_scoring_critical():
    """Verify health score falls below 50 with CRITICAL status under intense pressure."""
    metrics = _build_metrics(
        cpu_usage=95.0,
        per_core=[99.0, 91.0],
        ram_percent=92.0,
        swap_percent=60.0,
        disk_percent=98.0,
    )
    analysis = analyze_system_health(metrics)

    assert analysis.health_score < 50
    assert analysis.health_status == HealthStatus.CRITICAL
    assert analysis.cpu_classification.status == ResourceState.CRITICAL
    assert analysis.memory_classification.status == ResourceState.CRITICAL
    assert analysis.disk_classification.status == ResourceState.CRITICAL
    assert len(analysis.critical_alerts) >= 3
    assert len(analysis.suggested_actions) >= 2


def test_detect_bottlenecks_cpu():
    """Test CPU bottleneck detection when usage and per-core saturation are high."""
    metrics = _build_metrics(cpu_usage=92.0, per_core=[100.0, 84.0])
    res = detect_bottlenecks(metrics)

    cpu_bottlenecks = [
        b for b in res.active_bottlenecks if b.type == BottleneckType.CPU
    ]
    assert len(cpu_bottlenecks) == 1
    assert cpu_bottlenecks[0].severity == ResourceSeverity.CRITICAL
    assert cpu_bottlenecks[0].evidence["overall_usage_percent"] == 92.0
    assert "run-queue contention" in cpu_bottlenecks[0].explanation


def test_detect_bottlenecks_memory_and_swap():
    """Test Memory bottleneck detection under RAM exhaustion and swap usage."""
    metrics = _build_metrics(ram_percent=88.0, swap_percent=25.0)
    res = detect_bottlenecks(metrics)

    mem_bottlenecks = [
        b for b in res.active_bottlenecks if b.type == BottleneckType.MEMORY
    ]
    assert len(mem_bottlenecks) == 1
    assert mem_bottlenecks[0].severity in (
        ResourceSeverity.HIGH,
        ResourceSeverity.CRITICAL,
    )
    assert mem_bottlenecks[0].evidence["swap_percent"] == 25.0


def test_detect_bottlenecks_disk():
    """Test Disk capacity bottleneck detection on nearly full filesystem."""
    metrics = _build_metrics(disk_percent=96.0)
    res = detect_bottlenecks(metrics)

    disk_bottlenecks = [
        b for b in res.active_bottlenecks if b.type == BottleneckType.DISK
    ]
    assert len(disk_bottlenecks) == 1
    assert disk_bottlenecks[0].severity == ResourceSeverity.CRITICAL
    assert disk_bottlenecks[0].evidence["mountpoint"] == "/"


def test_detect_bottlenecks_network():
    """Test Network bottleneck detection on packet drops."""
    metrics = _build_metrics(net_drops=150, net_errs=10)
    res = detect_bottlenecks(metrics)

    net_bottlenecks = [
        b for b in res.active_bottlenecks if b.type == BottleneckType.NETWORK
    ]
    assert len(net_bottlenecks) == 1
    assert net_bottlenecks[0].severity == ResourceSeverity.HIGH
    assert net_bottlenecks[0].evidence["cumulative_packet_drops"] == 150


def test_detect_bottlenecks_historical_correlation():
    """Test bottleneck detection historical correlation across recorded documents."""
    metrics = _build_metrics(cpu_usage=20.0, ram_percent=30.0)

    # Mock historical records indicating sustained high CPU
    history_docs = [
        HistoricalSystemMetrics(
            timestamp=datetime.now(UTC),
            cpu=HistoricalCPUInfo(usage_percent=85.0),
            memory=HistoricalMemoryInfo(percent=50.0),
        )
        for _ in range(10)
    ]

    res = detect_bottlenecks(metrics, history_docs=history_docs)

    assert res.historical_pressure_detected is True
    assert res.historical_summary is not None
    assert res.historical_summary["samples_analyzed"] == 10
    assert res.historical_summary["avg_cpu_percent"] == 85.0


def test_rest_api_health_endpoint():
    """Test GET /api/v1/analysis/health endpoint via TestClient."""
    mock_collector = MagicMock()
    mock_collector.collect_all.return_value = _build_metrics(
        cpu_usage=25.0, ram_percent=45.0
    )

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/analysis/health")
        assert response.status_code == 200
        data = response.json()
        assert "health_score" in data
        assert "health_status" in data
        assert "cpu_classification" in data
        assert data["health_status"] == "EXCELLENT"
    finally:
        app.dependency_overrides.clear()
        reset_system_collector()


def test_rest_api_bottlenecks_endpoint():
    """Test GET /api/v1/analysis/bottlenecks endpoint via TestClient."""
    mock_collector = MagicMock()
    mock_collector.collect_all.return_value = _build_metrics(
        cpu_usage=95.0, ram_percent=92.0
    )

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/analysis/bottlenecks")
        assert response.status_code == 200
        data = response.json()
        assert "active_bottlenecks" in data
        assert len(data["active_bottlenecks"]) >= 2
    finally:
        app.dependency_overrides.clear()
        reset_system_collector()


def test_rest_api_scheduling_endpoints():
    """Test POST endpoints for all scheduling algorithms and comparison."""
    client = TestClient(app)
    workload = {
        "processes": [
            {"process_id": "P1", "arrival_time": 0.0, "burst_time": 4.0, "priority": 2},
            {"process_id": "P2", "arrival_time": 1.0, "burst_time": 3.0, "priority": 1},
        ]
    }

    # FCFS
    r_fcfs = client.post("/api/v1/analysis/scheduling/fcfs", json=workload)
    assert r_fcfs.status_code == 200
    assert "FCFS" in r_fcfs.json()["algorithm"]

    # SJF
    r_sjf = client.post("/api/v1/analysis/scheduling/sjf", json=workload)
    assert r_sjf.status_code == 200
    assert "SJF" in r_sjf.json()["algorithm"]

    # SRTF
    r_srtf = client.post("/api/v1/analysis/scheduling/srtf", json=workload)
    assert r_srtf.status_code == 200
    assert "SRTF" in r_srtf.json()["algorithm"]

    # Priority
    r_prio = client.post(
        "/api/v1/analysis/scheduling/priority",
        json={**workload, "preemptive": True, "priority_order": "lower_is_higher"},
    )
    assert r_prio.status_code == 200
    assert "Priority" in r_prio.json()["algorithm"]

    # Round Robin
    r_rr = client.post(
        "/api/v1/analysis/scheduling/round-robin",
        json={**workload, "time_quantum": 2.0},
    )
    assert r_rr.status_code == 200
    assert "Round Robin" in r_rr.json()["algorithm"]

    # Compare
    r_comp = client.post(
        "/api/v1/analysis/scheduling/compare",
        json={**workload, "time_quantum": 2.0, "priority_order": "lower_is_higher"},
    )
    assert r_comp.status_code == 200
    comp_data = r_comp.json()
    assert "algorithms" in comp_data
    assert "summary_table" in comp_data
    assert len(comp_data["summary_table"]) >= 5
