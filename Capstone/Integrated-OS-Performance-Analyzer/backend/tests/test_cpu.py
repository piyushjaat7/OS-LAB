import time
from collections import namedtuple
from unittest.mock import patch

import psutil

from app.collectors.cpu import CPUCollector
from app.schemas.metrics import CPUMetrics

MockFreq = namedtuple("scpufreq", ["current", "min", "max"])
MockTimes = namedtuple(
    "scputimes",
    [
        "user",
        "nice",
        "system",
        "idle",
        "iowait",
        "irq",
        "softirq",
        "steal",
        "guest",
        "guest_nice",
    ],
    defaults=[0.0] * 10,
)


def test_initial_cpu_reading_is_unavailable():
    # Initial measurement before CPU time has advanced returns None
    t0 = MockTimes(user=10.0, system=5.0, idle=100.0)
    per_c0 = [
        MockTimes(user=5.0, system=2.5, idle=50.0),
        MockTimes(user=5.0, system=2.5, idle=50.0),
    ]

    def mock_times(percpu=False):
        return per_c0 if percpu else t0

    with (
        patch("psutil.cpu_times", side_effect=mock_times),
        patch("psutil.cpu_count", side_effect=[4, 2]),
        patch("psutil.cpu_freq", return_value=None),
    ):
        collector = CPUCollector()
        metrics = collector.get_cpu_metrics()

    assert isinstance(metrics, CPUMetrics)
    assert metrics.usage_percent is None
    assert metrics.per_core_usage is None
    assert metrics.logical_cores == 4
    assert metrics.physical_cores == 2


def test_subsequent_valid_reading_returns_numeric_values():
    t0 = MockTimes(user=10.0, system=5.0, idle=100.0)
    per_c0 = [
        MockTimes(user=5.0, system=2.5, idle=50.0),
        MockTimes(user=5.0, system=2.5, idle=50.0),
    ]

    # Advance by 10s total (user +2, system +1, busy = 3s -> 30%)
    t1 = MockTimes(user=12.0, system=6.0, idle=107.0)
    per_c1 = [
        MockTimes(user=7.0, system=2.5, idle=58.0),
        MockTimes(user=5.0, system=3.5, idle=59.0),
    ]

    call_count = 0

    def mock_times(percpu=False):
        nonlocal call_count
        call_count += 1
        # Calls 1-2: during __init__ (t0)
        # Calls 3-4: first get_cpu_metrics (t0, delta = 0 -> None)
        # Calls 5-6: second get_cpu_metrics (t1, delta = 10 -> 30%)
        if call_count <= 4:
            return per_c0 if percpu else t0
        return per_c1 if percpu else t1

    with (
        patch("psutil.cpu_times", side_effect=mock_times),
        patch("psutil.cpu_count", return_value=2),
        patch(
            "psutil.cpu_freq",
            return_value=MockFreq(current=2500.0, min=800.0, max=3200.0),
        ),
    ):
        collector = CPUCollector()

        # Initial call before interval elapsed
        m1 = collector.get_cpu_metrics()
        assert m1.usage_percent is None
        assert m1.per_core_usage is None

        # Subsequent call with advanced CPU ticks
        m2 = collector.get_cpu_metrics()
        assert m2.usage_percent == 30.0
        assert m2.per_core_usage is not None
        assert len(m2.per_core_usage) == 2
        assert m2.per_core_usage == [20.0, 10.0]
        assert m2.frequency is not None
        assert m2.frequency.current == 2500.0


def test_genuine_zero_utilization_remains_zero():
    t0 = MockTimes(user=10.0, system=5.0, idle=100.0)
    per_c0 = [MockTimes(user=5.0, system=2.5, idle=50.0)]

    # 10s of idle time elapsed with zero busy change
    t_idle = MockTimes(user=10.0, system=5.0, idle=110.0)
    per_c_idle = [MockTimes(user=5.0, system=2.5, idle=60.0)]

    call_count = 0

    def mock_times(percpu=False):
        nonlocal call_count
        call_count += 1
        # Calls 1-2: during __init__ (t0)
        # Calls 3-4: first get_cpu_metrics (t0, returns None)
        # Calls 5-6: second get_cpu_metrics (t_idle, returns 0.0)
        if call_count <= 4:
            return per_c0 if percpu else t0
        return per_c_idle if percpu else t_idle

    with (
        patch("psutil.cpu_times", side_effect=mock_times),
        patch("psutil.cpu_count", return_value=1),
        patch("psutil.cpu_freq", return_value=None),
    ):
        collector = CPUCollector()
        m1 = collector.get_cpu_metrics()
        assert m1.usage_percent is None
        assert m1.per_core_usage is None

        m2 = collector.get_cpu_metrics()
        assert m2.usage_percent == 0.0
        assert m2.usage_percent is not None
        assert m2.per_core_usage == [0.0]


