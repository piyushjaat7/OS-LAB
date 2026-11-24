import asyncio
import logging
from typing import Any

from pymongo.errors import PyMongoError
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import get_system_collector
from app.collectors.system import SystemMetricsCollector
from app.core.config import get_settings
from app.database.mongodb import MongoDBManager, mongodb
from app.schemas.metrics import SystemMetrics

logger = logging.getLogger(__name__)

MIN_HISTORICAL_INTERVAL_SECONDS: float = 1.0
MAX_HISTORICAL_INTERVAL_SECONDS: float = 3600.0
DEFAULT_HISTORICAL_INTERVAL_SECONDS: float = 5.0


def build_historical_document(metrics: SystemMetrics) -> dict[str, Any]:
    """Transform a live SystemMetrics snapshot into a streamlined historical document.

    Omits high-volume per-process lists to minimize storage footprint while
    preserving hardware counters, aggregate statistics, and failure isolation (None).
    """
    # 1. CPU Section
    cpu_data: dict[str, Any] | None = None
    if metrics.cpu is not None:
        cpu_data = {
            "usage_percent": metrics.cpu.usage_percent,
            "per_core_usage": metrics.cpu.per_core_usage,
            "physical_cores": metrics.cpu.physical_cores,
            "logical_cores": metrics.cpu.logical_cores,
            "frequency_mhz": (
                metrics.cpu.frequency.current
                if metrics.cpu.frequency is not None
                else None
            ),
        }

    # 2. Memory Section
    mem_data: dict[str, Any] | None = None
    if metrics.memory is not None:
        vm = metrics.memory.virtual
        sm = metrics.memory.swap
        mem_data = {
            "total_bytes": vm.total if vm else None,
            "used_bytes": vm.used if vm else None,
            "available_bytes": vm.available if vm else None,
            "percent": vm.percent if vm else None,
            "swap_total_bytes": sm.total if sm else None,
            "swap_used_bytes": sm.used if sm else None,
            "swap_percent": sm.percent if sm else None,
        }

    # 3. Disk Section (Aggregate Partition Usage + I/O Counters)
    disk_data: dict[str, Any] | None = None
    if metrics.disk is not None:
        if metrics.disk.total_capacity_bytes is not None:
            total_space = metrics.disk.total_capacity_bytes
            used_space = metrics.disk.total_used_bytes or 0
            free_space = metrics.disk.total_free_bytes or 0
            aggregate_percent = metrics.disk.total_percent
            has_usage = True
        else:
            total_space = 0
            used_space = 0
            free_space = 0
            has_usage = False

            seen_devs: set[str] = set()
            for partition in metrics.disk.partitions:
                dev_id = partition.partition.device or partition.partition.mountpoint
                if dev_id in seen_devs:
                    continue
                seen_devs.add(dev_id)

                if partition.usage is not None:
                    has_usage = True
                    total_space += partition.usage.total
                    used_space += partition.usage.used
                    free_space += partition.usage.free

            aggregate_percent = (
                round((used_space / total_space) * 100.0, 1)
                if has_usage and total_space > 0
                else None
            )

        io = metrics.disk.io_counters
        disk_data = {
            "total_bytes": total_space if has_usage else None,
            "used_bytes": used_space if has_usage else None,
            "free_bytes": free_space if has_usage else None,
            "percent": aggregate_percent,
            "read_bytes": io.read_bytes if io else None,
            "write_bytes": io.write_bytes if io else None,
            "read_count": io.read_count if io else None,
            "write_count": io.write_count if io else None,
        }

    # 4. Network Section (Aggregate Counters + Calculated Throughput)
    net_data: dict[str, Any] | None = None
    if metrics.network is not None:
        net_io = metrics.network.io_counters
        net_tp = metrics.network.throughput
        net_data = {
            "bytes_sent": net_io.bytes_sent if net_io else None,
            "bytes_recv": net_io.bytes_recv if net_io else None,
            "packets_sent": net_io.packets_sent if net_io else None,
            "packets_recv": net_io.packets_recv if net_io else None,
            "throughput_sent_bytes_per_sec": (
                net_tp.bytes_sent_per_sec if net_tp else None
            ),
            "throughput_recv_bytes_per_sec": (
                net_tp.bytes_recv_per_sec if net_tp else None
            ),
        }

    # 5. Process Summary (Count only, NO full process list)
    total_procs = (
        metrics.processes.total_processes if metrics.processes is not None else None
    )

    return {
        "timestamp": metrics.timestamp,
        "cpu": cpu_data,
        "memory": mem_data,
        "disk": disk_data,
        "network": net_data,
        "total_processes": total_procs,
    }


