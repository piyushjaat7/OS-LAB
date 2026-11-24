from datetime import UTC, datetime
from typing import Any

import psutil

from app.schemas.metrics import CPUFrequency, CPUMetrics


class CPUCollector:
    """Cross-platform collector for CPU performance metrics using psutil."""

    def __init__(self) -> None:
        self.initialized_at: datetime = datetime.now(UTC)
        self.last_sampled_at: datetime | None = None
        self._sample_count: int = 0
        self._last_cpu_times: Any = None
        self._last_per_cpu_times: list[Any] | None = None
        self._init_sampling()

    def _init_sampling(self) -> None:
        """Initialize the CPU sampling baseline without blocking.

        Captures the initial system CPU times and per-core times into instance state.
        At this initial point, no sampling interval has elapsed.
        """
        try:
            self._last_cpu_times = psutil.cpu_times()
            self._last_per_cpu_times = psutil.cpu_times(percpu=True)
        except (psutil.Error, OSError):
            self._last_cpu_times = None
            self._last_per_cpu_times = None

    @staticmethod
    def _calculate_total_time(times: Any) -> float:
        """Calculate total CPU time from a scputimes namedtuple across platforms."""
        if times is None:
            return 0.0
        tot = sum(times)
        # On Linux, guest times are already accounted in user or nice times
        tot -= getattr(times, "guest", 0.0)
        tot -= getattr(times, "guest_nice", 0.0)
        return float(tot)

    @staticmethod
    def _calculate_busy_time(times: Any) -> float:
        """Calculate busy CPU time from a scputimes namedtuple across platforms."""
        if times is None:
            return 0.0
        tot = CPUCollector._calculate_total_time(times)
        idle = getattr(times, "idle", 0.0)
        iowait = getattr(times, "iowait", 0.0)
        return max(0.0, tot - idle - iowait)

    def _get_logical_cores(self, per_core_usage: list[float] | None) -> int:
        """Retrieve logical core count with safe fallbacks."""
        try:
            count = psutil.cpu_count(logical=True)
            if count is not None and count >= 0:
                return count
        except (psutil.Error, OSError):
            pass

        if per_core_usage:
            return len(per_core_usage)
        return 0

    def _get_physical_cores(self, logical_fallback: int) -> int:
        """Retrieve physical core count with safe fallbacks."""
        try:
            count = psutil.cpu_count(logical=False)
            if count is not None and count >= 0:
                return count
        except (psutil.Error, OSError):
            pass

        return max(0, logical_fallback)

    def _get_cpu_frequency(self) -> CPUFrequency | None:
        """Retrieve current CPU frequency where supported.

        Gracefully handles missing frequency data or platform-specific
        exceptions (e.g. VMs, WSL2, containers, or restricted environments).
        """
        try:
            freq = psutil.cpu_freq()
            if freq is None:
                return None

            current = (
                float(freq.current)
                if freq.current is not None and freq.current >= 0.0
                else None
            )
            min_freq = (
                float(freq.min) if freq.min is not None and freq.min >= 0.0 else None
            )
            max_freq = (
                float(freq.max) if freq.max is not None and freq.max >= 0.0 else None
            )

            if current is None and min_freq is None and max_freq is None:
                return None

            return CPUFrequency(
                current=round(current, 2) if current is not None else None,
                min=round(min_freq, 2) if min_freq is not None else None,
                max=round(max_freq, 2) if max_freq is not None else None,
            )
        except (AttributeError, OSError, psutil.Error):
            return None

    def get_cpu_metrics(self) -> CPUMetrics:
        """Collect and return validated CPU performance metrics.

        Lifecycle:
            - On the initial call before a valid sampling interval has elapsed
              (i.e. zero CPU clock ticks have advanced since the baseline),
              usage_percent and per_core_usage are returned as None.
            - On subsequent calls after CPU ticks have advanced, actual utilization
              percentages are computed and returned.
            - A genuine idle state (system was 100% idle over an elapsed interval)
              returns 0.0, clearly distinguishable from None (unavailable).
        """
        now = datetime.now(UTC)

        usage_percent: float | None = None
        per_core_usage: list[float] | None = None

        try:
            current_times = psutil.cpu_times()
            current_per_cpu = psutil.cpu_times(percpu=True)
        except (psutil.Error, OSError):
            current_times = None
            current_per_cpu = None

        if (
            self._sample_count > 0
            and self._last_cpu_times is not None
            and current_times is not None
        ):
            total_delta = self._calculate_total_time(
                current_times
            ) - self._calculate_total_time(self._last_cpu_times)

            if total_delta > 0.0:
                busy_delta = max(
                    0.0,
                    self._calculate_busy_time(current_times)
                    - self._calculate_busy_time(self._last_cpu_times),
                )
                usage_percent = max(
                    0.0, min(100.0, round((busy_delta / total_delta) * 100.0, 1))
                )

                if self._last_per_cpu_times and current_per_cpu:
                    per_core_usage = []
                    for last_c, curr_c in zip(
                        self._last_per_cpu_times, current_per_cpu
                    ):
                        core_tot = self._calculate_total_time(
                            curr_c
                        ) - self._calculate_total_time(last_c)
                        if core_tot > 0.0:
                            core_busy = max(
                                0.0,
                                self._calculate_busy_time(curr_c)
                                - self._calculate_busy_time(last_c),
                            )
                            per_core_usage.append(
                                max(
                                    0.0,
                                    min(
                                        100.0,
                                        round((core_busy / core_tot) * 100.0, 1),
                                    ),
                                )
                            )
                        else:
                            per_core_usage.append(0.0)

        if current_times is not None:
            self._last_cpu_times = current_times
            self._last_per_cpu_times = current_per_cpu

        # Core counts with safe fallbacks
        logical_cores = self._get_logical_cores(per_core_usage)
        physical_cores = self._get_physical_cores(logical_cores)

        # CPU Frequency
        frequency = self._get_cpu_frequency()

        # Update instance sampling tracking
        self.last_sampled_at = now
        self._sample_count += 1

        return CPUMetrics(
            usage_percent=usage_percent,
            per_core_usage=per_core_usage,
            physical_cores=physical_cores,
            logical_cores=logical_cores,
            frequency=frequency,
            timestamp=now,
        )
