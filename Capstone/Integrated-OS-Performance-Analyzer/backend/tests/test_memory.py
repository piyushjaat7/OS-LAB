from collections import namedtuple
from unittest.mock import patch

import psutil
import pytest

from app.collectors.memory import MemoryCollector
from app.schemas.metrics import (
    MemoryMetrics,
    SwapMemoryMetrics,
    VirtualMemoryMetrics,
)

MockVMem = namedtuple("svmem", ["total", "available", "percent", "used", "free"])
MockSwap = namedtuple("sswap", ["total", "used", "free", "percent", "sin", "sout"])


def test_get_virtual_memory_metrics_valid():
    mock_vm = MockVMem(
        total=16000000000,
        available=10000000000,
        percent=37.5,
        used=6000000000,
        free=8000000000,
    )

    with patch("psutil.virtual_memory", return_value=mock_vm):
        collector = MemoryCollector()
        vm = collector.get_virtual_memory_metrics()

    assert isinstance(vm, VirtualMemoryMetrics)
    assert vm.total == 16000000000
    assert vm.available == 10000000000
    assert vm.used == 6000000000
    assert vm.free == 8000000000
    assert vm.percent == 37.5


def test_get_swap_memory_metrics_valid():
    mock_sm = MockSwap(
        total=4000000000,
        used=1000000000,
        free=3000000000,
        percent=25.0,
        sin=1048576,
        sout=2097152,
    )

    with patch("psutil.swap_memory", return_value=mock_sm):
        collector = MemoryCollector()
        sm = collector.get_swap_memory_metrics()

    assert isinstance(sm, SwapMemoryMetrics)
    assert sm.total == 4000000000
    assert sm.used == 1000000000
    assert sm.free == 3000000000
    assert sm.percent == 25.0
    assert sm.sin == 1048576
    assert sm.sout == 2097152


def test_memory_percentage_boundaries():
    # Boundary 0.0%
    vm_zero = MockVMem(
        total=8000000000,
        available=8000000000,
        percent=0.0,
        used=0,
        free=8000000000,
    )
    # Boundary 100.0%
    vm_full = MockVMem(
        total=8000000000,
        available=0,
        percent=100.0,
        used=8000000000,
        free=0,
    )

    with patch("psutil.virtual_memory", side_effect=[vm_zero, vm_full]):
        collector = MemoryCollector()
        m0 = collector.get_virtual_memory_metrics()
        m100 = collector.get_virtual_memory_metrics()

    assert m0.percent == 0.0
    assert m100.percent == 100.0


def test_zero_swap_memory():
    # Containers or systems with swap disabled
    mock_sm_zero = MockSwap(
        total=0,
        used=0,
        free=0,
        percent=0.0,
        sin=0,
        sout=0,
    )

    with patch("psutil.swap_memory", return_value=mock_sm_zero):
        collector = MemoryCollector()
        sm = collector.get_swap_memory_metrics()

    assert sm.total == 0
    assert sm.used == 0
    assert sm.free == 0
    assert sm.percent == 0.0
    assert sm.sin == 0
    assert sm.sout == 0


def test_swap_memory_none_returns_zeroed():
    with patch("psutil.swap_memory", return_value=None):
        collector = MemoryCollector()
        sm = collector.get_swap_memory_metrics()

    assert sm.total == 0
    assert sm.used == 0
    assert sm.free == 0
    assert sm.percent == 0.0
    assert sm.sin == 0
    assert sm.sout == 0


def test_combined_memory_metrics():
    mock_vm = MockVMem(
        total=8000000000,
        available=5000000000,
        percent=37.5,
        used=3000000000,
        free=4000000000,
    )
    mock_sm = MockSwap(
        total=2000000000,
        used=500000000,
        free=1500000000,
        percent=25.0,
        sin=0,
        sout=0,
    )

    with (
        patch("psutil.virtual_memory", return_value=mock_vm),
        patch("psutil.swap_memory", return_value=mock_sm),
    ):
        collector = MemoryCollector()
        metrics = collector.get_memory_metrics()

    assert isinstance(metrics, MemoryMetrics)
    assert metrics.virtual.total == 8000000000
    assert metrics.virtual.percent == 37.5
    assert metrics.swap.total == 2000000000
    assert metrics.swap.percent == 25.0
    assert metrics.timestamp.tzinfo is not None
    assert collector._sample_count == 1
    assert collector.last_sampled_at is not None


def test_psutil_virtual_memory_error_raises():
    with patch(
        "psutil.virtual_memory",
        side_effect=psutil.Error(),
    ):
        collector = MemoryCollector()
        with pytest.raises(psutil.Error):
            collector.get_virtual_memory_metrics()


def test_psutil_swap_memory_error_raises():
    with patch(
        "psutil.swap_memory",
        side_effect=psutil.Error(),
    ):
        collector = MemoryCollector()
        with pytest.raises(psutil.Error):
            collector.get_swap_memory_metrics()


def test_collector_instances_do_not_share_state():
    mock_vm = MockVMem(
        total=8000000000,
        available=5000000000,
        percent=37.5,
        used=3000000000,
        free=4000000000,
    )

    with patch("psutil.virtual_memory", return_value=mock_vm):
        c1 = MemoryCollector()
        c2 = MemoryCollector()

        assert c1._sample_count == 0
        assert c2._sample_count == 0
        assert c1.last_sampled_at is None
        assert c2.last_sampled_at is None

        c1.get_virtual_memory_metrics()

        assert c1._sample_count == 1
        assert c1.last_sampled_at is not None
        assert c2._sample_count == 0
        assert c2.last_sampled_at is None


def test_repeated_collection_calls_increment_sample_count():
    mock_vm = MockVMem(
        total=8000000000,
        available=5000000000,
        percent=37.5,
        used=3000000000,
        free=4000000000,
    )

    with patch("psutil.virtual_memory", return_value=mock_vm):
        collector = MemoryCollector()
        collector.get_virtual_memory_metrics()
        collector.get_virtual_memory_metrics()

    assert collector._sample_count == 2


def test_collector_real_system():
    # Live execution on host system
    collector = MemoryCollector()
    metrics = collector.get_memory_metrics()

    assert isinstance(metrics, MemoryMetrics)
    assert metrics.virtual.total > 0
    assert metrics.virtual.available >= 0
    assert metrics.virtual.used >= 0
    assert metrics.virtual.free >= 0
    assert 0.0 <= metrics.virtual.percent <= 100.0

    assert metrics.swap.total >= 0
    assert metrics.swap.used >= 0
    assert metrics.swap.free >= 0
    assert 0.0 <= metrics.swap.percent <= 100.0
    assert metrics.swap.sin >= 0
    assert metrics.swap.sout >= 0
    assert metrics.timestamp.tzinfo is not None
