from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError

from app.api.dependencies import get_database
from app.collectors.system import SystemMetricsCollector
from app.database.mongodb import MongoDBManager
from app.main import app
from app.schemas.history import (
    HistoricalMetricsSummary,
    HistoricalSystemMetrics,
)
from app.schemas.metrics import (
    CPUFrequency,
    CPUMetrics,
    DiskIOCountersMetrics,
    DiskMetrics,
    DiskPartitionInfo,
    DiskPartitionMetrics,
    DiskUsageMetrics,
    MemoryMetrics,
    NetworkIOCountersMetrics,
    NetworkMetrics,
    NetworkThroughputMetrics,
    ProcessCollectionMetrics,
    ProcessMetrics,
    SwapMemoryMetrics,
    SystemMetrics,
    VirtualMemoryMetrics,
)
from app.services.history import (
    aggregate_historical_metrics,
    query_historical_metrics,
)
from app.services.metrics_persistence import (
    MAX_HISTORICAL_INTERVAL_SECONDS,
    MIN_HISTORICAL_INTERVAL_SECONDS,
    MetricsPersistenceService,
    build_historical_document,
)


@pytest.fixture(autouse=True)
def cleanup_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _make_dummy_system_metrics() -> SystemMetrics:
    cpu = CPUMetrics(
        usage_percent=32.5,
        per_core_usage=[30.0, 35.0],
        physical_cores=2,
        logical_cores=4,
        frequency=CPUFrequency(current=2400.0, min=800.0, max=4200.0),
    )
    mem = MemoryMetrics(
        virtual=VirtualMemoryMetrics(
            total=16000000000,
            available=10000000000,
            used=6000000000,
            free=4000000000,
            percent=37.5,
        ),
        swap=SwapMemoryMetrics(
            total=4000000000,
            used=1000000000,
            free=3000000000,
            percent=25.0,
            sin=0,
            sout=0,
        ),
    )
    disk = DiskMetrics(
        partitions=[
            DiskPartitionInfo(
                partition=DiskPartitionMetrics(
                    device="/dev/sda1",
                    mountpoint="/",
                    filesystem="ext4",
                    options="rw",
                ),
                usage=DiskUsageMetrics(
                    total=100000000000,
                    used=40000000000,
                    free=60000000000,
                    percent=40.0,
                ),
            )
        ],
        io_counters=DiskIOCountersMetrics(
            read_bytes=100000,
            write_bytes=200000,
            read_count=50,
            write_count=75,
            read_time=1000,
            write_time=2000,
        ),
    )
    network = NetworkMetrics(
        interfaces=[],
        io_counters=NetworkIOCountersMetrics(
            bytes_sent=500000,
            bytes_recv=800000,
            packets_sent=1000,
            packets_recv=1500,
            errin=0,
            errout=0,
            dropin=0,
            dropout=0,
        ),
        throughput=NetworkThroughputMetrics(
            bytes_sent_per_sec=12500.0,
            bytes_recv_per_sec=25000.0,
        ),
    )
    processes = ProcessCollectionMetrics(
        processes=[
            ProcessMetrics(
                pid=1,
                name="init",
                status="running",
                cpu_percent=0.1,
                memory_rss=1000,
                memory_vms=2000,
                memory_percent=0.01,
                num_threads=1,
                create_time=1700000000.0,
                username="root",
            )
        ],
        total_processes=42,
    )
    return SystemMetrics(
        cpu=cpu,
        memory=mem,
        disk=disk,
        network=network,
        processes=processes,
        timestamp=datetime.now(UTC),
    )


