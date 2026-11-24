from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.api.dependencies import get_system_collector, reset_system_collector
from app.api.routes.system import (
    MAX_SAMPLING_INTERVAL_SECONDS,
    MIN_SAMPLING_INTERVAL_SECONDS,
)
from app.collectors.system import SystemMetricsCollector
from app.main import app
from app.schemas.metrics import (
    SystemMetrics,
)


@pytest.fixture(autouse=True)
def cleanup_collector():
    """Ensure persistent collector is cleanly reset before and after each test."""
    reset_system_collector()
    app.dependency_overrides.clear()
    yield
    reset_system_collector()
    app.dependency_overrides.clear()


def test_websocket_stream_success():
    """Verify that a WebSocket client receives real-time serialized SystemMetrics snapshots."""
    client = TestClient(app)
    with client.websocket_connect(
        f"/api/v1/system/ws?interval={MIN_SAMPLING_INTERVAL_SECONDS}"
    ) as ws:
        snapshot1 = ws.receive_json()
        assert "cpu" in snapshot1
        assert "memory" in snapshot1
        assert "disk" in snapshot1
        assert "network" in snapshot1
        assert "processes" in snapshot1
        assert "timestamp" in snapshot1

        # Verify timestamp is a valid ISO-8601 string
        parsed_ts = datetime.fromisoformat(snapshot1["timestamp"])
        assert parsed_ts.tzinfo is not None

        snapshot2 = ws.receive_json()
        assert "timestamp" in snapshot2


def test_websocket_serialized_metrics_structure():
    """Verify the structural integrity of serialized metrics received over WebSocket."""
    client = TestClient(app)
    with client.websocket_connect(
        f"/api/v1/system/ws?interval={MIN_SAMPLING_INTERVAL_SECONDS}"
    ) as ws:
        data = ws.receive_json()

        # Validate CPU metrics structure if collected
        if data["cpu"] is not None:
            assert "physical_cores" in data["cpu"]
            assert "logical_cores" in data["cpu"]
            assert "per_core_usage" in data["cpu"]
            assert "timestamp" in data["cpu"]

        # Validate Memory metrics structure if collected
        if data["memory"] is not None:
            assert "virtual" in data["memory"]
            assert "swap" in data["memory"]
            assert data["memory"]["virtual"]["total"] > 0
            assert 0.0 <= data["memory"]["virtual"]["percent"] <= 100.0

        # Validate Disk metrics structure if collected
        if data["disk"] is not None:
            assert "partitions" in data["disk"]
            assert isinstance(data["disk"]["partitions"], list)

        # Validate Network metrics structure if collected
        if data["network"] is not None:
            assert "interfaces" in data["network"]
            assert isinstance(data["network"]["interfaces"], list)

        # Validate Process metrics structure if collected
        if data["processes"] is not None:
            assert "processes" in data["processes"]
            assert "total_processes" in data["processes"]
            assert data["processes"]["total_processes"] >= 0


def test_websocket_default_interval():
    """Verify WebSocket connection succeeds without specifying interval parameter."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/system/ws") as ws:
        data = ws.receive_json()
        assert "timestamp" in data


def test_websocket_custom_valid_interval():
    """Verify WebSocket connection accepts valid custom intervals within range."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/system/ws?interval=0.5") as ws:
        data = ws.receive_json()
        assert "timestamp" in data


def test_websocket_interval_too_small_rejected():
    """Verify that intervals below MIN_SAMPLING_INTERVAL_SECONDS are rejected with WS 1008."""
    client = TestClient(app)
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect(
            f"/api/v1/system/ws?interval={MIN_SAMPLING_INTERVAL_SECONDS - 0.1}"
        ),
    ):
        pass
    assert exc_info.value.code == 1008


def test_websocket_interval_too_large_rejected():
    """Verify that intervals above MAX_SAMPLING_INTERVAL_SECONDS are rejected with WS 1008."""
    client = TestClient(app)
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect(
            f"/api/v1/system/ws?interval={MAX_SAMPLING_INTERVAL_SECONDS + 10.0}"
        ),
    ):
        pass
    assert exc_info.value.code == 1008


def test_websocket_interval_negative_rejected():
    """Verify that negative intervals are rejected with WS 1008."""
    client = TestClient(app)
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect("/api/v1/system/ws?interval=-1.0"),
    ):
        pass
    assert exc_info.value.code == 1008


def test_websocket_interval_non_numeric_rejected():
    """Verify that non-numeric intervals are rejected with WS 1008."""
    client = TestClient(app)
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect("/api/v1/system/ws?interval=invalid"),
    ):
        pass
    assert exc_info.value.code == 1008