class MetricsPersistenceService:
    """Manages the background collection and persistence of system metrics into MongoDB."""

    def __init__(
        self,
        db_manager: MongoDBManager,
        collector: SystemMetricsCollector,
        interval_seconds: float = DEFAULT_HISTORICAL_INTERVAL_SECONDS,
        collection_name: str = "system_metrics_history",
    ) -> None:
        self._db_manager = db_manager
        self._collector = collector
        self._interval_seconds = self._validate_interval(interval_seconds)
        self._collection_name = collection_name
        self._task: asyncio.Task[None] | None = None
        self._running: bool = False

    @staticmethod
    def _validate_interval(interval: float) -> float:
        if (
            interval < MIN_HISTORICAL_INTERVAL_SECONDS
            or interval > MAX_HISTORICAL_INTERVAL_SECONDS
        ):
            raise ValueError(
                f"Historical metrics interval must be between "
                f"{MIN_HISTORICAL_INTERVAL_SECONDS} and {MAX_HISTORICAL_INTERVAL_SECONDS} seconds."
            )
        return float(interval)

    @property
    def is_running(self) -> bool:
        return self._running and self._task is not None and not self._task.done()

    @property
    def interval_seconds(self) -> float:
        return self._interval_seconds

    def ensure_indexes(self) -> None:
        """Create required timestamp index for efficient historical queries."""
        if self._db_manager.database is None:
            return
        collection = self._db_manager.database[self._collection_name]
        collection.create_index([("timestamp", -1)], name="idx_timestamp_desc")
        logger.info(
            "MongoDB index 'idx_timestamp_desc' ensured on '%s'",
            self._collection_name,
        )

    async def start(self) -> None:
        """Start the background persistence task, ensuring single worker execution."""
        if self.is_running:
            logger.warning(
                "Historical metrics persistence worker is already active; ignoring duplicate start request"
            )
            return

        if self._db_manager.database is not None:
            await run_in_threadpool(self.ensure_indexes)

        self._running = True
        self._task = asyncio.create_task(
            self._worker_loop(),
            name="historical-metrics-persistence-worker",
        )
        logger.info(
            "Historical metrics persistence service started (interval: %.2fs)",
            self._interval_seconds,
        )

    async def stop(self) -> None:
        """Stop the background persistence task cleanly."""
        if not self._running and self._task is None:
            return

        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("Historical metrics persistence service stopped cleanly")

    async def _worker_loop(self) -> None:
        """Main periodic collection loop running independently of web requests."""
        while self._running:
            try:
                await self._persist_snapshot()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception(
                    "Unexpected error in historical metrics persistence worker loop"
                )

            try:
                await asyncio.sleep(self._interval_seconds)
            except asyncio.CancelledError:
                break

    async def _persist_snapshot(self) -> None:
        """Collect and persist one historical metrics snapshot."""
        if self._db_manager.database is None:
            logger.debug(
                "MongoDB database not connected; skipping historical metrics persistence iteration"
            )
            return

        try:
            metrics = await run_in_threadpool(self._collector.collect_all)
            document = build_historical_document(metrics)
            await run_in_threadpool(self._write_document, document)
        except Exception:
            logger.exception("Failed to collect or persist historical metrics snapshot")

    def _write_document(self, document: dict[str, Any]) -> None:
        """Synchronously write document to MongoDB, isolated in worker thread."""
        if self._db_manager.database is None:
            return
        try:
            collection = self._db_manager.database[self._collection_name]
            collection.insert_one(document)
        except PyMongoError:
            logger.exception(
                "Failed to insert historical metrics document into MongoDB"
            )


_persistence_service_instance: MetricsPersistenceService | None = None


def get_metrics_persistence_service() -> MetricsPersistenceService:
    """Retrieve or initialize the persistent application-wide MetricsPersistenceService."""
    global _persistence_service_instance
    if _persistence_service_instance is None:
        settings = get_settings()
        collector = get_system_collector()
        _persistence_service_instance = MetricsPersistenceService(
            db_manager=mongodb,
            collector=collector,
            interval_seconds=settings.historical_metrics_interval_seconds,
            collection_name=settings.historical_metrics_collection,
        )
    return _persistence_service_instance


def reset_metrics_persistence_service() -> None:
    """Reset the persistence service instance (for testing teardown)."""
    global _persistence_service_instance
    _persistence_service_instance = None
