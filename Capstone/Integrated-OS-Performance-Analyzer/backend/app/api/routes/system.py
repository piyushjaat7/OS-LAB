import asyncio
import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from starlette.concurrency import run_in_threadpool
from starlette.websockets import WebSocketState

from app.api.dependencies import get_system_collector
from app.collectors.system import SystemMetricsCollector
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

DEFAULT_SAMPLING_INTERVAL_SECONDS: float = 1.0
MIN_SAMPLING_INTERVAL_SECONDS: float = 0.5
MAX_SAMPLING_INTERVAL_SECONDS: float = 60.0

router = APIRouter(
    prefix="/api/v1/system",
    tags=["System Metrics"],
)

SystemCollectorDep = Annotated[SystemMetricsCollector, Depends(get_system_collector)]


@router.websocket("/ws")
async def websocket_system_metrics(
    websocket: WebSocket,
    collector: SystemCollectorDep,
    interval: Annotated[
        float,
        Query(
            ge=MIN_SAMPLING_INTERVAL_SECONDS,
            le=MAX_SAMPLING_INTERVAL_SECONDS,
            description=(
                f"Sampling interval in seconds between metric snapshots "
                f"({MIN_SAMPLING_INTERVAL_SECONDS} to {MAX_SAMPLING_INTERVAL_SECONDS}s)."
            ),
        ),
    ] = DEFAULT_SAMPLING_INTERVAL_SECONDS,
) -> None:
    """Stream real-time consolidated system metrics over WebSocket.

    Periodically samples CPU, memory, disk, network, and process telemetry
    using the persistent application collector and transmits serialized
    SystemMetrics models at the requested sampling interval.
    """
    if (
        interval < MIN_SAMPLING_INTERVAL_SECONDS
        or interval > MAX_SAMPLING_INTERVAL_SECONDS
    ):
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=(
                f"Sampling interval must be between {MIN_SAMPLING_INTERVAL_SECONDS} "
                f"and {MAX_SAMPLING_INTERVAL_SECONDS} seconds."
            ),
        )
        return

    await websocket.accept()
    logger.info(
        "WebSocket client connected from %s (sampling interval: %.2fs)",
        websocket.client,
        interval,
    )
    try:
        while True:
            if websocket.client_state != WebSocketState.CONNECTED:
                break

            try:
                metrics = await run_in_threadpool(collector.collect_all)
            except Exception:
                logger.exception(
                    "Error collecting system metrics snapshot for WebSocket"
                )
                try:
                    await websocket.send_json(
                        {
                            "error": "Failed to collect system metrics snapshot",
                        }
                    )
                except (WebSocketDisconnect, RuntimeError):
                    break
                await asyncio.sleep(interval)
                continue

            try:
                await websocket.send_text(metrics.model_dump_json())
            except (WebSocketDisconnect, RuntimeError):
                break

            await asyncio.sleep(interval)
    except (WebSocketDisconnect, RuntimeError):
        logger.info("WebSocket client disconnected: %s", websocket.client)
    except asyncio.CancelledError:
        logger.info(
            "WebSocket streaming task cancelled for client: %s",
            websocket.client,
        )
        raise


@router.get(
    "/metrics",
    response_model=SystemMetrics,
    summary="Get unified system metrics snapshot",
    description="Returns a consolidated, failure-isolated snapshot of CPU, Memory, Disk, Network, and Process metrics.",
)
async def get_system_metrics(
    collector: SystemCollectorDep,
) -> SystemMetrics:
    return await run_in_threadpool(collector.collect_all)


@router.get(
    "/cpu",
    response_model=CPUMetrics,
    summary="Get CPU performance metrics",
    description="Returns overall utilization, per-core utilization, physical/logical core counts, and operating frequency.",
)
async def get_cpu_metrics(
    collector: SystemCollectorDep,
) -> CPUMetrics:
    cpu = await run_in_threadpool(collector.collect_cpu)
    if cpu is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CPU metrics are currently unavailable",
        )
    return cpu


@router.get(
    "/memory",
    response_model=MemoryMetrics,
    summary="Get memory metrics",
    description="Returns virtual memory (RAM) and swap memory capacity and utilization statistics.",
)
async def get_memory_metrics(
    collector: SystemCollectorDep,
) -> MemoryMetrics:
    memory = await run_in_threadpool(collector.collect_memory)
    if memory is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Memory metrics are currently unavailable",
        )
    return memory


@router.get(
    "/disk",
    response_model=DiskMetrics,
    summary="Get storage and disk metrics",
    description="Returns mounted disk partitions, storage capacity/utilization per partition, and cumulative I/O counters.",
)
async def get_disk_metrics(
    collector: SystemCollectorDep,
) -> DiskMetrics:
    disk = await run_in_threadpool(collector.collect_disk)
    if disk is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Disk metrics are currently unavailable",
        )
    return disk


@router.get(
    "/network",
    response_model=NetworkMetrics,
    summary="Get network metrics",
    description="Returns detected network interfaces, cumulative network traffic counters, and calculated instantaneous throughput.",
)
async def get_network_metrics(
    collector: SystemCollectorDep,
) -> NetworkMetrics:
    network = await run_in_threadpool(collector.collect_network)
    if network is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Network metrics are currently unavailable",
        )
    return network


@router.get(
    "/processes",
    response_model=ProcessCollectionMetrics,
    summary="Get running processes telemetry",
    description="Returns telemetry metrics for all active running processes including CPU, memory, status, and thread count.",
)
async def get_processes_metrics(
    collector: SystemCollectorDep,
) -> ProcessCollectionMetrics:
    processes = await run_in_threadpool(collector.collect_processes)
    if processes is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Process collection metrics are currently unavailable",
        )
    return processes


@router.get(
    "/processes/{pid}",
    response_model=ProcessMetrics,
    summary="Get single process metrics by PID",
    description="Returns resource consumption and telemetry metrics for an individual process identified by its PID.",
)
async def get_process_by_pid(
    pid: int,
    collector: SystemCollectorDep,
) -> ProcessMetrics:
    if pid < 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process with PID {pid} not found or inaccessible",
        )
    process = await run_in_threadpool(collector.collect_process, pid)
    if process is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process with PID {pid} not found or inaccessible",
        )
    return process
