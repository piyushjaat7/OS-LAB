from collections import namedtuple
from unittest.mock import patch

import psutil

from app.collectors.network import NetworkCollector
from app.schemas.metrics import (
    NetworkInterfaceMetrics,
    NetworkIOCountersMetrics,
    NetworkMetrics,
    NetworkThroughputMetrics,
)

MockNetIO = namedtuple(
    "snetio",
    [
        "bytes_sent",
        "bytes_recv",
        "packets_sent",
        "packets_recv",
        "errin",
        "errout",
        "dropin",
        "dropout",
    ],
)
MockNicStats = namedtuple("snicstats", ["isup", "duplex", "speed", "mtu", "flags"])
MockNicAddr = namedtuple(
    "snicaddr", ["family", "address", "netmask", "broadcast", "ptp"]
)


def test_collector_initialization():
    collector = NetworkCollector()
    assert collector._sample_count == 0
    assert collector.last_sampled_at is None
    assert collector.initialized_at.tzinfo is not None
    assert collector._last_aggregate_time is None
    assert collector._last_aggregate_io is None
    assert collector._last_pernic_io == {}
    assert collector._last_pernic_time == {}


def test_calculate_rate_logic():
    # None counter inputs
    assert NetworkCollector.calculate_rate(None, 100, 1.0) is None
    assert NetworkCollector.calculate_rate(100, None, 1.0) is None

    # Zero or negative elapsed time
    assert NetworkCollector.calculate_rate(100, 200, 0.0) is None
    assert NetworkCollector.calculate_rate(100, 200, -1.0) is None

    # Counter reset or rollover (curr < prev)
    assert NetworkCollector.calculate_rate(500, 200, 1.0) is None

    # Normal delta calculation
    # 2048 bytes in 2 seconds = 1024.0 bytes/sec
    assert NetworkCollector.calculate_rate(1000, 3048, 2.0) == 1024.0

    # Zero delta (no traffic)
    assert NetworkCollector.calculate_rate(1000, 1000, 1.0) == 0.0


def test_calculate_throughput_logic():
    io_baseline = NetworkIOCountersMetrics(
        bytes_sent=1000,
        bytes_recv=2000,
        packets_sent=10,
        packets_recv=20,
        errin=0,
        errout=0,
        dropin=0,
        dropout=0,
    )
    io_next = NetworkIOCountersMetrics(
        bytes_sent=2024,  # +1024 bytes
        bytes_recv=4048,  # +2048 bytes
        packets_sent=15,
        packets_recv=25,
        errin=0,
        errout=0,
        dropin=0,
        dropout=0,
    )

    # curr_io is None
    assert NetworkCollector.calculate_throughput(io_baseline, None, 1.0) is None

    # prev_io is None (first sample) -> throughput rates must be None
    first_tp = NetworkCollector.calculate_throughput(None, io_baseline, 1.0)
    assert isinstance(first_tp, NetworkThroughputMetrics)
    assert first_tp.bytes_sent_per_sec is None
    assert first_tp.bytes_recv_per_sec is None

    # Zero elapsed time -> throughput rates must be None
    zero_time_tp = NetworkCollector.calculate_throughput(io_baseline, io_next, 0.0)
    assert zero_time_tp.bytes_sent_per_sec is None
    assert zero_time_tp.bytes_recv_per_sec is None

    # Valid subsequent sample: elapsed = 1.0s
    tp = NetworkCollector.calculate_throughput(io_baseline, io_next, 1.0)
    assert tp is not None
    assert tp.bytes_sent_per_sec == 1024.0
    assert tp.bytes_recv_per_sec == 2048.0

    # Partial counter reset (bytes_sent reset, bytes_recv increased)
    io_reset = NetworkIOCountersMetrics(
        bytes_sent=500,  # reset from 1000
        bytes_recv=3000,  # +1000 from 2000
        packets_sent=5,
        packets_recv=30,
        errin=0,
        errout=0,
        dropin=0,
        dropout=0,
    )
    tp_reset = NetworkCollector.calculate_throughput(io_baseline, io_reset, 1.0)
    assert tp_reset.bytes_sent_per_sec is None
    assert tp_reset.bytes_recv_per_sec == 1000.0