def test_build_historical_document_complete():
    """Verify complete transformation and omission of full process list."""
    metrics = _make_dummy_system_metrics()
    doc = build_historical_document(metrics)

    assert doc["timestamp"] == metrics.timestamp
    assert doc["cpu"]["usage_percent"] == 32.5
    assert doc["cpu"]["frequency_mhz"] == 2400.0
    assert doc["memory"]["total_bytes"] == 16000000000
    assert doc["memory"]["swap_percent"] == 25.0
    assert doc["disk"]["total_bytes"] == 100000000000
    assert doc["disk"]["percent"] == 40.0
    assert doc["disk"]["read_bytes"] == 100000
    assert doc["network"]["bytes_sent"] == 500000
    assert doc["network"]["throughput_sent_bytes_per_sec"] == 12500.0
    assert doc["total_processes"] == 42
    # Verify process list is completely excluded from historical storage
    assert "processes" not in doc


def test_build_historical_document_null_isolation():
    """Verify that unavailable metrics remain None and are not converted to 0."""
    metrics = SystemMetrics(
        cpu=None,
        memory=None,
        disk=None,
        network=None,
        processes=None,
        timestamp=datetime.now(UTC),
    )
    doc = build_historical_document(metrics)

    assert doc["cpu"] is None
    assert doc["memory"] is None
    assert doc["disk"] is None
    assert doc["network"] is None
    assert doc["total_processes"] is None


def test_interval_validation():
    """Verify validation of persistence service sampling intervals."""
    mock_db = MagicMock(spec=MongoDBManager)
    mock_col = MagicMock(spec=SystemMetricsCollector)

    # Valid bounds
    s1 = MetricsPersistenceService(mock_db, mock_col, interval_seconds=1.0)
    assert s1.interval_seconds == 1.0

    s2 = MetricsPersistenceService(mock_db, mock_col, interval_seconds=3600.0)
    assert s2.interval_seconds == 3600.0

    # Below minimum
    with pytest.raises(ValueError):
        MetricsPersistenceService(
            mock_db,
            mock_col,
            interval_seconds=MIN_HISTORICAL_INTERVAL_SECONDS - 0.1,
        )

    # Above maximum
    with pytest.raises(ValueError):
        MetricsPersistenceService(
            mock_db,
            mock_col,
            interval_seconds=MAX_HISTORICAL_INTERVAL_SECONDS + 10.0,
        )


@pytest.mark.anyio
async def test_worker_startup_shutdown_and_duplicate_prevention():
    """Verify background worker lifecycle and duplicate worker prevention."""
    mock_db = MagicMock(spec=MongoDBManager)
    mock_db.database = MagicMock()
    mock_col = MagicMock(spec=SystemMetricsCollector)
    mock_col.collect_all.return_value = _make_dummy_system_metrics()

    service = MetricsPersistenceService(
        db_manager=mock_db,
        collector=mock_col,
        interval_seconds=5.0,
    )
    assert not service.is_running

    await service.start()
    assert service.is_running

    initial_task = service._task
    # Attempt duplicate start; should log warning and retain original task
    await service.start()
    assert service._task is initial_task

    await service.stop()
    assert not service.is_running
    assert service._task is None


def test_index_creation():
    """Verify timestamp index creation on collection."""
    mock_db_manager = MagicMock(spec=MongoDBManager)
    mock_database = MagicMock()
    mock_db_manager.database = mock_database
    mock_collection = MagicMock()
    mock_database.__getitem__.return_value = mock_collection
    mock_col = MagicMock(spec=SystemMetricsCollector)

    service = MetricsPersistenceService(
        db_manager=mock_db_manager,
        collector=mock_col,
        interval_seconds=5.0,
        collection_name="test_history_collection",
    )
    service.ensure_indexes()

    mock_collection.create_index.assert_called_once_with(
        [("timestamp", -1)],
        name="idx_timestamp_desc",
    )


def test_write_failure_handling_does_not_crash():
    """Verify PyMongo errors during write are logged and do not crash."""
    mock_db_manager = MagicMock(spec=MongoDBManager)
    mock_database = MagicMock()
    mock_db_manager.database = mock_database
    mock_collection = MagicMock()
    mock_database.__getitem__.return_value = mock_collection
    mock_collection.insert_one.side_effect = PyMongoError("Connection reset")
    mock_col = MagicMock(spec=SystemMetricsCollector)

    service = MetricsPersistenceService(
        db_manager=mock_db_manager,
        collector=mock_col,
        interval_seconds=5.0,
    )
    # Should not raise exception
    service._write_document({"timestamp": datetime.now(UTC)})


