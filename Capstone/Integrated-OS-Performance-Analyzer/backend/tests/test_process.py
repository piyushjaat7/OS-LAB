from collections import namedtuple
from unittest.mock import MagicMock, patch

import psutil

from app.collectors.process import ProcessCollector
from app.schemas.metrics import (
    CPUMetrics,
    ProcessCollectionMetrics,
    ProcessMetrics,
    SystemMetrics,
)

MockMemInfo = namedtuple("pmem", ["rss", "vms"])


class MockProcess:
    """Mock psutil Process helper for deterministic unit testing."""

    def __init__(
        self,
        pid: int = 100,
        name: str = "test_proc",
        status: str = "running",
        rss: int = 50000000,
        vms: int = 100000000,
        mem_percent: float = 2.5,
        num_threads: int = 4,
        create_time: float = 1700000000.0,
        username: str = "user1",
        cpu_returns: list[float] | None = None,
    ):
        self.pid = pid
        self._name = name
        self._status = status
        self._mem_info = MockMemInfo(rss=rss, vms=vms)
        self._mem_percent = mem_percent
        self._num_threads = num_threads
        self._create_time = create_time
        self._username = username
        self._cpu_returns = (
            list(cpu_returns) if cpu_returns is not None else [0.0, 25.0]
        )
        self._cpu_idx = 0

    def name(self) -> str:
        return self._name

    def status(self) -> str:
        return self._status

    def memory_info(self) -> MockMemInfo:
        return self._mem_info

    def memory_percent(self) -> float:
        return self._mem_percent

    def num_threads(self) -> int:
        return self._num_threads

    def create_time(self) -> float:
        return self._create_time

    def username(self) -> str:
        return self._username

    def is_running(self) -> bool:
        return True

    def cpu_percent(self, interval: float | None = None) -> float:
        if self._cpu_idx < len(self._cpu_returns):
            val = self._cpu_returns[self._cpu_idx]
            self._cpu_idx += 1
            return val
        return self._cpu_returns[-1]


def test_collector_initialization():
    collector = ProcessCollector()
    assert collector._sample_count == 0
    assert collector.last_sampled_at is None
    assert collector.initialized_at.tzinfo is not None
    assert collector._proc_cache == {}


def test_get_process_metrics_valid():
    mock_p = MockProcess(
        pid=123,
        name="/usr/bin/daemon",
        status="running",
        rss=10485760,
        vms=20971520,
        mem_percent=1.5,
        num_threads=2,
        create_time=1700000000.0,
        username="daemon_user",
        cpu_returns=[0.0, 15.5],
    )

    with patch("psutil.Process", return_value=mock_p):
        collector = ProcessCollector()
        # First reading: CPU baseline primed, returns None
        p1 = collector.get_process_metrics(123)
        assert isinstance(p1, ProcessMetrics)
        assert p1.pid == 123
        assert p1.name == "daemon"  # Path stripped to basename
        assert p1.status == "running"
        assert p1.memory_rss == 10485760
        assert p1.memory_vms == 20971520
        assert p1.memory_percent == 1.5
        assert p1.num_threads == 2
        assert p1.create_time == 1700000000.0
        assert p1.username == "daemon_user"
        assert p1.cpu_percent is None
        assert p1.timestamp.tzinfo is not None

        # Subsequent reading: valid CPU percentage computed
        p2 = collector.get_process_metrics(123)
        assert isinstance(p2, ProcessMetrics)
        assert p2.cpu_percent == 15.5


def test_cpu_first_reading_semantics_and_subsequent_reading():
    mock_p = MockProcess(pid=456, cpu_returns=[0.0, 42.0])

    with patch("psutil.Process", return_value=mock_p):
        collector = ProcessCollector()

        # Call 1: Baseline initialization -> None
        m1 = collector.get_process_metrics(456)
        assert m1 is not None
        assert m1.cpu_percent is None

        # Call 2: Second measurement -> 42.0
        m2 = collector.get_process_metrics(456)
        assert m2 is not None
        assert m2.cpu_percent == 42.0


def test_cpu_genuine_zero_utilization():
    mock_p = MockProcess(pid=789, cpu_returns=[0.0, 0.0])

    with patch("psutil.Process", return_value=mock_p):
        collector = ProcessCollector()

        # Call 1: Baseline -> None
        m1 = collector.get_process_metrics(789)
        assert m1.cpu_percent is None

        # Call 2: Genuine zero utilization -> 0.0
        m2 = collector.get_process_metrics(789)
        assert m2.cpu_percent == 0.0


def test_pid_reuse_resets_cpu_baseline():
    mock_p_old = MockProcess(pid=999, create_time=100.0, cpu_returns=[0.0, 50.0])
    mock_p_new = MockProcess(pid=999, create_time=200.0, cpu_returns=[0.0, 75.0])

    collector = ProcessCollector()

    # Call 1 on old process (create_time 100.0) -> None
    with patch("psutil.Process", return_value=mock_p_old):
        m1 = collector.get_process_metrics(999)
        assert m1.cpu_percent is None

    # Call 2 on old process -> 50.0
    with patch("psutil.Process", return_value=mock_p_old):
        m2 = collector.get_process_metrics(999)
        assert m2.cpu_percent == 50.0

    # Process died and PID 999 was reused for a new process (create_time 200.0)
    # Must reset baseline -> None
    with patch("psutil.Process", return_value=mock_p_new):
        m3 = collector.get_process_metrics(999)
        assert m3.cpu_percent is None


def test_get_process_metrics_missing_process():
    with patch("psutil.Process", side_effect=psutil.NoSuchProcess(pid=99999)):
        collector = ProcessCollector()
        result = collector.get_process_metrics(99999)

    assert result is None