def test_get_network_io_counters_valid():
    raw_io = MockNetIO(
        bytes_sent=5000,
        bytes_recv=10000,
        packets_sent=50,
        packets_recv=100,
        errin=1,
        errout=2,
        dropin=3,
        dropout=4,
    )
    with patch("psutil.net_io_counters", return_value=raw_io):
        collector = NetworkCollector()
        io = collector.get_network_io_counters()

    assert isinstance(io, NetworkIOCountersMetrics)
    assert io.bytes_sent == 5000
    assert io.bytes_recv == 10000
    assert io.packets_sent == 50
    assert io.packets_recv == 100
    assert io.errin == 1
    assert io.errout == 2
    assert io.dropin == 3
    assert io.dropout == 4
    assert collector._sample_count == 1
    assert collector.last_sampled_at is not None


def test_get_network_io_counters_none_unavailable():
    with patch("psutil.net_io_counters", return_value=None):
        collector = NetworkCollector()
        io = collector.get_network_io_counters()

    assert io is None
    assert collector._sample_count == 1


def test_get_network_io_counters_psutil_error():
    with patch("psutil.net_io_counters", side_effect=psutil.Error("Simulated error")):
        collector = NetworkCollector()
        io = collector.get_network_io_counters()

    assert io is None


def test_get_network_io_counters_os_error():
    with patch("psutil.net_io_counters", side_effect=OSError("OS error")):
        collector = NetworkCollector()
        io = collector.get_network_io_counters()

    assert io is None


def test_get_network_interfaces_valid_multiple():
    mock_stats = {
        "eth0": MockNicStats(
            isup=True, duplex=2, speed=1000, mtu=1500, flags="up,broadcast"
        ),
        "lo": MockNicStats(
            isup=True, duplex=0, speed=0, mtu=65536, flags="up,loopback"
        ),
    }
    mock_pernic = {
        "eth0": MockNetIO(
            bytes_sent=1000,
            bytes_recv=2000,
            packets_sent=10,
            packets_recv=20,
            errin=0,
            errout=0,
            dropin=0,
            dropout=0,
        ),
        "lo": MockNetIO(
            bytes_sent=500,
            bytes_recv=500,
            packets_sent=5,
            packets_recv=5,
            errin=0,
            errout=0,
            dropin=0,
            dropout=0,
        ),
    }
    mock_addrs = {
        "eth0": [
            MockNicAddr(
                family=2, address="192.168.1.50", netmask=None, broadcast=None, ptp=None
            ),
            MockNicAddr(
                family=17,
                address="00:11:22:33:44:55",
                netmask=None,
                broadcast=None,
                ptp=None,
            ),
        ],
        "lo": [
            MockNicAddr(
                family=2, address="127.0.0.1", netmask=None, broadcast=None, ptp=None
            ),
        ],
    }

    with (
        patch("psutil.net_if_stats", return_value=mock_stats),
        patch("psutil.net_io_counters", return_value=mock_pernic),
        patch("psutil.net_if_addrs", return_value=mock_addrs),
    ):
        collector = NetworkCollector()
        interfaces = collector.get_network_interfaces()

    assert len(interfaces) == 2
    # Deterministic alphabetical ordering: eth0 then lo
    assert interfaces[0].name == "eth0"
    assert interfaces[0].is_up is True
    assert interfaces[0].speed == 1000
    assert interfaces[0].mtu == 1500
    assert "MAC: 00:11:22:33:44:55" in interfaces[0].addresses
    assert "IPv4" in interfaces[0].addresses
    # Confirm private IP was not leaked directly into addresses
    assert "192.168.1.50" not in interfaces[0].addresses
    assert interfaces[0].io_counters.bytes_sent == 1000
    assert interfaces[0].throughput.bytes_sent_per_sec is None  # First sample

    assert interfaces[1].name == "lo"
    assert interfaces[1].is_up is True
    assert interfaces[1].speed is None  # 0 converted to None
    assert interfaces[1].mtu == 65536
    assert interfaces[1].addresses == ["IPv4"]
    assert interfaces[1].io_counters.bytes_sent == 500


def test_get_network_interfaces_empty():
    with (
        patch("psutil.net_if_stats", return_value={}),
        patch("psutil.net_io_counters", return_value={}),
        patch("psutil.net_if_addrs", return_value={}),
    ):
        collector = NetworkCollector()
        interfaces = collector.get_network_interfaces()

    assert interfaces == []


