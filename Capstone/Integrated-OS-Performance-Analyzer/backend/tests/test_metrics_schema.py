from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.metrics import (
    CPUFrequency,
    CPUMetrics,
    DiskIOCountersMetrics,
    DiskMetrics,
    DiskPartitionInfo,
    DiskPartitionMetrics,
    DiskUsageMetrics,
    MemoryMetrics,
    NetworkInterfaceMetrics,
    NetworkIOCountersMetrics,
    NetworkMetrics,
    NetworkThroughputMetrics,
    ProcessCollectionMetrics,
    ProcessMetrics,
    SwapMemoryMetrics,
    SystemMetrics,
    VirtualMemoryMetrics,
)


def test_valid_cpu_metrics_numeric():
    timestamp = datetime.now(UTC)
    metrics = CPUMetrics(
        usage_percent=25.4,
        per_core_usage=[20.0, 30.8],
        physical_cores=2,
        logical_cores=4,
        frequency=CPUFrequency(current=2400.0, min=800.0, max=3200.0),
        timestamp=timestamp,
    )

    assert metrics.usage_percent == 25.4
    assert metrics.per_core_usage == [20.0, 30.8]
    assert metrics.physical_cores == 2
    assert metrics.logical_cores == 4
    assert metrics.frequency is not None
    assert metrics.frequency.current == 2400.0
    assert metrics.frequency.min == 800.0
    assert metrics.frequency.max == 3200.0
    assert metrics.timestamp == timestamp


def test_valid_cpu_metrics_with_none_readings():
    # Initial reading where baseline has not yet elapsed
    metrics = CPUMetrics(
        usage_percent=None,
        per_core_usage=None,
        physical_cores=4,
        logical_cores=8,
    )

    assert metrics.usage_percent is None
    assert metrics.per_core_usage is None
    assert metrics.physical_cores == 4
    assert metrics.logical_cores == 8
    assert metrics.frequency is None
    assert metrics.timestamp.tzinfo is not None


def test_cpu_usage_bounds_validation():
    # Negative usage should raise
    with pytest.raises(ValidationError):
        CPUMetrics(
            usage_percent=-0.1,
            per_core_usage=[10.0],
            physical_cores=1,
            logical_cores=1,
            timestamp=datetime.now(UTC),
        )

    # Usage above 100 should raise
    with pytest.raises(ValidationError):
        CPUMetrics(
            usage_percent=100.1,
            per_core_usage=[10.0],
            physical_cores=1,
            logical_cores=1,
            timestamp=datetime.now(UTC),
        )

    # Genuine 0.0 usage is valid
    zero_metrics = CPUMetrics(
        usage_percent=0.0,
        per_core_usage=[0.0],
        physical_cores=1,
        logical_cores=1,
    )
    assert zero_metrics.usage_percent == 0.0


def test_per_core_usage_validation():
    # None is valid (initial reading)
    metrics_none = CPUMetrics(
        usage_percent=None,
        per_core_usage=None,
        physical_cores=1,
        logical_cores=1,
    )
    assert metrics_none.per_core_usage is None

    # Empty list is valid
    metrics_empty = CPUMetrics(
        usage_percent=0.0,
        per_core_usage=[],
        physical_cores=1,
        logical_cores=1,
    )
    assert metrics_empty.per_core_usage == []

    # Negative per-core usage must be rejected
    with pytest.raises(ValidationError, match="must be between 0.0 and 100.0"):
        CPUMetrics(
            usage_percent=10.0,
            per_core_usage=[10.0, -1.0],
            physical_cores=2,
            logical_cores=2,
            timestamp=datetime.now(UTC),
        )

    # Per-core usage over 100 must be rejected
    with pytest.raises(ValidationError, match="must be between 0.0 and 100.0"):
        CPUMetrics(
            usage_percent=10.0,
            per_core_usage=[105.0],
            physical_cores=1,
            logical_cores=1,
            timestamp=datetime.now(UTC),
        )


