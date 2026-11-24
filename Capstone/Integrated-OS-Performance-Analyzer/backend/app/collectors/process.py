import os
from datetime import UTC, datetime
from typing import Any

import psutil

from app.schemas.metrics import ProcessCollectionMetrics, ProcessMetrics


class ProcessCollector:
    """Cross-platform collector for operating system processes and per-process telemetry."""

    def __init__(self) -> None:
        self.initialized_at: datetime = datetime.now(UTC)
        self.last_sampled_at: datetime | None = None
        self._sample_count: int = 0
        # Maps pid -> (create_time, cached_proc) to maintain CPU baseline across non-blocking calls
        self._proc_cache: dict[int, tuple[float | None, Any]] = {}

    @staticmethod
    def _get_username(proc: Any) -> str | None:
        """Safely retrieve process owner username without crashing on restricted system processes."""
        try:
            user = proc.username()
            return str(user) if user else None
        except (
            psutil.AccessDenied,
            KeyError,
            OSError,
            AttributeError,
        ):
            return None

    def _collect_process(self, proc: Any, now: datetime) -> ProcessMetrics | None:
        """Extract and validate metrics for an individual process.

        CPU First-Reading Semantics:
        - When a process is first encountered, proc.cpu_percent(interval=None) has
          no prior sampling baseline and returns an uninformative 0.0.
          We call cpu_percent(None) to prime the baseline on the process object,
          cache the instance paired with its create_time, and return cpu_percent=None.
        - On subsequent queries where create_time matches, we query the cached instance
          and return the genuine calculated utilization (0.0 or higher).
        - If create_time differs, the OS has recycled the PID for a new process;
          we treat it as a new process, prime it, and return None.
        - If a process terminates during collection (NoSuchProcess / ZombieProcess),
          returns None to avoid collecting dead processes.
        """
        try:
            pid = int(proc.pid)
            if pid < 0:
                return None

            # Retrieve creation time
            try:
                raw_create_time = proc.create_time()
                create_time = (
                    float(raw_create_time) if raw_create_time is not None else None
                )
            except (
                psutil.AccessDenied,
                OSError,
                AttributeError,
            ):
                create_time = None

            # CPU percentage calculation
            if pid not in self._proc_cache:
                # First observation: prime baseline and return None
                try:
                    proc.cpu_percent(None)
                except (
                    psutil.AccessDenied,
                    OSError,
                ):
                    pass
                self._proc_cache[pid] = (create_time, proc)
                cpu_percent = None
            else:
                prev_create_time, cached_proc = self._proc_cache[pid]
                if (
                    create_time is not None
                    and prev_create_time is not None
                    and create_time != prev_create_time
                ):
                    # PID reuse detected: prime new process and return None
                    try:
                        proc.cpu_percent(None)
                    except (
                        psutil.AccessDenied,
                        OSError,
                    ):
                        pass
                    self._proc_cache[pid] = (create_time, proc)
                    cpu_percent = None
                else:
                    # Subsequent valid measurement: query cached process instance
                    target_proc = (
                        cached_proc if hasattr(cached_proc, "cpu_percent") else proc
                    )
                    try:
                        raw_cpu = target_proc.cpu_percent(None)
                        cpu_percent = (
                            round(max(0.0, min(100.0, float(raw_cpu))), 2)
                            if raw_cpu is not None
                            else None
                        )
                    except (
                        psutil.AccessDenied,
                        OSError,
                    ):
                        cpu_percent = None
                    self._proc_cache[pid] = (create_time, target_proc)

            # Process Name: strip directory paths to avoid leaking system hierarchy
            try:
                raw_name = proc.name()
                name = os.path.basename(str(raw_name)) if raw_name else "unknown"
            except (
                psutil.AccessDenied,
                OSError,
                AttributeError,
            ):
                name = "unknown"

            # Process Status
            try:
                status = str(proc.status()) if proc.status() else "unknown"
            except (
                psutil.AccessDenied,
                OSError,
                AttributeError,
            ):
                status = "unknown"

            # Memory Info (RSS and VMS)
            try:
                mem_info = proc.memory_info()
                rss = max(0, int(getattr(mem_info, "rss", 0)))
                vms = max(0, int(getattr(mem_info, "vms", 0)))
            except (
                psutil.AccessDenied,
                OSError,
                AttributeError,
            ):
                rss = 0
                vms = 0

            # Memory utilization percentage
            try:
                raw_mem_pct = proc.memory_percent()
                mem_percent = (
                    round(max(0.0, min(100.0, float(raw_mem_pct))), 2)
                    if raw_mem_pct is not None
                    else None
                )
            except (
                psutil.AccessDenied,
                OSError,
                AttributeError,
            ):
                mem_percent = None

            # Thread count
            try:
                raw_threads = proc.num_threads()
                num_threads = max(0, int(raw_threads)) if raw_threads is not None else 1
            except (
                psutil.AccessDenied,
                OSError,
                AttributeError,
            ):
                num_threads = 1

            username = self._get_username(proc)

            return ProcessMetrics(
                pid=pid,
                name=name,
                status=status,
                cpu_percent=cpu_percent,
                memory_rss=rss,
                memory_vms=vms,
                memory_percent=mem_percent,
                num_threads=num_threads,
                create_time=create_time,
                username=username,
                timestamp=now,
            )
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            return None

    def _collect_all_processes(self, now: datetime) -> list[ProcessMetrics]:
        """Enumerate all running processes and perform defensive state cleanup."""
        results: list[ProcessMetrics] = []
        observed_pids: set[int] = set()

        try:
            for proc in psutil.process_iter():
                try:
                    metrics = self._collect_process(proc, now)
                    if metrics is not None:
                        results.append(metrics)
                        observed_pids.add(metrics.pid)
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                    OSError,
                ):
                    continue
        except (psutil.Error, OSError):
            pass

        # Defensive cleanup: remove terminated PIDs to prevent state growth
        stale_pids = set(self._proc_cache.keys()) - observed_pids
        for pid in stale_pids:
            self._proc_cache.pop(pid, None)

        return results

    def get_process_metrics(self, pid: int) -> ProcessMetrics | None:
        """Collect metrics for a specific running process by PID."""
        now = datetime.now(UTC)
        try:
            proc = psutil.Process(pid)
            metrics = self._collect_process(proc, now)
        except (
            psutil.NoSuchProcess,
            psutil.ZombieProcess,
            psutil.AccessDenied,
            psutil.Error,
            OSError,
            ValueError,
        ):
            self._proc_cache.pop(pid, None)
            metrics = None

        self.last_sampled_at = now
        self._sample_count += 1
        return metrics

    def get_all_process_metrics(self) -> list[ProcessMetrics]:
        """Collect a list of metrics for all running processes."""
        now = datetime.now(UTC)
        processes = self._collect_all_processes(now)
        self.last_sampled_at = now
        self._sample_count += 1
        return processes

    def get_process_collection_metrics(self) -> ProcessCollectionMetrics:
        """Collect a unified snapshot container of running processes and total count."""
        now = datetime.now(UTC)
        processes = self._collect_all_processes(now)
        self.last_sampled_at = now
        self._sample_count += 1
        return ProcessCollectionMetrics(
            processes=processes,
            total_processes=len(processes),
            timestamp=now,
        )