def test_get_network_interfaces_unsupported_stats():
    mock_stats = {
        "eth0": MockNicStats(isup=False, duplex=0, speed=-1, mtu=-1, flags=""),
    }
    with (
        patch("psutil.net_if_stats", return_value=mock_stats),
        patch("psutil.net_io_counters", return_value={}),
        patch("psutil.net_if_addrs", return_value={}),
    ):
        collector = NetworkCollector()
        interfaces = collector.get_network_interfaces()

    assert len(interfaces) == 1
    assert interfaces[0].name == "eth0"
    assert interfaces[0].is_up is False
    assert interfaces[0].speed is None
    assert interfaces[0].mtu is None
    assert interfaces[0].io_counters is None
    assert interfaces[0].throughput is None


def test_get_network_interfaces_psutil_exceptions_handled():
    with (
        patch("psutil.net_if_stats", side_effect=psutil.Error("Simulated error")),
        patch("psutil.net_io_counters", side_effect=OSError("Simulated OS error")),
        patch(
            "psutil.net_if_addrs", side_effect=AttributeError("Simulated attr error")
        ),
    ):
        collector = NetworkCollector()
        interfaces = collector.get_network_interfaces()

    assert interfaces == []


def test_get_network_metrics_first_reading_throughput_unavailable():
    mock_agg = MockNetIO(
        bytes_sent=1000,
        bytes_recv=2000,
        packets_sent=10,
        packets_recv=20,
        errin=0,
        errout=0,
        dropin=0,
        dropout=0,
    )
    mock_pernic = {
        "eth0": mock_agg,
    }
    mock_stats = {
        "eth0": MockNicStats(isup=True, duplex=2, speed=1000, mtu=1500, flags=""),
    }

    with (
        patch("psutil.net_io_counters", side_effect=[mock_agg, mock_pernic]),
        patch("psutil.net_if_stats", return_value=mock_stats),
        patch("psutil.net_if_addrs", return_value={}),
    ):
        collector = NetworkCollector()
        metrics = collector.get_network_metrics()

    assert isinstance(metrics, NetworkMetrics)
    assert metrics.io_counters.bytes_sent == 1000
    # First reading: throughput rates must be None, not fabricated zeros
    assert metrics.throughput is not None
    assert metrics.throughput.bytes_sent_per_sec is None
    assert metrics.throughput.bytes_recv_per_sec is None
    assert len(metrics.interfaces) == 1
    assert metrics.interfaces[0].throughput.bytes_sent_per_sec is None
    assert metrics.interfaces[0].throughput.bytes_recv_per_sec is None


def test_get_network_metrics_subsequent_reading_throughput_calculated():
    mock_agg_1 = MockNetIO(
        bytes_sent=10000,
        bytes_recv=20000,
        packets_sent=100,
        packets_recv=200,
        errin=0,
        errout=0,
        dropin=0,
        dropout=0,
    )
    mock_pernic_1 = {"eth0": mock_agg_1}

    mock_agg_2 = MockNetIO(
        bytes_sent=15000,  # +5000 bytes
        bytes_recv=30000,  # +10000 bytes
        packets_sent=150,
        packets_recv=300,
        errin=0,
        errout=0,
        dropin=0,
        dropout=0,
    )
    mock_pernic_2 = {"eth0": mock_agg_2}

    mock_stats = {
        "eth0": MockNicStats(isup=True, duplex=2, speed=1000, mtu=1500, flags=""),
    }

    collector = NetworkCollector()

    # Reading 1 at t=100.0s
    with (
        patch("psutil.net_io_counters", side_effect=[mock_agg_1, mock_pernic_1]),
        patch("psutil.net_if_stats", return_value=mock_stats),
        patch("psutil.net_if_addrs", return_value={}),
        patch("time.monotonic", return_value=100.0),
    ):
        m1 = collector.get_network_metrics()
        assert m1.throughput.bytes_sent_per_sec is None
        assert m1.throughput.bytes_recv_per_sec is None

    # Reading 2 at t=102.0s (delta_t = 2.0s)
    with (
        patch("psutil.net_io_counters", side_effect=[mock_agg_2, mock_pernic_2]),
        patch("psutil.net_if_stats", return_value=mock_stats),
        patch("psutil.net_if_addrs", return_value={}),
        patch("time.monotonic", return_value=102.0),
    ):
        m2 = collector.get_network_metrics()
        # 5000 B / 2.0s = 2500.0 B/s; 10000 B / 2.0s = 5000.0 B/s
        assert m2.throughput.bytes_sent_per_sec == 2500.0
        assert m2.throughput.bytes_recv_per_sec == 5000.0
        assert m2.interfaces[0].throughput.bytes_sent_per_sec == 2500.0
        assert m2.interfaces[0].throughput.bytes_recv_per_sec == 5000.0


