from datetime import UTC, datetime

import psutil

from app.schemas.metrics import (
    MemoryMetrics,
    SwapMemoryMetrics,
    VirtualMemoryMetrics,
)


class MemoryCollector:
    """Cross-platform collector for RAM and Swap memory metrics using psutil."""

    def __init__(self) -> None:
        self.initialized_at: datetime = datetime.now(UTC)
        self.last_sampled_at: datetime | None = None
        self._sample_count: int = 0

    def _collect_virtual(self) -> VirtualMemoryMetrics:
        """Internal helper to sample and validate virtual memory."""
        vm = psutil.virtual_memory()
        return VirtualMemoryMetrics(
            total=int(vm.total),
            available=int(vm.available),
            used=int(vm.used),
            free=int(vm.free),
            percent=max(0.0, min(100.0, float(vm.percent))),
        )

    def _collect_swap(self) -> SwapMemoryMetrics:
        """Internal helper to sample and validate swap memory."""
        sm = psutil.swap_memory()
        if sm is None:
            return SwapMemoryMetrics(
                total=0,
                used=0,
                free=0,
                percent=0.0,
                sin=0,
                sout=0,
            )
        return SwapMemoryMetrics(
            total=int(sm.total),
            used=int(sm.used),
            free=int(sm.free),
            percent=max(0.0, min(100.0, float(sm.percent))),
            sin=int(getattr(sm, "sin", 0)),
            sout=int(getattr(sm, "sout", 0)),
        )

    def get_virtual_memory_metrics(self) -> VirtualMemoryMetrics:
        """Collect current system virtual memory (RAM) statistics.

        Returns:
            VirtualMemoryMetrics: Validated metrics including total, available,
                used, free, and percentage.

        Raises:
            psutil.Error: If underlying system memory counters cannot be retrieved.
            OSError: If an operating system error occurs.
        """
        vm = self._collect_virtual()
        self.last_sampled_at = datetime.now(UTC)
        self._sample_count += 1
        return vm

    def get_swap_memory_metrics(self) -> SwapMemoryMetrics:
        """Collect current system swap space statistics.

        On environments where swap memory is absent (e.g. containers, certain
        WSL2 configurations, or systems with swap disabled), zeroed values
        are returned rather than failing.

        Returns:
            SwapMemoryMetrics: Validated swap metrics including total, used,
                free, percent, sin, and sout.

        Raises:
            psutil.Error: If an unexpected psutil error occurs.
            OSError: If an operating system error occurs.
        """
        sm = self._collect_swap()
        self.last_sampled_at = datetime.now(UTC)
        self._sample_count += 1
        return sm

    def get_memory_metrics(self) -> MemoryMetrics:
        """Collect combined virtual and swap memory metrics with a unified timestamp.

        Returns:
            MemoryMetrics: Container with both virtual and swap telemetry.

        Raises:
            psutil.Error: If memory collection fails.
            OSError: If an operating system error occurs.
        """
        now = datetime.now(UTC)
        vm = self._collect_virtual()
        sm = self._collect_swap()
        self.last_sampled_at = now
        self._sample_count += 1
        return MemoryMetrics(
            virtual=vm,
            swap=sm,
            timestamp=now,
        )