def test_cpu_collector_missing_frequency_returns_none():
    t0 = MockTimes(user=10.0, system=5.0, idle=100.0)

    def mock_times(percpu=False):
        return [] if percpu else t0

    with (
        patch("psutil.cpu_times", side_effect=mock_times),
        patch("psutil.cpu_count", return_value=2),
        patch("psutil.cpu_freq", return_value=None),
    ):
        collector = CPUCollector()
        metrics = collector.get_cpu_metrics()

    assert metrics.frequency is None


def test_cpu_collector_frequency_attribute_error_handled():
    t0 = MockTimes(user=10.0, system=5.0, idle=100.0)

    def mock_times(percpu=False):
        return [] if percpu else t0

    with (
        patch("psutil.cpu_times", side_effect=mock_times),
        patch("psutil.cpu_count", return_value=2),
        patch(
            "psutil.cpu_freq",
            side_effect=AttributeError("cpu_freq not supported"),
        ),
    ):
        collector = CPUCollector()
        metrics = collector.get_cpu_metrics()

    assert metrics.frequency is None


def test_cpu_collector_frequency_access_denied_handled():
    t0 = MockTimes(user=10.0, system=5.0, idle=100.0)

    def mock_times(percpu=False):
        return [] if percpu else t0

    with (
        patch("psutil.cpu_times", side_effect=mock_times),
        patch("psutil.cpu_count", return_value=2),
        patch("psutil.cpu_freq", side_effect=psutil.AccessDenied()),
    ):
        collector = CPUCollector()
        metrics = collector.get_cpu_metrics()

    assert metrics.frequency is None


def test_cpu_collector_physical_cores_none_fallback():
    t0 = MockTimes(user=10.0, system=5.0, idle=100.0)

    def mock_times(percpu=False):
        return [] if percpu else t0

    def mock_cpu_count(logical=True):
        return 2 if logical else None

    with (
        patch("psutil.cpu_times", side_effect=mock_times),
        patch("psutil.cpu_count", side_effect=mock_cpu_count),
        patch("psutil.cpu_freq", return_value=None),
    ):
        collector = CPUCollector()
        metrics = collector.get_cpu_metrics()

    assert metrics.logical_cores == 2
    assert metrics.physical_cores == 2


def test_cpu_collector_psutil_error_fallback():
    # If psutil.cpu_times raises an unexpected psutil.Error or OSError
    with (
        patch("psutil.cpu_times", side_effect=psutil.Error("Read error")),
        patch("psutil.cpu_count", return_value=2),
        patch("psutil.cpu_freq", return_value=None),
    ):
        collector = CPUCollector()
        metrics = collector.get_cpu_metrics()

    assert metrics.usage_percent is None
    assert metrics.per_core_usage is None


def test_repeated_collector_calls_do_not_crash():
    collector = CPUCollector()
    metrics1 = collector.get_cpu_metrics()
    metrics2 = collector.get_cpu_metrics()

    assert isinstance(metrics1, CPUMetrics)
    assert isinstance(metrics2, CPUMetrics)
    assert collector._sample_count == 2
    assert collector.last_sampled_at is not None


def test_collector_instances_do_not_share_mutable_state():
    collector1 = CPUCollector()
    collector2 = CPUCollector()

    assert collector1._sample_count == 0
    assert collector2._sample_count == 0
    assert collector1.last_sampled_at is None
    assert collector2.last_sampled_at is None

    # Sample collector1 only
    collector1.get_cpu_metrics()

    assert collector1._sample_count == 1
    assert collector1.last_sampled_at is not None
    assert collector2._sample_count == 0
    assert collector2.last_sampled_at is None


def test_collector_real_system_first_and_subsequent_reading():
    # Live execution against current host system
    collector = CPUCollector()

    # Immediate call has zero elapsed interval -> returns None
    m_immediate = collector.get_cpu_metrics()
    assert isinstance(m_immediate, CPUMetrics)
    assert m_immediate.usage_percent is None
    assert m_immediate.per_core_usage is None
    assert m_immediate.logical_cores >= 0
    assert m_immediate.physical_cores >= 0

    # Sleep briefly to allow hardware ticks to advance
    time.sleep(0.05)
    m_subsequent = collector.get_cpu_metrics()
    assert isinstance(m_subsequent, CPUMetrics)
    assert m_subsequent.usage_percent is not None
    assert 0.0 <= m_subsequent.usage_percent <= 100.0
    assert m_subsequent.per_core_usage is not None
    for core_usage in m_subsequent.per_core_usage:
        assert 0.0 <= core_usage <= 100.0