def test_non_negative_cores_validation():
    # Negative physical cores
    with pytest.raises(ValidationError):
        CPUMetrics(
            usage_percent=10.0,
            per_core_usage=[10.0],
            physical_cores=-1,
            logical_cores=1,
            timestamp=datetime.now(UTC),
        )

    # Negative logical cores
    with pytest.raises(ValidationError):
        CPUMetrics(
            usage_percent=10.0,
            per_core_usage=[10.0],
            physical_cores=1,
            logical_cores=-1,
            timestamp=datetime.now(UTC),
        )


def test_cpu_frequency_validation():
    # Valid optional None fields
    freq_none = CPUFrequency()
    assert freq_none.current is None
    assert freq_none.min is None
    assert freq_none.max is None

    # Negative current frequency
    with pytest.raises(ValidationError):
        CPUFrequency(current=-100.0)

    # Negative min frequency
    with pytest.raises(ValidationError):
        CPUFrequency(min=-1.0)

    # Negative max frequency
    with pytest.raises(ValidationError):
        CPUFrequency(max=-1.0)


def test_timezone_aware_timestamp_validation():
    # Naive timestamp must be rejected
    naive_dt = datetime.now()
    with pytest.raises(ValidationError, match="Timestamp must be timezone-aware"):
        CPUMetrics(
            usage_percent=10.0,
            per_core_usage=[10.0],
            physical_cores=1,
            logical_cores=1,
            timestamp=naive_dt,
        )

    # Default factory provides timezone-aware UTC timestamp
    metrics = CPUMetrics(
        usage_percent=10.0,
        per_core_usage=[10.0],
        physical_cores=1,
        logical_cores=1,
    )
    assert metrics.timestamp.tzinfo is not None


def test_system_metrics_foundation():
    cpu_metrics = CPUMetrics(
        usage_percent=15.0,
        per_core_usage=[15.0],
        physical_cores=1,
        logical_cores=1,
    )
    system_metrics = SystemMetrics(cpu=cpu_metrics)

    assert system_metrics.cpu.usage_percent == 15.0
    assert system_metrics.memory is None
    assert system_metrics.disk is None
    assert system_metrics.network is None
    assert system_metrics.timestamp.tzinfo is not None

    # Naive timestamp in SystemMetrics must also be rejected
    naive_dt = datetime.now()
    with pytest.raises(ValidationError, match="Timestamp must be timezone-aware"):
        SystemMetrics(cpu=cpu_metrics, timestamp=naive_dt)


def test_virtual_memory_metrics_validation():
    # Valid model
    vm = VirtualMemoryMetrics(
        total=8000000000,
        available=5000000000,
        used=3000000000,
        free=2000000000,
        percent=37.5,
    )
    assert vm.total == 8000000000
    assert vm.available == 5000000000
    assert vm.used == 3000000000
    assert vm.free == 2000000000
    assert vm.percent == 37.5

    # Negative total
    with pytest.raises(ValidationError):
        VirtualMemoryMetrics(
            total=-1,
            available=0,
            used=0,
            free=0,
            percent=0.0,
        )

    # Negative available
    with pytest.raises(ValidationError):
        VirtualMemoryMetrics(
            total=1000,
            available=-1,
            used=0,
            free=0,
            percent=0.0,
        )

    # Percent > 100
    with pytest.raises(ValidationError):
        VirtualMemoryMetrics(
            total=1000,
            available=500,
            used=500,
            free=500,
            percent=100.1,
        )

    # Percent < 0
    with pytest.raises(ValidationError):
        VirtualMemoryMetrics(
            total=1000,
            available=500,
            used=500,
            free=500,
            percent=-0.1,
        )


def test_swap_memory_metrics_validation():
    # Valid model
    sm = SwapMemoryMetrics(
        total=2000000000,
        used=500000000,
        free=1500000000,
        percent=25.0,
        sin=100,
        sout=200,
    )
    assert sm.total == 2000000000
    assert sm.used == 500000000
    assert sm.free == 1500000000
    assert sm.percent == 25.0
    assert sm.sin == 100
    assert sm.sout == 200

    # Zero swap space
    sm_zero = SwapMemoryMetrics(
        total=0,
        used=0,
        free=0,
        percent=0.0,
        sin=0,
        sout=0,
    )
    assert sm_zero.total == 0

    # Negative used
    with pytest.raises(ValidationError):
        SwapMemoryMetrics(
            total=1000,
            used=-1,
            free=1000,
            percent=0.0,
            sin=0,
            sout=0,
        )

    # Negative sin
    with pytest.raises(ValidationError):
        SwapMemoryMetrics(
            total=1000,
            used=0,
            free=1000,
            percent=0.0,
            sin=-1,
            sout=0,
        )

    # Percent > 100
    with pytest.raises(ValidationError):
        SwapMemoryMetrics(
            total=1000,
            used=0,
            free=1000,
            percent=100.1,
            sin=0,
            sout=0,
        )