def test_query_historical_metrics_helper():
    """Verify query_historical_metrics transforms docs and normalizes timezone."""
    mock_db = MagicMock()
    mock_col = MagicMock()
    mock_db.__getitem__.return_value = mock_col

    fake_id = ObjectId()
    naive_dt = datetime(2026, 11, 13, 5, 0, 0)
    mock_col.find.return_value.sort.return_value.limit.return_value = [
        {
            "_id": fake_id,
            "timestamp": naive_dt,
            "cpu": {"usage_percent": 25.0},
            "memory": {"percent": 45.0},
            "disk": None,
            "network": None,
            "total_processes": 50,
        }
    ]

    results = query_historical_metrics(mock_db, limit=10)
    assert len(results) == 1
    item = results[0]
    assert isinstance(item, HistoricalSystemMetrics)
    assert item.id == str(fake_id)
    assert item.timestamp.tzinfo is not None
    assert item.cpu.usage_percent == 25.0


def test_aggregate_historical_metrics_empty():
    """Verify aggregate_historical_metrics handles empty collections correctly."""
    mock_db = MagicMock()
    mock_col = MagicMock()
    mock_db.__getitem__.return_value = mock_col
    mock_col.aggregate.return_value = []

    res = aggregate_historical_metrics(mock_db)
    assert isinstance(res, HistoricalMetricsSummary)
    assert res.sample_count == 0
    assert res.cpu_avg_percent is None
    assert res.memory_avg_percent is None


def test_aggregate_historical_metrics_with_data():
    """Verify aggregate_historical_metrics parses aggregation result correctly."""
    mock_db = MagicMock()
    mock_col = MagicMock()
    mock_db.__getitem__.return_value = mock_col
    mock_col.aggregate.return_value = [
        {
            "sample_count": 10,
            "min_timestamp": datetime(2026, 11, 13, 5, 0, 0),
            "max_timestamp": datetime(2026, 11, 13, 5, 1, 0),
            "cpu_avg_percent": 15.678,
            "cpu_max_percent": 25.0,
            "memory_avg_percent": 42.123,
            "memory_max_percent": 50.0,
            "network_avg_bytes_sent_per_sec": 1000.5,
            "network_avg_bytes_recv_per_sec": 2000.5,
        }
    ]

    res = aggregate_historical_metrics(mock_db)
    assert res.sample_count == 10
    assert res.cpu_avg_percent == 15.68
    assert res.cpu_max_percent == 25.0
    assert res.memory_avg_percent == 42.12
    assert res.memory_max_percent == 50.0
    assert res.network_avg_bytes_sent_per_sec == 1000.5
    assert res.network_avg_bytes_recv_per_sec == 2000.5


def test_api_get_history_empty():
    """Verify GET /api/v1/system/history returns empty list when no records exist."""
    mock_db = MagicMock()
    mock_col = MagicMock()
    mock_db.__getitem__.return_value = mock_col
    mock_col.find.return_value.sort.return_value.limit.return_value = []

    app.dependency_overrides[get_database] = lambda: mock_db
    client = TestClient(app)

    res = client.get("/api/v1/system/history")
    assert res.status_code == 200
    assert res.json() == []