def test_get_process_metrics_access_denied():
    with patch("psutil.Process", side_effect=psutil.AccessDenied(pid=1)):
        collector = ProcessCollector()
        result = collector.get_process_metrics(1)

    assert result is None


def test_get_process_metrics_zombie_process():
    with patch("psutil.Process", side_effect=psutil.ZombieProcess(pid=2)):
        collector = ProcessCollector()
        result = collector.get_process_metrics(2)

    assert result is None


def test_get_all_process_metrics_multiple():
    p1 = MockProcess(pid=10, name="init", rss=1000, vms=2000)
    p2 = MockProcess(pid=20, name="bash", rss=5000, vms=8000)

    with patch("psutil.process_iter", return_value=[p1, p2]):
        collector = ProcessCollector()
        processes = collector.get_all_process_metrics()

    assert len(processes) == 2
    assert processes[0].pid == 10
    assert processes[0].name == "init"
    assert processes[1].pid == 20
    assert processes[1].name == "bash"
    assert collector._sample_count == 1
    assert collector.last_sampled_at is not None


def test_get_all_process_metrics_empty():
    with patch("psutil.process_iter", return_value=[]):
        collector = ProcessCollector()
        processes = collector.get_all_process_metrics()

    assert processes == []


def test_process_disappearing_during_enumeration():
    p_valid = MockProcess(pid=10, name="init")
    p_disappearing = MockProcess(pid=20, name="temp")
    # Simulate disappearing when memory_info is called
    p_disappearing.memory_info = MagicMock(
        side_effect=psutil.NoSuchProcess(pid=20, msg="Process terminated")
    )

    with patch("psutil.process_iter", return_value=[p_valid, p_disappearing]):
        collector = ProcessCollector()
        processes = collector.get_all_process_metrics()

    # The disappearing process is skipped cleanly without aborting collection
    assert len(processes) == 1
    assert processes[0].pid == 10


def test_stale_pid_sampling_state_cleanup():
    p1 = MockProcess(pid=100, name="p1")
    p2 = MockProcess(pid=200, name="p2")

    collector = ProcessCollector()

    # Call 1: Both p1 and p2 exist
    with patch("psutil.process_iter", return_value=[p1, p2]):
        collector.get_all_process_metrics()
        assert 100 in collector._proc_cache
        assert 200 in collector._proc_cache

    # Call 2: p2 has terminated, only p1 exists
    with patch("psutil.process_iter", return_value=[p1]):
        collector.get_all_process_metrics()
        assert 100 in collector._proc_cache
        # p2 must be cleaned up from cache
        assert 200 not in collector._proc_cache


def test_get_process_collection_metrics_combined():
    p1 = MockProcess(pid=10, name="init")
    p2 = MockProcess(pid=20, name="bash")

    with patch("psutil.process_iter", return_value=[p1, p2]):
        collector = ProcessCollector()
        collection = collector.get_process_collection_metrics()

    assert isinstance(collection, ProcessCollectionMetrics)
    assert collection.total_processes == 2
    assert len(collection.processes) == 2
    assert collection.timestamp.tzinfo is not None


def test_collector_instances_do_not_share_state():
    c1 = ProcessCollector()
    c2 = ProcessCollector()

    p = MockProcess(pid=100)

    with patch("psutil.process_iter", return_value=[p]):
        c1.get_all_process_metrics()

    assert c1._sample_count == 1
    assert 100 in c1._proc_cache
    assert c2._sample_count == 0
    assert c2._proc_cache == {}


def test_repeated_calls_increment_sample_count():
    p = MockProcess(pid=1)

    with (
        patch("psutil.Process", return_value=p),
        patch("psutil.process_iter", return_value=[p]),
    ):
        collector = ProcessCollector()
        assert collector._sample_count == 0

        collector.get_process_metrics(1)
        assert collector._sample_count == 1

        collector.get_all_process_metrics()
        assert collector._sample_count == 2

        collector.get_process_collection_metrics()
        assert collector._sample_count == 3


def test_system_metrics_integration_with_processes():
    p = ProcessMetrics(
        pid=1,
        name="init",
        status="running",
        memory_rss=1000,
        memory_vms=2000,
    )
    collection = ProcessCollectionMetrics(processes=[p], total_processes=1)
    cpu = CPUMetrics(
        usage_percent=10.0,
        per_core_usage=[10.0],
        physical_cores=1,
        logical_cores=1,
    )

    system_metrics = SystemMetrics(cpu=cpu, processes=collection)
    assert system_metrics.processes is not None
    assert system_metrics.processes.total_processes == 1
    assert system_metrics.processes.processes[0].name == "init"


def test_collector_real_system_smoke():
    """Live smoke test on host verifying process collector behavior."""
    collector = ProcessCollector()

    # Test single process query on current python process
    current_pid = psutil.Process().pid
    proc_metrics = collector.get_process_metrics(current_pid)
    assert proc_metrics is not None
    assert isinstance(proc_metrics, ProcessMetrics)
    assert proc_metrics.pid == current_pid
    assert proc_metrics.memory_rss >= 0
    assert proc_metrics.memory_vms >= 0
    assert proc_metrics.num_threads >= 1
    # First reading: CPU is None
    assert proc_metrics.cpu_percent is None

    # Second reading on same PID: CPU is numeric
    proc_metrics_2 = collector.get_process_metrics(current_pid)
    assert proc_metrics_2 is not None
    assert proc_metrics_2.cpu_percent is not None
    assert proc_metrics_2.cpu_percent >= 0.0

    # Test collection query
    collection = collector.get_process_collection_metrics()
    assert isinstance(collection, ProcessCollectionMetrics)
    assert collection.total_processes > 0
    assert len(collection.processes) == collection.total_processes
    assert collection.timestamp.tzinfo is not None