def test_memory_metrics_validation():
    vm = VirtualMemoryMetrics(
        total=8000000000,
        available=5000000000,
        used=3000000000,
        free=2000000000,
        percent=37.5,
    )
    sm = SwapMemoryMetrics(
        total=2000000000,
        used=0,
        free=2000000000,
        percent=0.0,
        sin=0,
        sout=0,
    )
    mm = MemoryMetrics(virtual=vm, swap=sm)

    assert mm.virtual.total == 8000000000
    assert mm.swap.total == 2000000000
    assert mm.timestamp.tzinfo is not None

    # Naive timestamp rejection
    naive_dt = datetime.now()
    with pytest.raises(ValidationError, match="Timestamp must be timezone-aware"):
        MemoryMetrics(virtual=vm, swap=sm, timestamp=naive_dt)


def test_system_metrics_with_memory():
    cpu_metrics = CPUMetrics(
        usage_percent=15.0,
        per_core_usage=[15.0],
        physical_cores=1,
        logical_cores=1,
    )
    vm = VirtualMemoryMetrics(
        total=8000000000,
        available=5000000000,
        used=3000000000,
        free=2000000000,
        percent=37.5,
    )
    sm = SwapMemoryMetrics(
        total=0,
        used=0,
        free=0,
        percent=0.0,
        sin=0,
        sout=0,
    )
    mem_metrics = MemoryMetrics(virtual=vm, swap=sm)
    system_metrics = SystemMetrics(cpu=cpu_metrics, memory=mem_metrics)

    assert system_metrics.memory is not None
    assert system_metrics.memory.virtual.total == 8000000000
    assert system_metrics.memory.swap.total == 0


def test_valid_disk_partition_metrics():
    part = DiskPartitionMetrics(
        device="/dev/sda1",
        mountpoint="/",
        filesystem="ext4",
        options="rw,relatime",
    )
    assert part.device == "/dev/sda1"
    assert part.mountpoint == "/"
    assert part.filesystem == "ext4"
    assert part.options == "rw,relatime"

    # None options default
    part_no_opts = DiskPartitionMetrics(
        device="C:\\",
        mountpoint="C:\\",
        filesystem="NTFS",
    )
    assert part_no_opts.options is None


def test_valid_disk_usage_metrics():
    usage = DiskUsageMetrics(
        total=500000000000,
        used=200000000000,
        free=300000000000,
        percent=40.0,
    )
    assert usage.total == 500000000000
    assert usage.used == 200000000000
    assert usage.free == 300000000000
    assert usage.percent == 40.0


def test_disk_usage_metrics_negative_values_rejected():
    with pytest.raises(ValidationError):
        DiskUsageMetrics(
            total=-1,
            used=100,
            free=100,
            percent=50.0,
        )

    with pytest.raises(ValidationError):
        DiskUsageMetrics(
            total=200,
            used=-1,
            free=100,
            percent=50.0,
        )

    with pytest.raises(ValidationError):
        DiskUsageMetrics(
            total=200,
            used=100,
            free=-1,
            percent=50.0,
        )


def test_disk_usage_metrics_percent_bounds():
    # Negative percent rejected
    with pytest.raises(ValidationError):
        DiskUsageMetrics(
            total=1000,
            used=500,
            free=500,
            percent=-0.1,
        )

    # Above 100 rejected
    with pytest.raises(ValidationError):
        DiskUsageMetrics(
            total=1000,
            used=500,
            free=500,
            percent=100.1,
        )

    # Exactly 0.0 and 100.0 valid
    usage_min = DiskUsageMetrics(total=1000, used=0, free=1000, percent=0.0)
    usage_max = DiskUsageMetrics(total=1000, used=1000, free=0, percent=100.0)
    assert usage_min.percent == 0.0
    assert usage_max.percent == 100.0


