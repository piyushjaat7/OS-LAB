from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.api.dependencies import get_system_collector, reset_system_collector
from app.main import app
from app.schemas.metrics import (
    CPUMetrics,
    DiskMetrics,
    MemoryMetrics,
    NetworkMetrics,
    ProcessCollectionMetrics,
    ProcessMetrics,
    SwapMemoryMetrics,
    SystemMetrics,
    VirtualMemoryMetrics,
)


def _build_dummy_cpu() -> CPUMetrics:
    return CPUMetrics(
        usage_percent=25.0,
        per_core_usage=[20.0, 30.0],
        physical_cores=2,
        logical_cores=4,
    )


def _build_dummy_memory() -> MemoryMetrics:
    vm = VirtualMemoryMetrics(
        total=8000000000,
        available=4000000000,
        used=4000000000,
        free=4000000000,
        percent=50.0,
    )
    sm = SwapMemoryMetrics(total=0, used=0, free=0, percent=0.0, sin=0, sout=0)
    return MemoryMetrics(virtual=vm, swap=sm)


def _build_dummy_disk() -> DiskMetrics:
    return DiskMetrics(partitions=[], io_counters=None)


def _build_dummy_network() -> NetworkMetrics:
    return NetworkMetrics(interfaces=[], io_counters=None, throughput=None)


def _build_dummy_processes() -> ProcessCollectionMetrics:
    p = ProcessMetrics(
        pid=123,
        name="test_proc",
        status="running",
        cpu_percent=5.0,
        memory_rss=10000,
        memory_vms=20000,
        memory_percent=0.1,
        num_threads=2,
        create_time=1700000000.0,
        username="test_user",
    )
    return ProcessCollectionMetrics(processes=[p], total_processes=1)


def _build_dummy_system() -> SystemMetrics:
    return SystemMetrics(
        cpu=_build_dummy_cpu(),
        memory=_build_dummy_memory(),
        disk=_build_dummy_disk(),
        network=_build_dummy_network(),
        processes=_build_dummy_processes(),
    )


def test_root_endpoint_unaffected():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_route_registration():
    openapi_paths = app.openapi()["paths"]
    expected_prefixes = [
        "/api/v1/system/metrics",
        "/api/v1/system/cpu",
        "/api/v1/system/memory",
        "/api/v1/system/disk",
        "/api/v1/system/network",
        "/api/v1/system/processes",
        "/api/v1/system/processes/{pid}",
    ]
    for prefix in expected_prefixes:
        assert prefix in openapi_paths


def test_get_system_metrics_endpoint_success():
    mock_collector = MagicMock()
    mock_collector.collect_all.return_value = _build_dummy_system()

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/system/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data
        assert "processes" in data
        assert "timestamp" in data
        assert data["cpu"]["usage_percent"] == 25.0
        assert data["memory"]["virtual"]["total"] == 8000000000
    finally:
        app.dependency_overrides.clear()


def test_get_cpu_endpoint_success():
    mock_collector = MagicMock()
    mock_collector.collect_cpu.return_value = _build_dummy_cpu()

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/system/cpu")
        assert response.status_code == 200
        data = response.json()
        assert data["usage_percent"] == 25.0
        assert data["physical_cores"] == 2
        assert data["logical_cores"] == 4
    finally:
        app.dependency_overrides.clear()


def test_get_cpu_endpoint_unavailable_503():
    mock_collector = MagicMock()
    mock_collector.collect_cpu.return_value = None

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/system/cpu")
        assert response.status_code == 503
        assert response.json()["detail"] == "CPU metrics are currently unavailable"
    finally:
        app.dependency_overrides.clear()


def test_get_memory_endpoint_success():
    mock_collector = MagicMock()
    mock_collector.collect_memory.return_value = _build_dummy_memory()

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/system/memory")
        assert response.status_code == 200
        data = response.json()
        assert data["virtual"]["total"] == 8000000000
        assert data["virtual"]["percent"] == 50.0
        assert data["swap"]["total"] == 0
    finally:
        app.dependency_overrides.clear()


def test_get_memory_endpoint_unavailable_503():
    mock_collector = MagicMock()
    mock_collector.collect_memory.return_value = None

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/system/memory")
        assert response.status_code == 503
        assert response.json()["detail"] == "Memory metrics are currently unavailable"
    finally:
        app.dependency_overrides.clear()


def test_get_disk_endpoint_success():
    mock_collector = MagicMock()
    mock_collector.collect_disk.return_value = _build_dummy_disk()

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/system/disk")
        assert response.status_code == 200
        data = response.json()
        assert "partitions" in data
        assert data["partitions"] == []
    finally:
        app.dependency_overrides.clear()


def test_get_disk_endpoint_unavailable_503():
    mock_collector = MagicMock()
    mock_collector.collect_disk.return_value = None

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/system/disk")
        assert response.status_code == 503
        assert response.json()["detail"] == "Disk metrics are currently unavailable"
    finally:
        app.dependency_overrides.clear()


def test_get_network_endpoint_success():
    mock_collector = MagicMock()
    mock_collector.collect_network.return_value = _build_dummy_network()

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/system/network")
        assert response.status_code == 200
        data = response.json()
        assert "interfaces" in data
        assert data["interfaces"] == []
    finally:
        app.dependency_overrides.clear()


def test_get_network_endpoint_unavailable_503():
    mock_collector = MagicMock()
    mock_collector.collect_network.return_value = None

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/system/network")
        assert response.status_code == 503
        assert response.json()["detail"] == "Network metrics are currently unavailable"
    finally:
        app.dependency_overrides.clear()


def test_get_processes_endpoint_success():
    mock_collector = MagicMock()
    mock_collector.collect_processes.return_value = _build_dummy_processes()

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/system/processes")
        assert response.status_code == 200
        data = response.json()
        assert data["total_processes"] == 1
        assert len(data["processes"]) == 1
        assert data["processes"][0]["pid"] == 123
        assert data["processes"][0]["name"] == "test_proc"
    finally:
        app.dependency_overrides.clear()


def test_get_processes_endpoint_unavailable_503():
    mock_collector = MagicMock()
    mock_collector.collect_processes.return_value = None

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/system/processes")
        assert response.status_code == 503
        assert (
            response.json()["detail"]
            == "Process collection metrics are currently unavailable"
        )
    finally:
        app.dependency_overrides.clear()


def test_get_process_by_pid_success():
    proc = ProcessMetrics(
        pid=123,
        name="target_proc",
        status="running",
        cpu_percent=10.0,
        memory_rss=50000,
        memory_vms=80000,
    )
    mock_collector = MagicMock()
    mock_collector.collect_process.return_value = proc

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/system/processes/123")
        assert response.status_code == 200
        data = response.json()
        assert data["pid"] == 123
        assert data["name"] == "target_proc"
        assert data["status"] == "running"
        assert data["cpu_percent"] == 10.0
    finally:
        app.dependency_overrides.clear()


def test_get_process_by_pid_not_found_404():
    mock_collector = MagicMock()
    mock_collector.collect_process.return_value = None

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/system/processes/999999")
        assert response.status_code == 404
        assert "not found or inaccessible" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_get_process_by_pid_negative_404():
    mock_collector = MagicMock()

    app.dependency_overrides[get_system_collector] = lambda: mock_collector
    try:
        client = TestClient(app)
        response = client.get("/api/v1/system/processes/-1")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_persistent_collector_dependency_singleton():
    reset_system_collector()
    c1 = get_system_collector()
    c2 = get_system_collector()
    assert c1 is c2
    reset_system_collector()
