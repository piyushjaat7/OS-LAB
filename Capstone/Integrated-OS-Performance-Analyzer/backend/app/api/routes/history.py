from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.database import Database
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import get_database
from app.core.config import get_settings
from app.schemas.history import (
    HistoricalMetricsSummary,
    HistoricalSystemMetrics,
)
from app.services.history import (
    aggregate_historical_metrics,
    query_historical_metrics,
)

router = APIRouter(
    prefix="/api/v1/system/history",
    tags=["Historical Metrics"],
)

DatabaseDep = Annotated[Database, Depends(get_database)]


def _normalize_time(dt: datetime | None) -> datetime | None:
    """Ensure datetime has timezone UTC if provided."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


@router.get(
    "",
    response_model=list[HistoricalSystemMetrics],
    summary="Get historical system metric snapshots",
    description="Retrieve stored chronological system metric snapshots with optional time range and sorting.",
)
@router.get(
    "/",
    response_model=list[HistoricalSystemMetrics],
    include_in_schema=False,
)
async def get_historical_metrics(
    db: DatabaseDep,
    start_time: Annotated[
        datetime | None,
        Query(
            description="Filter snapshots on or after this UTC timestamp (ISO-8601).",
        ),
    ] = None,
    end_time: Annotated[
        datetime | None,
        Query(
            description="Filter snapshots on or before this UTC timestamp (ISO-8601).",
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=1000,
            description="Maximum number of historical records to return (1 to 1000).",
        ),
    ] = 100,
    order: Annotated[
        str,
        Query(
            pattern="^(asc|desc)$",
            description="Chronological sort ordering ('desc' or 'asc').",
        ),
    ] = "desc",
) -> list[HistoricalSystemMetrics]:
    start_time = _normalize_time(start_time)
    end_time = _normalize_time(end_time)

    if start_time is not None and end_time is not None and start_time > end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time cannot be greater than end_time",
        )

    settings = get_settings()
    return await run_in_threadpool(
        query_historical_metrics,
        database=db,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        order=order,
        collection_name=settings.historical_metrics_collection,
    )


@router.get(
    "/summary",
    response_model=HistoricalMetricsSummary,
    summary="Get historical metrics summary and statistics",
    description="Compute aggregated statistical metrics (averages, maximums, throughput) over a time window.",
)
async def get_historical_metrics_summary(
    db: DatabaseDep,
    start_time: Annotated[
        datetime | None,
        Query(
            description="Filter summary for snapshots on or after this UTC timestamp.",
        ),
    ] = None,
    end_time: Annotated[
        datetime | None,
        Query(
            description="Filter summary for snapshots on or before this UTC timestamp.",
        ),
    ] = None,
) -> HistoricalMetricsSummary:
    start_time = _normalize_time(start_time)
    end_time = _normalize_time(end_time)

    if start_time is not None and end_time is not None and start_time > end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time cannot be greater than end_time",
        )

    settings = get_settings()
    return await run_in_threadpool(
        aggregate_historical_metrics,
        database=db,
        start_time=start_time,
        end_time=end_time,
        collection_name=settings.historical_metrics_collection,
    )