def test_disk_usage_zero_capacity_edge_case():
    # Zero capacity device (e.g. empty virtual drive or pseudo disk)
    usage = DiskUsageMetrics(
        total=0,
        used=0,
        free=0,
        percent=0.0,
    )
    assert usage.total == 0
    assert usage.used == 0
    assert usage.free == 0
    assert usage.percent == 0.0


def test_valid_disk_io_counters_metrics():
    io = DiskIOCountersMetrics(
        read_count=1000,
        write_count=500,
        read_bytes=10485760,
        write_bytes=5242880,
        read_time=1500,
        write_time=800,
    )
    assert io.read_count == 1000
    assert io.write_count == 500
    assert io.read_bytes == 10485760
    assert io.write_bytes == 5242880
    assert io.read_time == 1500
    assert io.write_time == 800


def test_disk_io_counters_negative_rejected():
    with pytest.raises(ValidationError):
        DiskIOCountersMetrics(
            read_count=-1,
            write_count=0,
            read_bytes=0,
            write_bytes=0,
            read_time=0,
            write_time=0,
        )

    with pytest.raises(ValidationError):
        DiskIOCountersMetrics(
            read_count=0,
            write_count=0,
            read_bytes=-10,
            write_bytes=0,
            read_time=0,
            write_time=0,
        )

    with pytest.raises(ValidationError):
        DiskIOCountersMetrics(
            read_count=0,
            write_count=0,
            read_bytes=0,
            write_bytes=0,
            read_time=-5,
            write_time=0,
        )


def test_disk_partition_info_validation():
    part = DiskPartitionMetrics(
        device="/dev/sda1",
        mountpoint="/",
        filesystem="ext4",
    )
    usage = DiskUsageMetrics(
        total=1000000,
        used=400000,
        free=600000,
        percent=40.0,
    )

    info_accessible = DiskPartitionInfo(partition=part, usage=usage)
    assert info_accessible.partition.mountpoint == "/"
    assert info_accessible.usage is not None
    assert info_accessible.usage.total == 1000000

    # Inaccessible partition preserves metadata with usage=None
    info_inaccessible = DiskPartitionInfo(partition=part, usage=None)
    assert info_inaccessible.partition.mountpoint == "/"
    assert info_inaccessible.usage is None


def test_disk_metrics_combined_validation():
    part = DiskPartitionMetrics(
        device="/dev/sda1",
        mountpoint="/",
        filesystem="ext4",
    )
    info = DiskPartitionInfo(partition=part, usage=None)
    io = DiskIOCountersMetrics(
        read_count=10,
        write_count=5,
        read_bytes=1024,
        write_bytes=512,
        read_time=20,
        write_time=10,
    )
    dm = DiskMetrics(partitions=[info], io_counters=io)

    assert len(dm.partitions) == 1
    assert dm.partitions[0].partition.mountpoint == "/"
    assert dm.io_counters is not None
    assert dm.io_counters.read_count == 10
    assert dm.timestamp.tzinfo is not None

    # io_counters=None accepted when unavailable on platform
    dm_no_io = DiskMetrics(partitions=[info], io_counters=None)
    assert dm_no_io.io_counters is None


def test_disk_metrics_naive_timestamp_rejected():
    naive_dt = datetime.now()
    with pytest.raises(ValidationError, match="Timestamp must be timezone-aware"):
        DiskMetrics(partitions=[], io_counters=None, timestamp=naive_dt)


