import logging
from datetime import UTC, datetime

import psutil

from app.collectors.cpu import CPUCollector
from app.collectors.disk import DiskCollector
from app.collectors.memory import MemoryCollector
from app.collectors.network import NetworkCollector
from app.collectors.process import ProcessCollector
from app.schemas.metrics import (
    CPUMetrics,
    DiskMetrics,
    MemoryMetrics,
    NetworkMetrics,
    ProcessCollectionMetrics,
    ProcessMetrics,
    SystemMetrics,
)

logger = logging.getLogger(__name__)


class SystemMetricsCollector:
    """Central coordinator for unified operating system metrics collection.

    Maintains persistent instances of CPU, Memory, Disk, Network, and Process collectors
    to preserve their internal sampling state, baseline measurements, and non-blocking semantics.
    Coordinates failure-isolated collection across all subsystems into a unified SystemMetrics model.
    """

    def __init__(
        self,
        cpu_collector: CPUCollector | None = None,
        memory_collector: MemoryCollector | None = None,
        disk_collector: DiskCollector | None = None,
        network_collector: NetworkCollector | None = None,
        process_collector: ProcessCollector | None = None,
    ) -> None:
        self.cpu_collector = cpu_collector or CPUCollector()
        self.memory_collector = memory_collector or MemoryCollector()
        self.disk_collector = disk_collector or DiskCollector()
        self.network_collector = network_collector or NetworkCollector()
        self.process_collector = process_collector or ProcessCollector()

        self.initialized_at: datetime = datetime.now(UTC)
        self.last_sampled_at: datetime | None = None
        self._sample_count: int = 0

    def collect_cpu(self) -> CPUMetrics | None:
        """Collect CPU performance metrics with error isolation."""
        try:
            return self.cpu_collector.get_cpu_metrics()
        except (psutil.Error, OSError) as e:
            logger.warning("CPU metrics collection failed: %s", e)
            return None
        except Exception:
            logger.exception("Unexpected error during CPU metrics collection")
            return None

    def collect_memory(self) -> MemoryMetrics | None:
        """Collect RAM and swap memory metrics with error isolation."""
        try:
            return self.memory_collector.get_memory_metrics()
        except (psutil.Error, OSError) as e:
            logger.warning("Memory metrics collection failed: %s", e)
            return None
        except Exception:
            logger.exception("Unexpected error during Memory metrics collection")
            return None

    def collect_disk(self) -> DiskMetrics | None:
        """Collect storage partitions, usage, and I/O metrics with error isolation."""
        try:
            return self.disk_collector.get_disk_metrics()
        except (psutil.Error, OSError) as e:
            logger.warning("Disk metrics collection failed: %s", e)
            return None
        except Exception:
            logger.exception("Unexpected error during Disk metrics collection")
            return None

    def collect_network(self) -> NetworkMetrics | None:
        """Collect network interfaces, counters, and throughput with error isolation."""
        try:
            return self.network_collector.get_network_metrics()
        except (psutil.Error, OSError) as e:
            logger.warning("Network metrics collection failed: %s", e)
            return None
        except Exception:
            logger.exception("Unexpected error during Network metrics collection")
            return None

    def collect_processes(self) -> ProcessCollectionMetrics | None:
        """Collect running processes and resource utilization with error isolation."""
        try:
            return self.process_collector.get_process_collection_metrics()
        except (psutil.Error, OSError) as e:
            logger.warning("Process metrics collection failed: %s", e)
            return None
        except Exception:
            logger.exception("Unexpected error during Process metrics collection")
            return None

    def collect_process(self, pid: int) -> ProcessMetrics | None:
        """Collect metrics for an individual process with error isolation."""
        try:
            return self.process_collector.get_process_metrics(pid)
        except (psutil.Error, OSError) as e:
            logger.warning("Process metrics collection failed for PID %s: %s", pid, e)
            return None
        except Exception:
            logger.exception(
                "Unexpected error during Process metrics collection for PID %s", pid
            )
            return None

    def collect_all(self) -> SystemMetrics:
        """Collect a unified, failure-isolated system metrics snapshot.

        Coordinates collection across all five subsystems:
        - CPU
        - Memory
        - Disk
        - Network
        - Processes

        Timestamp Strategy:
        The top-level `timestamp` is recorded at the start of collection using a
        timezone-aware UTC datetime, representing the beginning of the snapshot capture.
        Individual component schemas maintain their own internal sampling timestamps.

        Failure Isolation:
        A failure in any individual subsystem collector logs a warning and isolates
        that component as None, allowing all other functional components to be returned.

        Returns:
            SystemMetrics: Unified telemetry model containing all available subsystems.
        """
        snapshot_time = datetime.now(UTC)

        cpu = self.collect_cpu()
        memory = self.collect_memory()
        disk = self.collect_disk()
        network = self.collect_network()
        processes = self.collect_processes()

        self.last_sampled_at = snapshot_time
        self._sample_count += 1

        return SystemMetrics(
            cpu=cpu,
            memory=memory,
            disk=disk,
            network=network,
            processes=processes,
            timestamp=snapshot_time,
        )
