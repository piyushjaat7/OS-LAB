# REST & WebSocket API Specification

## Base URL
- Local Development: `http://localhost:8000`
- WebSocket Endpoint: `ws://localhost:8000`

---

## 1. System Health & Infrastructure

### `GET /`
Returns service identification and application state.
- **Response**: `200 OK`
  ```json
  {
    "application": "Integrated OS Performance Analyzer",
    "version": "0.1.0",
    "status": "running"
  }
  ```

### `GET /health`
Validates MongoDB database connectivity and application status.
- **Response**: `200 OK` (Healthy)
  ```json
  {
    "status": "healthy",
    "database": "connected"
  }
  ```
- **Error Response**: `503 Service Unavailable` if MongoDB is unreachable.

---

## 2. Real-Time System Metrics (`/api/v1/system`)

### `GET /api/v1/system/metrics`
Retrieve an instant, unified snapshot across CPU, Memory, Disk, Network, and Processes.
- **Response**: `200 OK` (`SystemMetrics`)

### `GET /api/v1/system/cpu`
Retrieve current CPU telemetry including frequency, core counts, and per-core utilization percentages.
- **Response**: `200 OK` (`CPUMetrics`)

### `GET /api/v1/system/memory`
Retrieve virtual memory (RAM) and swap memory statistics.
- **Response**: `200 OK` (`MemoryMetrics`)

### `GET /api/v1/system/disk`
Retrieve mounted filesystem partitions, used/free capacities, and cumulative I/O counters.
- **Response**: `200 OK` (`DiskMetrics`)

### `GET /api/v1/system/network`
Retrieve operational network interfaces, link speeds, MTU, and throughput rates.
- **Response**: `200 OK` (`NetworkMetrics`)

### `GET /api/v1/system/processes`
Retrieve running processes and snapshot metadata.
- **Response**: `200 OK` (`ProcessCollectionMetrics`)

### `GET /api/v1/system/processes/{pid}`
Retrieve resource telemetry for a specific process ID.
- **Response**: `200 OK` (`ProcessMetrics`)
- **Error Response**: `404 Not Found` if PID does not exist.

### `WS /api/v1/system/ws`
Full-duplex WebSocket stream broadcasting continuous `SystemMetrics` snapshots.
- **Query Parameters**:
  - `interval` (float, optional, default: `1.0`): Streaming interval in seconds ($0.5 \le \text{interval} \le 60.0$).
- **Output Frame**: Serialized JSON string of `SystemMetrics`.

---

## 3. Historical Telemetry (`/api/v1/system/history`)

### `GET /api/v1/system/history`
Retrieve stored chronological system metric snapshots from MongoDB.
- **Query Parameters**:
  - `start_time` (ISO-8601 string, optional): Filter snapshots $\ge$ timestamp.
  - `end_time` (ISO-8601 string, optional): Filter snapshots $\le$ timestamp.
  - `limit` (integer, optional, default: `100`, max: `1000`): Maximum records.
  - `order` (string, optional, default: `"desc"`): `"asc"` or `"desc"`.
- **Response**: `200 OK` (`list[HistoricalSystemMetrics]`)

### `GET /api/v1/system/history/summary`
Retrieve aggregated statistical metrics (average/peak CPU, average/peak RAM, average network throughput) over an optional time window.
- **Response**: `200 OK` (`HistoricalMetricsSummary`)

---

## 4. Performance Analysis & Bottlenecks (`/api/v1/analysis`)

### `GET /api/v1/analysis/health`
Evaluates live telemetry to calculate a 0–100 health score, operational status, resource classifications, warnings, critical alerts, and actionable recommendations.
- **Response**: `200 OK` (`SystemHealthAnalysis`)

### `GET /api/v1/analysis/bottlenecks`
Analyzes active hardware constraints and correlates with recent MongoDB historical records to detect sustained vs transient pressure across CPU, memory, disk, and network subsystems.
- **Response**: `200 OK` (`BottlenecksResponse`)

---

## 5. CPU Scheduling Simulations (`/api/v1/analysis/scheduling`)

### Common Workload Request Schema:
```json
{
  "processes": [
    { "process_id": "P1", "arrival_time": 0.0, "burst_time": 4.0, "priority": 1 },
    { "process_id": "P2", "arrival_time": 1.0, "burst_time": 3.0, "priority": 2 }
  ]
}
```

### `POST /api/v1/analysis/scheduling/fcfs`
Runs non-preemptive First-Come First-Served simulation.
- **Response**: `200 OK` (`SimulationResult`)

### `POST /api/v1/analysis/scheduling/sjf`
Runs non-preemptive Shortest Job First simulation with deterministic tie-breaking.
- **Response**: `200 OK` (`SimulationResult`)

### `POST /api/v1/analysis/scheduling/srtf`
Runs preemptive Shortest Remaining Time First simulation.
- **Response**: `200 OK` (`SimulationResult`)

### `POST /api/v1/analysis/scheduling/priority`
Runs Priority scheduling simulation.
- **Parameters**:
  - `preemptive` (boolean, optional, default: `false`)
  - `priority_order` (string, optional, default: `"lower_is_higher"`): `"lower_is_higher"` or `"higher_is_higher"`.
- **Response**: `200 OK` (`SimulationResult`)

### `POST /api/v1/analysis/scheduling/round-robin`
Runs Round Robin scheduling simulation.
- **Parameters**:
  - `time_quantum` (float, optional, default: `2.0`, $> 0$)
- **Response**: `200 OK` (`SimulationResult`)

### `POST /api/v1/analysis/scheduling/compare`
Runs an automated multi-algorithm comparison benchmark of all 5 schedulers against the exact same workload and generates comparative summary metrics and trade-off analysis.
- **Response**: `200 OK` (`SchedulingComparison`)