def test_system_metrics_with_disk():
    cpu = CPUMetrics(
        usage_percent=10.0,
        per_core_usage=[10.0],
        physical_cores=1,
        logical_cores=1,
    )
    vm = VirtualMemoryMetrics(
        total=8000,
        available=4000,
        used=4000,
        free=4000,
        percent=50.0,
    )
    sm = SwapMemoryMetrics(
        total=0,
        used=0,
        free=0,
        percent=0.0,
        sin=0,
        sout=0,
    )
    mem = MemoryMetrics(virtual=vm, swap=sm)
    disk = DiskMetrics(partitions=[], io_counters=None)

    system_metrics = SystemMetrics(cpu=cpu, memory=mem, disk=disk)
    assert system_metrics.disk is not None
    assert system_metrics.disk.partitions == []
    assert system_metrics.disk.io_counters is None


def test_valid_network_io_counters_metrics():
    io = NetworkIOCountersMetrics(
        bytes_sent=1024,
        bytes_recv=2048,
        packets_sent=10,
        packets_recv=20,
        errin=1,
        errout=2,
        dropin=3,
        dropout=4,
    )
    assert io.bytes_sent == 1024
    assert io.bytes_recv == 2048
    assert io.packets_sent == 10
    assert io.packets_recv == 20
    assert io.errin == 1
    assert io.errout == 2
    assert io.dropin == 3
    assert io.dropout == 4


def test_network_io_counters_negative_values_rejected():
    with pytest.raises(ValidationError):
        NetworkIOCountersMetrics(
            bytes_sent=-1,
            bytes_recv=0,
            packets_sent=0,
            packets_recv=0,
            errin=0,
            errout=0,
            dropin=0,
            dropout=0,
        )

    with pytest.raises(ValidationError):
        NetworkIOCountersMetrics(
            bytes_sent=0,
            bytes_recv=-1,
            packets_sent=0,
            packets_recv=0,
            errin=0,
            errout=0,
            dropin=0,
            dropout=0,
        )

    with pytest.raises(ValidationError):
        NetworkIOCountersMetrics(
            bytes_sent=0,
            bytes_recv=0,
            packets_sent=0,
            packets_recv=0,
            errin=-1,
            errout=0,
            dropin=0,
            dropout=0,
        )

    with pytest.raises(ValidationError):
        NetworkIOCountersMetrics(
            bytes_sent=0,
            bytes_recv=0,
            packets_sent=0,
            packets_recv=0,
            errin=0,
            errout=0,
            dropin=-1,
            dropout=0,
        )


def test_network_throughput_metrics_validation():
    # Valid numeric throughput
    tp = NetworkThroughputMetrics(
        bytes_sent_per_sec=1024.5,
        bytes_recv_per_sec=2048.25,
    )
    assert tp.bytes_sent_per_sec == 1024.5
    assert tp.bytes_recv_per_sec == 2048.25

    # Valid None values (first sample/unavailable)
    tp_none = NetworkThroughputMetrics(
        bytes_sent_per_sec=None,
        bytes_recv_per_sec=None,
    )
    assert tp_none.bytes_sent_per_sec is None
    assert tp_none.bytes_recv_per_sec is None

    # Negative rates rejected
    with pytest.raises(ValidationError):
        NetworkThroughputMetrics(bytes_sent_per_sec=-1.0)

    with pytest.raises(ValidationError):
        NetworkThroughputMetrics(bytes_recv_per_sec=-0.01)


def test_network_interface_metrics_validation():
    # Valid complete interface
    io = NetworkIOCountersMetrics(
        bytes_sent=100,
        bytes_recv=200,
        packets_sent=1,
        packets_recv=2,
        errin=0,
        errout=0,
        dropin=0,
        dropout=0,
    )
    tp = NetworkThroughputMetrics(
        bytes_sent_per_sec=50.0,
        bytes_recv_per_sec=100.0,
    )
    iface = NetworkInterfaceMetrics(
        name="eth0",
        is_up=True,
        speed=1000,
        mtu=1500,
        addresses=["IPv4", "MAC: 00:11:22:33:44:55"],
        io_counters=io,
        throughput=tp,
    )
    assert iface.name == "eth0"
    assert iface.is_up is True
    assert iface.speed == 1000
    assert iface.mtu == 1500
    assert iface.addresses == ["IPv4", "MAC: 00:11:22:33:44:55"]
    assert iface.io_counters == io
    assert iface.throughput == tp

    # Minimal interface with default None fields
    minimal = NetworkInterfaceMetrics(name="lo", is_up=True)
    assert minimal.name == "lo"
    assert minimal.is_up is True
    assert minimal.speed is None
    assert minimal.mtu is None
    assert minimal.addresses is None
    assert minimal.io_counters is None
    assert minimal.throughput is None

    # Negative speed rejected
    with pytest.raises(ValidationError):
        NetworkInterfaceMetrics(name="eth0", is_up=True, speed=-10)

    # Negative mtu rejected
    with pytest.raises(ValidationError):
        NetworkInterfaceMetrics(name="eth0", is_up=True, mtu=-1500)


