from datetime import UTC
from unittest.mock import MagicMock

import psutil

from app.collectors.system import SystemMetricsCollector
from app.schemas.metrics import (
    CPUMetrics,
    DiskMetrics,
    MemoryMetrics,
    NetworkMetrics,
    ProcessCollectionMetrics,
    SwapMemoryMetrics,
    SystemMetrics,
    VirtualMemoryMetrics,
)


def _make_dummy_cpu() -> CPUMetrics:
    return CPUMetrics(
        usage_percent=15.0,
        per_core_usage=[15.0],
        physical_cores=2,
        logical_cores=4,
    )


def _make_dummy_memory() -> MemoryMetrics:
    vm = VirtualMemoryMetrics(
        total=8000, available=4000, used=4000, free=4000, percent=50.0
    )
    sm = SwapMemoryMetrics(total=0, used=0, free=0, percent=0.0, sin=0, sout=0)
    return MemoryMetrics(virtual=vm, swap=sm)


def _make_dummy_disk() -> DiskMetrics:
    return DiskMetrics(partitions=[], io_counters=None)


def _make_dummy_network() -> NetworkMetrics:
    return NetworkMetrics(interfaces=[], io_counters=None, throughput=None)


def _make_dummy_processes() -> ProcessCollectionMetrics:
    return ProcessCollectionMetrics(processes=[], total_processes=0)


def test_system_collector_initialization():
    collector = SystemMetricsCollector()
    assert collector._sample_count == 0
    assert collector.last_sampled_at is None
    assert collector.initialized_at.tzinfo is not None
    assert collector.cpu_collector is not None
    assert collector.memory_collector is not None
    assert collector.disk_collector is not None
    assert collector.network_collector is not None
    assert collector.process_collector is not None


def test_collect_all_success():
    mock_cpu = MagicMock()
    mock_cpu.get_cpu_metrics.return_value = _make_dummy_cpu()

    mock_mem = MagicMock()
    mock_mem.get_memory_metrics.return_value = _make_dummy_memory()

    mock_disk = MagicMock()
    mock_disk.get_disk_metrics.return_value = _make_dummy_disk()

    mock_net = MagicMock()
    mock_net.get_network_metrics.return_value = _make_dummy_network()

    mock_proc = MagicMock()
    mock_proc.get_process_collection_metrics.return_value = _make_dummy_processes()

    system_collector = SystemMetricsCollector(
        cpu_collector=mock_cpu,
        memory_collector=mock_mem,
        disk_collector=mock_disk,
        network_collector=mock_net,
        process_collector=mock_proc,
    )

    metrics = system_collector.collect_all()

    assert isinstance(metrics, SystemMetrics)
    assert metrics.cpu is not None
    assert metrics.cpu.usage_percent == 15.0
    assert metrics.memory is not None
    assert metrics.disk is not None
    assert metrics.network is not None
    assert metrics.processes is not None
    assert metrics.timestamp.tzinfo is not None
    assert system_collector._sample_count == 1
    assert system_collector.last_sampled_at == metrics.timestamp


def test_cpu_failure_isolation():
    mock_cpu = MagicMock()
    mock_cpu.get_cpu_metrics.side_effect = psutil.Error("Simulated CPU error")

    mock_mem = MagicMock()
    mock_mem.get_memory_metrics.return_value = _make_dummy_memory()

    mock_disk = MagicMock()
    mock_disk.get_disk_metrics.return_value = _make_dummy_disk()

    mock_net = MagicMock()
    mock_net.get_network_metrics.return_value = _make_dummy_network()

    mock_proc = MagicMock()
    mock_proc.get_process_collection_metrics.return_value = _make_dummy_processes()

    system_collector = SystemMetricsCollector(
        cpu_collector=mock_cpu,
        memory_collector=mock_mem,
        disk_collector=mock_disk,
        network_collector=mock_net,
        process_collector=mock_proc,
    )

    metrics = system_collector.collect_all()

    assert isinstance(metrics, SystemMetrics)
    # CPU failure isolated to None; other collectors successfully reported
    assert metrics.cpu is None
    assert metrics.memory is not None
    assert metrics.disk is not None
    assert metrics.network is not None
    assert metrics.processes is not None