def test_get_network_metrics_counter_reset_handling():
    mock_agg_1 = MockNetIO(
        bytes_sent=100000,
        bytes_recv=200000,
        packets_sent=1000,
        packets_recv=2000,
        errin=0,
        errout=0,
        dropin=0,
        dropout=0,
    )
    mock_agg_reset = MockNetIO(
        bytes_sent=500,  # Reset from 100000
        bytes_recv=1000,  # Reset from 200000
        packets_sent=5,
        packets_recv=10,
        errin=0,
        errout=0,
        dropin=0,
        dropout=0,
    )

    collector = NetworkCollector()

    with (
        patch("psutil.net_io_counters", side_effect=[mock_agg_1, {}]),
        patch("psutil.net_if_stats", return_value={}),
        patch("psutil.net_if_addrs", return_value={}),
        patch("time.monotonic", return_value=100.0),
    ):
        collector.get_network_metrics()

    # Reading 2 has reset counters
    with (
        patch("psutil.net_io_counters", side_effect=[mock_agg_reset, {}]),
        patch("psutil.net_if_stats", return_value={}),
        patch("psutil.net_if_addrs", return_value={}),
        patch("time.monotonic", return_value=101.0),
    ):
        m2 = collector.get_network_metrics()
        assert m2.throughput.bytes_sent_per_sec is None
        assert m2.throughput.bytes_recv_per_sec is None


def test_get_network_metrics_zero_elapsed_time():
    mock_agg = MockNetIO(
        bytes_sent=1000,
        bytes_recv=2000,
        packets_sent=10,
        packets_recv=20,
        errin=0,
        errout=0,
        dropin=0,
        dropout=0,
    )

    collector = NetworkCollector()

    with (
        patch("psutil.net_io_counters", side_effect=[mock_agg, {}]),
        patch("psutil.net_if_stats", return_value={}),
        patch("psutil.net_if_addrs", return_value={}),
        patch("time.monotonic", return_value=100.0),
    ):
        collector.get_network_metrics()

    # Same monotonic timestamp (zero elapsed time)
    with (
        patch("psutil.net_io_counters", side_effect=[mock_agg, {}]),
        patch("psutil.net_if_stats", return_value={}),
        patch("psutil.net_if_addrs", return_value={}),
        patch("time.monotonic", return_value=100.0),
    ):
        m2 = collector.get_network_metrics()
        assert m2.throughput.bytes_sent_per_sec is None
        assert m2.throughput.bytes_recv_per_sec is None