def test_network_metrics_combined_validation():
    iface = NetworkInterfaceMetrics(name="eth0", is_up=True)
    io = NetworkIOCountersMetrics(
        bytes_sent=500,
        bytes_recv=1000,
        packets_sent=5,
        packets_recv=10,
        errin=0,
        errout=0,
        dropin=0,
        dropout=0,
    )
    tp = NetworkThroughputMetrics(
        bytes_sent_per_sec=250.0,
        bytes_recv_per_sec=500.0,
    )
    net_metrics = NetworkMetrics(
        interfaces=[iface],
        io_counters=io,
        throughput=tp,
    )
    assert len(net_metrics.interfaces) == 1
    assert net_metrics.interfaces[0].name == "eth0"
    assert net_metrics.io_counters == io
    assert net_metrics.throughput == tp
    assert net_metrics.timestamp.tzinfo is not None

    # Optional fields as None
    net_metrics_empty = NetworkMetrics()
    assert net_metrics_empty.interfaces == []
    assert net_metrics_empty.io_counters is None
    assert net_metrics_empty.throughput is None


def test_network_metrics_naive_timestamp_rejected():
    naive_dt = datetime.now()
    with pytest.raises(ValidationError, match="Timestamp must be timezone-aware"):
        NetworkMetrics(timestamp=naive_dt)


def test_system_metrics_with_network():
    cpu = CPUMetrics(
        usage_percent=10.0,
        per_core_usage=[10.0],
        physical_cores=1,
        logical_cores=1,
    )
    net_metrics = NetworkMetrics(interfaces=[], io_counters=None, throughput=None)
    system_metrics = SystemMetrics(cpu=cpu, network=net_metrics)

    assert system_metrics.network is not None
    assert system_metrics.network.interfaces == []
    assert system_metrics.network.io_counters is None
    assert system_metrics.network.throughput is None


def test_valid_process_metrics():
    proc = ProcessMetrics(
        pid=1234,
        name="python3",
        status="running",
        cpu_percent=12.5,
        memory_rss=104857600,
        memory_vms=209715200,
        memory_percent=1.25,
        num_threads=4,
        create_time=1700000000.0,
        username="piyush",
    )
    assert proc.pid == 1234
    assert proc.name == "python3"
    assert proc.status == "running"
    assert proc.cpu_percent == 12.5
    assert proc.memory_rss == 104857600
    assert proc.memory_vms == 209715200
    assert proc.memory_percent == 1.25
    assert proc.num_threads == 4
    assert proc.create_time == 1700000000.0
    assert proc.username == "piyush"
    assert proc.timestamp.tzinfo is not None

    # Optional fields as None (e.g. initial CPU reading unavailable)
    proc_minimal = ProcessMetrics(
        pid=1,
        name="systemd",
        status="sleeping",
        memory_rss=5000000,
        memory_vms=10000000,
    )
    assert proc_minimal.cpu_percent is None
    assert proc_minimal.memory_percent is None
    assert proc_minimal.create_time is None
    assert proc_minimal.username is None
    assert proc_minimal.num_threads == 1


