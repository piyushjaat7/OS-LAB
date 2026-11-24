from datetime import UTC, datetime
from typing import Any

from pymongo.database import Database

from app.schemas.history import (
    HistoricalMetricsSummary,
    HistoricalSystemMetrics,
)


def _round_optional(val: Any) -> float | None:
    """Safely round numeric values to 2 decimal places if present."""
    return round(float(val), 2) if val is not None else None


def query_historical_metrics(
    database: Database,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100,
    order: str = "desc",
    collection_name: str = "system_metrics_history",
) -> list[HistoricalSystemMetrics]:
    """Query chronological historical system metric snapshots from MongoDB."""
    if database is None:
        return []

    collection = database[collection_name]
    query_filter: dict[str, Any] = {}
    time_filter: dict[str, Any] = {}

    if start_time is not None:
        time_filter["$gte"] = start_time
    if end_time is not None:
        time_filter["$lte"] = end_time
    if time_filter:
        query_filter["timestamp"] = time_filter

    sort_direction = -1 if order == "desc" else 1
    cursor = (
        collection.find(query_filter).sort("timestamp", sort_direction).limit(limit)
    )

    results: list[HistoricalSystemMetrics] = []
    for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        if (
            isinstance(doc.get("timestamp"), datetime)
            and doc["timestamp"].tzinfo is None
        ):
            doc["timestamp"] = doc["timestamp"].replace(tzinfo=UTC)
        results.append(HistoricalSystemMetrics.model_validate(doc))

    return results


def aggregate_historical_metrics(
    database: Database,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    collection_name: str = "system_metrics_history",
) -> HistoricalMetricsSummary:
    """Execute MongoDB aggregation pipeline to compute statistical summaries over historical window."""
    if database is None:
        return HistoricalMetricsSummary(
            sample_count=0,
            start_time=start_time,
            end_time=end_time,
        )

    collection = database[collection_name]
    pipeline: list[dict[str, Any]] = []
    match_stage: dict[str, Any] = {}
    time_filter: dict[str, Any] = {}

    if start_time is not None:
        time_filter["$gte"] = start_time
    if end_time is not None:
        time_filter["$lte"] = end_time
    if time_filter:
        match_stage["timestamp"] = time_filter

    if match_stage:
        pipeline.append({"$match": match_stage})

    pipeline.append(
        {
            "$group": {
                "_id": None,
                "sample_count": {"$sum": 1},
                "min_timestamp": {"$min": "$timestamp"},
                "max_timestamp": {"$max": "$timestamp"},
                "cpu_avg_percent": {"$avg": "$cpu.usage_percent"},
                "cpu_max_percent": {"$max": "$cpu.usage_percent"},
                "memory_avg_percent": {"$avg": "$memory.percent"},
                "memory_max_percent": {"$max": "$memory.percent"},
                "network_avg_bytes_sent_per_sec": {
                    "$avg": "$network.throughput_sent_bytes_per_sec"
                },
                "network_avg_bytes_recv_per_sec": {
                    "$avg": "$network.throughput_recv_bytes_per_sec"
                },
            }
        }
    )

    rows = list(collection.aggregate(pipeline))
    if not rows:
        return HistoricalMetricsSummary(
            sample_count=0,
            start_time=start_time,
            end_time=end_time,
            cpu_avg_percent=None,
            cpu_max_percent=None,
            memory_avg_percent=None,
            memory_max_percent=None,
            network_avg_bytes_sent_per_sec=None,
            network_avg_bytes_recv_per_sec=None,
        )

    row = rows[0]
    min_ts = row.get("min_timestamp")
    if isinstance(min_ts, datetime) and min_ts.tzinfo is None:
        min_ts = min_ts.replace(tzinfo=UTC)
    max_ts = row.get("max_timestamp")
    if isinstance(max_ts, datetime) and max_ts.tzinfo is None:
        max_ts = max_ts.replace(tzinfo=UTC)

    return HistoricalMetricsSummary(
        sample_count=int(row.get("sample_count", 0)),
        start_time=min_ts or start_time,
        end_time=max_ts or end_time,
        cpu_avg_percent=_round_optional(row.get("cpu_avg_percent")),
        cpu_max_percent=_round_optional(row.get("cpu_max_percent")),
        memory_avg_percent=_round_optional(row.get("memory_avg_percent")),
        memory_max_percent=_round_optional(row.get("memory_max_percent")),
        network_avg_bytes_sent_per_sec=_round_optional(
            row.get("network_avg_bytes_sent_per_sec")
        ),
        network_avg_bytes_recv_per_sec=_round_optional(
            row.get("network_avg_bytes_recv_per_sec")
        ),
    )