def test_memory_failure_isolation():
    mock_cpu = MagicMock()
    mock_cpu.get_cpu_metrics.return_value = _make_dummy_cpu()

    mock_mem = MagicMock()
    mock_mem.get_memory_metrics.side_effect = OSError("Memory read failed")

    mock_disk = MagicMock()
    mock_disk.get_disk_metrics.return_value = _make_dummy_disk()

    mock_net = MagicMock()
    mock_net.get_network_metrics.return_value = _make_dummy_network()

    mock_proc = MagicMock()
    mock_proc.get_process_collection_metrics.return_value = _make_dummy_processes()

    system_collector = SystemMetricsCollector(
        cpu_collector=mock_cpu,
        memory_collector=mock_mem,
        disk_collector=mock_disk,
        network_collector=mock_net,
        process_collector=mock_proc,
    )

    metrics = system_collector.collect_all()

    assert metrics.cpu is not None
    assert metrics.memory is None
    assert metrics.disk is not None
    assert metrics.network is not None
    assert metrics.processes is not None


def test_disk_failure_isolation():
    mock_cpu = MagicMock()
    mock_cpu.get_cpu_metrics.return_value = _make_dummy_cpu()

    mock_mem = MagicMock()
    mock_mem.get_memory_metrics.return_value = _make_dummy_memory()

    mock_disk = MagicMock()
    mock_disk.get_disk_metrics.side_effect = psutil.Error("Disk error")

    mock_net = MagicMock()
    mock_net.get_network_metrics.return_value = _make_dummy_network()

    mock_proc = MagicMock()
    mock_proc.get_process_collection_metrics.return_value = _make_dummy_processes()

    system_collector = SystemMetricsCollector(
        cpu_collector=mock_cpu,
        memory_collector=mock_mem,
        disk_collector=mock_disk,
        network_collector=mock_net,
        process_collector=mock_proc,
    )

    metrics = system_collector.collect_all()

    assert metrics.cpu is not None
    assert metrics.memory is not None
    assert metrics.disk is None
    assert metrics.network is not None
    assert metrics.processes is not None


def test_network_failure_isolation():
    mock_cpu = MagicMock()
    mock_cpu.get_cpu_metrics.return_value = _make_dummy_cpu()

    mock_mem = MagicMock()
    mock_mem.get_memory_metrics.return_value = _make_dummy_memory()

    mock_disk = MagicMock()
    mock_disk.get_disk_metrics.return_value = _make_dummy_disk()

    mock_net = MagicMock()
    mock_net.get_network_metrics.side_effect = OSError("Network unreachable")

    mock_proc = MagicMock()
    mock_proc.get_process_collection_metrics.return_value = _make_dummy_processes()

    system_collector = SystemMetricsCollector(
        cpu_collector=mock_cpu,
        memory_collector=mock_mem,
        disk_collector=mock_disk,
        network_collector=mock_net,
        process_collector=mock_proc,
    )

    metrics = system_collector.collect_all()

    assert metrics.cpu is not None
    assert metrics.memory is not None
    assert metrics.disk is not None
    assert metrics.network is None
    assert metrics.processes is not None


def test_process_failure_isolation():
    mock_cpu = MagicMock()
    mock_cpu.get_cpu_metrics.return_value = _make_dummy_cpu()

    mock_mem = MagicMock()
    mock_mem.get_memory_metrics.return_value = _make_dummy_memory()

    mock_disk = MagicMock()
    mock_disk.get_disk_metrics.return_value = _make_dummy_disk()

    mock_net = MagicMock()
    mock_net.get_network_metrics.return_value = _make_dummy_network()

    mock_proc = MagicMock()
    mock_proc.get_process_collection_metrics.side_effect = psutil.AccessDenied()

    system_collector = SystemMetricsCollector(
        cpu_collector=mock_cpu,
        memory_collector=mock_mem,
        disk_collector=mock_disk,
        network_collector=mock_net,
        process_collector=mock_proc,
    )

    metrics = system_collector.collect_all()

    assert metrics.cpu is not None
    assert metrics.memory is not None
    assert metrics.disk is not None
    assert metrics.network is not None
    assert metrics.processes is None


def test_multiple_failures_isolation():
    mock_cpu = MagicMock()
    mock_cpu.get_cpu_metrics.side_effect = psutil.Error("CPU failed")

    mock_mem = MagicMock()
    mock_mem.get_memory_metrics.return_value = _make_dummy_memory()

    mock_disk = MagicMock()
    mock_disk.get_disk_metrics.side_effect = OSError("Disk failed")

    mock_net = MagicMock()
    mock_net.get_network_metrics.return_value = _make_dummy_network()

    mock_proc = MagicMock()
    mock_proc.get_process_collection_metrics.side_effect = RuntimeError(
        "Process crashed"
    )

    system_collector = SystemMetricsCollector(
        cpu_collector=mock_cpu,
        memory_collector=mock_mem,
        disk_collector=mock_disk,
        network_collector=mock_net,
        process_collector=mock_proc,
    )

    metrics = system_collector.collect_all()

    assert metrics.cpu is None
    assert metrics.memory is not None
    assert metrics.disk is None
    assert metrics.network is not None
    assert metrics.processes is None