def test_get_network_metrics_interface_disappearance_and_reappearance():
    stats_both = {
        "eth0": MockNicStats(isup=True, duplex=2, speed=1000, mtu=1500, flags=""),
        "eth1": MockNicStats(isup=True, duplex=2, speed=1000, mtu=1500, flags=""),
    }
    io_both = {
        "eth0": MockNetIO(1000, 1000, 10, 10, 0, 0, 0, 0),
        "eth1": MockNetIO(2000, 2000, 20, 20, 0, 0, 0, 0),
    }

    collector = NetworkCollector()

    # Sample 1: eth0 and eth1 present
    with (
        patch("psutil.net_io_counters", side_effect=[None, io_both]),
        patch("psutil.net_if_stats", return_value=stats_both),
        patch("psutil.net_if_addrs", return_value={}),
        patch("time.monotonic", return_value=10.0),
    ):
        m1 = collector.get_network_metrics()
        assert len(m1.interfaces) == 2
        assert "eth1" in collector._last_pernic_io

    # Sample 2: eth1 disappeared
    stats_eth0_only = {
        "eth0": MockNicStats(isup=True, duplex=2, speed=1000, mtu=1500, flags=""),
    }
    io_eth0_only = {
        "eth0": MockNetIO(2000, 2000, 20, 20, 0, 0, 0, 0),
    }
    with (
        patch("psutil.net_io_counters", side_effect=[None, io_eth0_only]),
        patch("psutil.net_if_stats", return_value=stats_eth0_only),
        patch("psutil.net_if_addrs", return_value={}),
        patch("time.monotonic", return_value=11.0),
    ):
        m2 = collector.get_network_metrics()
        assert len(m2.interfaces) == 1
        assert m2.interfaces[0].name == "eth0"
        assert m2.interfaces[0].throughput.bytes_sent_per_sec == 1000.0
        # eth1 should be purged from state
        assert "eth1" not in collector._last_pernic_io

    # Sample 3: eth1 reappears with new counters
    io_both_reappear = {
        "eth0": MockNetIO(3000, 3000, 30, 30, 0, 0, 0, 0),
        "eth1": MockNetIO(5000, 5000, 50, 50, 0, 0, 0, 0),
    }
    with (
        patch("psutil.net_io_counters", side_effect=[None, io_both_reappear]),
        patch("psutil.net_if_stats", return_value=stats_both),
        patch("psutil.net_if_addrs", return_value={}),
        patch("time.monotonic", return_value=12.0),
    ):
        m3 = collector.get_network_metrics()
        assert len(m3.interfaces) == 2
        eth0 = next(i for i in m3.interfaces if i.name == "eth0")
        eth1 = next(i for i in m3.interfaces if i.name == "eth1")
        assert eth0.throughput.bytes_sent_per_sec == 1000.0
        # Reappeared eth1 gets first-reading unavailable throughput
        assert eth1.throughput.bytes_sent_per_sec is None
        assert eth1.throughput.bytes_recv_per_sec is None


def test_get_network_metrics_timestamp_consistency():
    collector = NetworkCollector()
    metrics = collector.get_network_metrics()
    assert metrics.timestamp == collector.last_sampled_at


def test_collector_repeated_calls_increment_sample_count():
    collector = NetworkCollector()
    assert collector._sample_count == 0

    with (
        patch("psutil.net_io_counters", return_value=None),
        patch("psutil.net_if_stats", return_value={}),
        patch("psutil.net_if_addrs", return_value={}),
    ):
        collector.get_network_io_counters()
        assert collector._sample_count == 1

        collector.get_network_interfaces()
        assert collector._sample_count == 2

        collector.get_network_metrics()
        assert collector._sample_count == 3


def test_collector_instances_do_not_share_state():
    c1 = NetworkCollector()
    c2 = NetworkCollector()

    with (
        patch("psutil.net_io_counters", return_value=None),
        patch("psutil.net_if_stats", return_value={}),
        patch("psutil.net_if_addrs", return_value={}),
    ):
        c1.get_network_metrics()

    assert c1._sample_count == 1
    assert c1.last_sampled_at is not None
    assert c2._sample_count == 0
    assert c2.last_sampled_at is None


def test_collector_real_system_smoke():
    """Live smoke test on host verifying network collector behavior."""
    collector = NetworkCollector()

    io = collector.get_network_io_counters()
    if io is not None:
        assert isinstance(io, NetworkIOCountersMetrics)
        assert io.bytes_sent >= 0
        assert io.bytes_recv >= 0
        assert io.packets_sent >= 0
        assert io.packets_recv >= 0

    interfaces = collector.get_network_interfaces()
    assert isinstance(interfaces, list)
    for iface in interfaces:
        assert isinstance(iface, NetworkInterfaceMetrics)
        assert isinstance(iface.name, str)
        assert isinstance(iface.is_up, bool)
        if iface.speed is not None:
            assert iface.speed >= 0
        if iface.mtu is not None:
            assert iface.mtu >= 0
        if iface.addresses is not None:
            assert isinstance(iface.addresses, list)
        if iface.io_counters is not None:
            assert iface.io_counters.bytes_sent >= 0

    # First metrics sample: throughput fields should be None
    m1 = collector.get_network_metrics()
    assert isinstance(m1, NetworkMetrics)
    assert m1.timestamp.tzinfo is not None

    # Subsequent metrics sample
    m2 = collector.get_network_metrics()
    assert isinstance(m2, NetworkMetrics)
    assert collector._sample_count >= 3