def test_api_get_history_with_records():
    """Verify GET /api/v1/system/history returns serialized models without raw ObjectId."""
    mock_db = MagicMock()
    mock_col = MagicMock()
    mock_db.__getitem__.return_value = mock_col

    fake_id = ObjectId()
    mock_col.find.return_value.sort.return_value.limit.return_value = [
        {
            "_id": fake_id,
            "timestamp": datetime(2026, 11, 13, 5, 0, 0, tzinfo=UTC),
            "cpu": {"usage_percent": 20.0},
            "memory": {"percent": 40.0},
            "disk": None,
            "network": None,
            "total_processes": 30,
        }
    ]

    app.dependency_overrides[get_database] = lambda: mock_db
    client = TestClient(app)

    res = client.get("/api/v1/system/history")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["id"] == str(fake_id)
    assert "_id" not in data[0]
    assert data[0]["cpu"]["usage_percent"] == 20.0


def test_api_get_history_invalid_time_range():
    """Verify 400 Bad Request when start_time > end_time."""
    mock_db = MagicMock()
    app.dependency_overrides[get_database] = lambda: mock_db
    client = TestClient(app)

    now = datetime.now(UTC)
    earlier = now - timedelta(hours=1)
    now_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    earlier_str = earlier.strftime("%Y-%m-%dT%H:%M:%SZ")

    res = client.get(
        f"/api/v1/system/history?start_time={now_str}&end_time={earlier_str}"
    )
    assert res.status_code == 400
    assert "start_time cannot be greater than end_time" in res.json()["detail"]


def test_api_get_history_limit_validation():
    """Verify 422 Unprocessable Entity when limit is out of allowed bounds."""
    mock_db = MagicMock()
    app.dependency_overrides[get_database] = lambda: mock_db
    client = TestClient(app)

    res_zero = client.get("/api/v1/system/history?limit=0")
    assert res_zero.status_code == 422

    res_high = client.get("/api/v1/system/history?limit=1001")
    assert res_high.status_code == 422

    res_bad_order = client.get("/api/v1/system/history?order=random")
    assert res_bad_order.status_code == 422


def test_api_get_history_summary():
    """Verify GET /api/v1/system/history/summary returns aggregation model."""
    mock_db = MagicMock()
    mock_col = MagicMock()
    mock_db.__getitem__.return_value = mock_col
    mock_col.aggregate.return_value = [
        {
            "sample_count": 5,
            "min_timestamp": datetime(2026, 11, 13, 5, 0, 0, tzinfo=UTC),
            "max_timestamp": datetime(2026, 11, 13, 5, 5, 0, tzinfo=UTC),
            "cpu_avg_percent": 18.5,
            "cpu_max_percent": 30.0,
            "memory_avg_percent": 45.0,
            "memory_max_percent": 55.0,
            "network_avg_bytes_sent_per_sec": 500.0,
            "network_avg_bytes_recv_per_sec": 1000.0,
        }
    ]

    app.dependency_overrides[get_database] = lambda: mock_db
    client = TestClient(app)

    res = client.get("/api/v1/system/history/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["sample_count"] == 5
    assert data["cpu_avg_percent"] == 18.5
    assert data["cpu_max_percent"] == 30.0


def test_api_get_history_summary_invalid_time_range():
    """Verify 400 Bad Request for summary endpoint when start_time > end_time."""
    mock_db = MagicMock()
    app.dependency_overrides[get_database] = lambda: mock_db
    client = TestClient(app)

    now = datetime.now(UTC)
    earlier = now - timedelta(hours=1)
    now_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    earlier_str = earlier.strftime("%Y-%m-%dT%H:%M:%SZ")

    res = client.get(
        f"/api/v1/system/history/summary?start_time={now_str}&end_time={earlier_str}"
    )
    assert res.status_code == 400
    assert "start_time cannot be greater than end_time" in res.json()["detail"]


def test_api_history_database_unavailable_503():
    """Verify 503 Service Unavailable when MongoDB database is None."""
    # Ensure dependency returns None
    from app.database.mongodb import mongodb

    old_db = mongodb.database
    mongodb.database = None
    try:
        client = TestClient(app)
        res = client.get("/api/v1/system/history")
        assert res.status_code == 503
        assert "Database service is currently unavailable" in res.json()["detail"]
    finally:
        mongodb.database = old_db