def test_all_components_unavailable():
    mock_cpu = MagicMock()
    mock_cpu.get_cpu_metrics.side_effect = psutil.Error()

    mock_mem = MagicMock()
    mock_mem.get_memory_metrics.side_effect = psutil.Error()

    mock_disk = MagicMock()
    mock_disk.get_disk_metrics.side_effect = psutil.Error()

    mock_net = MagicMock()
    mock_net.get_network_metrics.side_effect = psutil.Error()

    mock_proc = MagicMock()
    mock_proc.get_process_collection_metrics.side_effect = psutil.Error()

    system_collector = SystemMetricsCollector(
        cpu_collector=mock_cpu,
        memory_collector=mock_mem,
        disk_collector=mock_disk,
        network_collector=mock_net,
        process_collector=mock_proc,
    )

    metrics = system_collector.collect_all()

    assert isinstance(metrics, SystemMetrics)
    assert metrics.cpu is None
    assert metrics.memory is None
    assert metrics.disk is None
    assert metrics.network is None
    assert metrics.processes is None
    assert metrics.timestamp.tzinfo is not None


def test_collector_instances_persisted_across_calls():
    mock_cpu = MagicMock()
    mock_cpu.get_cpu_metrics.return_value = _make_dummy_cpu()

    mock_mem = MagicMock()
    mock_mem.get_memory_metrics.return_value = _make_dummy_memory()

    mock_disk = MagicMock()
    mock_disk.get_disk_metrics.return_value = _make_dummy_disk()

    mock_net = MagicMock()
    mock_net.get_network_metrics.return_value = _make_dummy_network()

    mock_proc = MagicMock()
    mock_proc.get_process_collection_metrics.return_value = _make_dummy_processes()

    system_collector = SystemMetricsCollector(
        cpu_collector=mock_cpu,
        memory_collector=mock_mem,
        disk_collector=mock_disk,
        network_collector=mock_net,
        process_collector=mock_proc,
    )

    # First call
    system_collector.collect_all()
    # Second call
    system_collector.collect_all()

    # Collectors must have been called twice on the exact same instance
    assert mock_cpu.get_cpu_metrics.call_count == 2
    assert mock_mem.get_memory_metrics.call_count == 2
    assert mock_disk.get_disk_metrics.call_count == 2
    assert mock_net.get_network_metrics.call_count == 2
    assert mock_proc.get_process_collection_metrics.call_count == 2
    assert system_collector._sample_count == 2


def test_top_level_timestamp_timezone_aware():
    collector = SystemMetricsCollector()
    metrics = collector.collect_all()
    assert metrics.timestamp.tzinfo is not None
    assert metrics.timestamp.tzinfo == UTC


def test_individual_collect_methods():
    mock_cpu = MagicMock()
    mock_cpu.get_cpu_metrics.return_value = _make_dummy_cpu()

    collector = SystemMetricsCollector(cpu_collector=mock_cpu)
    cpu_result = collector.collect_cpu()
    assert cpu_result is not None
    assert cpu_result.usage_percent == 15.0


def test_system_collector_real_system_smoke():
    """Live smoke test on host verifying persistent instances and first/second reading semantics."""
    collector = SystemMetricsCollector()

    # Call 1: First readings
    m1 = collector.collect_all()
    assert isinstance(m1, SystemMetrics)
    assert m1.timestamp.tzinfo is not None

    if m1.cpu is not None:
        # First reading: CPU utilization is None
        assert m1.cpu.usage_percent is None

    if m1.network is not None and m1.network.throughput is not None:
        # First reading: Network throughput is None
        assert m1.network.throughput.bytes_sent_per_sec is None

    # Call 2: Persistent collector state enables non-blocking second readings
    m2 = collector.collect_all()
    assert isinstance(m2, SystemMetrics)
    assert collector._sample_count == 2

    if m2.cpu is not None:
        # Subsequent reading: CPU utilization may be numeric
        assert m2.cpu.usage_percent is None or m2.cpu.usage_percent >= 0.0

    if m2.network is not None and m2.network.throughput is not None:
        # Subsequent reading: Throughput is computed
        assert (
            m2.network.throughput.bytes_sent_per_sec is None
            or m2.network.throughput.bytes_sent_per_sec >= 0.0
        )