def test_websocket_collector_reuse_with_rest():
    """Verify the persistent collector instance is shared between WebSocket and REST endpoints."""
    persistent_collector = get_system_collector()

    client = TestClient(app)
    with client.websocket_connect(
        f"/api/v1/system/ws?interval={MIN_SAMPLING_INTERVAL_SECONDS}"
    ) as ws:
        ws_data = ws.receive_json()
        assert "timestamp" in ws_data

        rest_response = client.get("/api/v1/system/cpu")
        assert rest_response.status_code == 200

    assert get_system_collector() is persistent_collector


def test_websocket_no_unintended_collector_recreation():
    """Verify multiple sequential WebSocket connections reuse the same collector instance."""
    initial_collector = get_system_collector()
    initial_id = id(initial_collector)

    client = TestClient(app)
    with client.websocket_connect(
        f"/api/v1/system/ws?interval={MIN_SAMPLING_INTERVAL_SECONDS}"
    ) as ws1:
        data1 = ws1.receive_json()
        assert "timestamp" in data1

    assert id(get_system_collector()) == initial_id

    with client.websocket_connect(
        f"/api/v1/system/ws?interval={MIN_SAMPLING_INTERVAL_SECONDS}"
    ) as ws2:
        data2 = ws2.receive_json()
        assert "timestamp" in data2

    assert id(get_system_collector()) == initial_id


def test_websocket_client_disconnect_handling():
    """Verify graceful handling when client disconnects after receiving a message."""
    client = TestClient(app)
    with client.websocket_connect(
        f"/api/v1/system/ws?interval={MIN_SAMPLING_INTERVAL_SECONDS}"
    ) as ws:
        data = ws.receive_json()
        assert "timestamp" in data
        # Exiting context triggers client disconnect; should cleanly shut down server loop


def test_websocket_multiple_concurrent_clients():
    """Verify multiple concurrent clients stream independently without contention."""
    client = TestClient(app)
    with (
        client.websocket_connect(
            f"/api/v1/system/ws?interval={MIN_SAMPLING_INTERVAL_SECONDS}"
        ) as ws1,
        client.websocket_connect(
            f"/api/v1/system/ws?interval={MIN_SAMPLING_INTERVAL_SECONDS}"
        ) as ws2,
    ):
        data1 = ws1.receive_json()
        data2 = ws2.receive_json()
        assert "timestamp" in data1
        assert "timestamp" in data2


def test_websocket_collection_failure_handling():
    """Verify server catches collection exceptions and transmits error frame without crashing."""
    failing_collector = MagicMock(spec=SystemMetricsCollector)
    failing_collector.collect_all.side_effect = RuntimeError(
        "Sensor hardware communication failed"
    )

    app.dependency_overrides[get_system_collector] = lambda: failing_collector

    client = TestClient(app)
    with client.websocket_connect(
        f"/api/v1/system/ws?interval={MIN_SAMPLING_INTERVAL_SECONDS}"
    ) as ws:
        msg = ws.receive_json()
        assert "error" in msg
        assert "Failed to collect system metrics" in msg["error"]


def test_websocket_partial_component_failures_streaming():
    """Verify streaming continues even when some subsystems report None due to failure isolation."""
    partial_collector = MagicMock(spec=SystemMetricsCollector)
    partial_collector.collect_all.return_value = SystemMetrics(
        cpu=None,
        memory=None,
        disk=None,
        network=None,
        processes=None,
        timestamp=datetime.now(UTC),
    )

    app.dependency_overrides[get_system_collector] = lambda: partial_collector

    client = TestClient(app)
    with client.websocket_connect(
        f"/api/v1/system/ws?interval={MIN_SAMPLING_INTERVAL_SECONDS}"
    ) as ws:
        data = ws.receive_json()
        assert data["cpu"] is None
        assert data["memory"] is None
        assert data["timestamp"] is not None


def test_existing_rest_endpoints_unaffected():
    """Verify all system REST endpoints remain functional alongside the WebSocket route."""
    client = TestClient(app)

    assert client.get("/").status_code == 200
    assert client.get("/api/v1/system/metrics").status_code == 200
    assert client.get("/api/v1/system/cpu").status_code == 200
    assert client.get("/api/v1/system/memory").status_code == 200
    assert client.get("/api/v1/system/disk").status_code == 200
    assert client.get("/api/v1/system/network").status_code == 200
    assert client.get("/api/v1/system/processes").status_code == 200