def test_process_metrics_negative_fields_rejected():
    # Negative PID rejected
    with pytest.raises(ValidationError):
        ProcessMetrics(
            pid=-1,
            name="init",
            status="running",
            memory_rss=1000,
            memory_vms=1000,
        )

    # Negative memory RSS rejected
    with pytest.raises(ValidationError):
        ProcessMetrics(
            pid=1,
            name="init",
            status="running",
            memory_rss=-1000,
            memory_vms=1000,
        )

    # Negative memory VMS rejected
    with pytest.raises(ValidationError):
        ProcessMetrics(
            pid=1,
            name="init",
            status="running",
            memory_rss=1000,
            memory_vms=-1000,
        )

    # Negative num_threads rejected
    with pytest.raises(ValidationError):
        ProcessMetrics(
            pid=1,
            name="init",
            status="running",
            memory_rss=1000,
            memory_vms=1000,
            num_threads=-1,
        )

    # Negative create_time rejected
    with pytest.raises(ValidationError):
        ProcessMetrics(
            pid=1,
            name="init",
            status="running",
            memory_rss=1000,
            memory_vms=1000,
            create_time=-10.0,
        )


def test_process_metrics_percentage_bounds():
    # CPU percent < 0 rejected
    with pytest.raises(ValidationError):
        ProcessMetrics(
            pid=1,
            name="proc",
            status="running",
            memory_rss=1000,
            memory_vms=1000,
            cpu_percent=-0.1,
        )

    # CPU percent > 100 rejected
    with pytest.raises(ValidationError):
        ProcessMetrics(
            pid=1,
            name="proc",
            status="running",
            memory_rss=1000,
            memory_vms=1000,
            cpu_percent=100.1,
        )

    # Memory percent < 0 rejected
    with pytest.raises(ValidationError):
        ProcessMetrics(
            pid=1,
            name="proc",
            status="running",
            memory_rss=1000,
            memory_vms=1000,
            memory_percent=-0.1,
        )

    # Memory percent > 100 rejected
    with pytest.raises(ValidationError):
        ProcessMetrics(
            pid=1,
            name="proc",
            status="running",
            memory_rss=1000,
            memory_vms=1000,
            memory_percent=100.1,
        )

    # Boundary percentages valid (0.0 and 100.0)
    p_min = ProcessMetrics(
        pid=1,
        name="proc",
        status="running",
        memory_rss=1000,
        memory_vms=1000,
        cpu_percent=0.0,
        memory_percent=0.0,
    )
    p_max = ProcessMetrics(
        pid=1,
        name="proc",
        status="running",
        memory_rss=1000,
        memory_vms=1000,
        cpu_percent=100.0,
        memory_percent=100.0,
    )
    assert p_min.cpu_percent == 0.0
    assert p_max.cpu_percent == 100.0


def test_process_metrics_naive_timestamp_rejected():
    naive_dt = datetime.now()
    with pytest.raises(ValidationError, match="Timestamp must be timezone-aware"):
        ProcessMetrics(
            pid=1,
            name="proc",
            status="running",
            memory_rss=1000,
            memory_vms=1000,
            timestamp=naive_dt,
        )


def test_valid_process_collection_metrics():
    proc = ProcessMetrics(
        pid=1,
        name="init",
        status="running",
        memory_rss=1000,
        memory_vms=2000,
    )
    collection = ProcessCollectionMetrics(
        processes=[proc],
        total_processes=1,
    )
    assert len(collection.processes) == 1
    assert collection.total_processes == 1
    assert collection.timestamp.tzinfo is not None

    # Empty collection valid
    empty = ProcessCollectionMetrics(processes=[], total_processes=0)
    assert empty.processes == []
    assert empty.total_processes == 0

    # Negative total_processes rejected
    with pytest.raises(ValidationError):
        ProcessCollectionMetrics(processes=[], total_processes=-1)


def test_process_collection_metrics_naive_timestamp_rejected():
    naive_dt = datetime.now()
    with pytest.raises(ValidationError, match="Timestamp must be timezone-aware"):
        ProcessCollectionMetrics(
            processes=[],
            total_processes=0,
            timestamp=naive_dt,
        )


def test_system_metrics_with_processes():
    cpu = CPUMetrics(
        usage_percent=10.0,
        per_core_usage=[10.0],
        physical_cores=1,
        logical_cores=1,
    )
    proc_collection = ProcessCollectionMetrics(processes=[], total_processes=0)
    system_metrics = SystemMetrics(cpu=cpu, processes=proc_collection)

    assert system_metrics.processes is not None
    assert system_metrics.processes.processes == []
    assert system_metrics.processes.total_processes == 0
