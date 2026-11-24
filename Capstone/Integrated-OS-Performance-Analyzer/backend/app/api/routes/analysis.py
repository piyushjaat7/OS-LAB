"""Performance analysis and CPU scheduling simulation API routes.

Provides REST endpoints for:
- Live system health scoring and resource classification.
- Real-time and historically correlated bottleneck detection.
- CPU scheduling simulations (FCFS, SJF, SRTF, Priority, Round Robin).
- Comprehensive multi-algorithm scheduling performance comparisons.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from pymongo.database import Database
from pymongo.errors import PyMongoError
from starlette.concurrency import run_in_threadpool

from app.algorithms.scheduling import (
    compare_all_schedulers,
    schedule_fcfs,
    schedule_priority,
    schedule_round_robin,
    schedule_sjf,
    schedule_srtf,
)
from app.analyzers.bottlenecks import detect_bottlenecks
from app.analyzers.health import analyze_system_health
from app.api.dependencies import get_system_collector
from app.collectors.system import SystemMetricsCollector
from app.database.mongodb import mongodb
from app.schemas.analysis import BottlenecksResponse, SystemHealthAnalysis
from app.schemas.history import HistoricalSystemMetrics
from app.schemas.scheduling import (
    CompareSchedulingRequest,
    PrioritySchedulingRequest,
    RoundRobinSchedulingRequest,
    SchedulingComparison,
    SchedulingRequest,
    SimulationResult,
)
from app.services.history import query_historical_metrics

router = APIRouter(
    prefix="/api/v1/analysis",
    tags=["Performance Analysis & Scheduling"],
)

SystemCollectorDep = Annotated[SystemMetricsCollector, Depends(get_system_collector)]


def get_optional_database() -> Database | None:
    """Return the active MongoDB database if available, else None."""
    return mongodb.database


OptionalDatabaseDep = Annotated[Database | None, Depends(get_optional_database)]


@router.get(
    "/health",
    response_model=SystemHealthAnalysis,
    summary="Compute current system health analysis",
    description="Calculates a unified 0-100 system health score, resource classifications, alerts, and suggested actions.",
)
async def get_system_health(
    collector: SystemCollectorDep,
) -> SystemHealthAnalysis:
    """Evaluate live system metrics snapshot and produce health score & classifications."""
    metrics = await run_in_threadpool(collector.collect_all)
    return analyze_system_health(metrics)


@router.get(
    "/bottlenecks",
    response_model=BottlenecksResponse,
    summary="Detect active system bottlenecks",
    description="Analyzes live metrics and correlates with historical telemetry to identify CPU, memory, disk, and network saturation.",
)
async def get_system_bottlenecks(
    collector: SystemCollectorDep,
    db: OptionalDatabaseDep,
) -> BottlenecksResponse:
    """Evaluate active bottlenecks and historical pressure correlation."""
    metrics = await run_in_threadpool(collector.collect_all)

    history_docs: list[HistoricalSystemMetrics] | None = None
    if db is not None:
        try:
            history_docs = await run_in_threadpool(
                query_historical_metrics,
                database=db,
                limit=60,
                order="desc",
            )
        except PyMongoError:
            history_docs = None

    return detect_bottlenecks(metrics, history_docs=history_docs)


@router.post(
    "/scheduling/fcfs",
    response_model=SimulationResult,
    summary="Simulate First-Come First-Served scheduling",
    description="Executes FCFS scheduling simulation on the submitted workload and computes metrics and Gantt chart segments.",
)
async def simulate_fcfs(payload: SchedulingRequest) -> SimulationResult:
    """Run non-preemptive First-Come First-Served simulation."""
    return schedule_fcfs(payload.processes)


@router.post(
    "/scheduling/sjf",
    response_model=SimulationResult,
    summary="Simulate Shortest Job First scheduling",
    description="Executes non-preemptive Shortest Job First simulation on the submitted workload.",
)
async def simulate_sjf(payload: SchedulingRequest) -> SimulationResult:
    """Run non-preemptive Shortest Job First simulation."""
    return schedule_sjf(payload.processes)


@router.post(
    "/scheduling/srtf",
    response_model=SimulationResult,
    summary="Simulate Shortest Remaining Time First scheduling",
    description="Executes preemptive Shortest Remaining Time First simulation on the submitted workload.",
)
async def simulate_srtf(payload: SchedulingRequest) -> SimulationResult:
    """Run preemptive Shortest Remaining Time First simulation."""
    return schedule_srtf(payload.processes)


@router.post(
    "/scheduling/priority",
    response_model=SimulationResult,
    summary="Simulate Priority scheduling",
    description="Executes Priority scheduling simulation with configurable preemption mode and priority polarity.",
)
async def simulate_priority(
    payload: PrioritySchedulingRequest,
) -> SimulationResult:
    """Run Priority scheduling simulation."""
    return schedule_priority(
        payload.processes,
        preemptive=payload.preemptive,
        priority_order=payload.priority_order,
    )


@router.post(
    "/scheduling/round-robin",
    response_model=SimulationResult,
    summary="Simulate Round Robin scheduling",
    description="Executes Round Robin scheduling simulation with a configurable time quantum.",
)
async def simulate_round_robin(
    payload: RoundRobinSchedulingRequest,
) -> SimulationResult:
    """Run Round Robin scheduling simulation."""
    return schedule_round_robin(
        payload.processes,
        time_quantum=payload.time_quantum,
    )


@router.post(
    "/scheduling/compare",
    response_model=SchedulingComparison,
    summary="Compare all CPU scheduling algorithms",
    description="Executes all standard scheduling algorithms against the exact same workload and produces comparative metrics and recommendations.",
)
async def compare_scheduling_algorithms(
    payload: CompareSchedulingRequest,
) -> SchedulingComparison:
    """Run multi-algorithm comparison across FCFS, SJF, SRTF, Priority, and Round Robin."""
    return compare_all_schedulers(
        payload.processes,
        time_quantum=payload.time_quantum,
        priority_order=payload.priority_order,
    )
