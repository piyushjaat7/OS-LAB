# System Architecture & Technical Design

## Integrated OS Performance Analyzer

### 1. Architectural Philosophy & Design Principles

The **Integrated OS Performance Analyzer** is structured around four non-negotiable architectural tenets:

1. **Non-Blocking Telemetry & Continuous Baselines**:
   Hardware and kernel counters in operating systems (such as CPU time deltas, network throughput, and process utilization) require differential sampling. Rather than stalling HTTP worker threads with blocking sleep calls (e.g. `psutil.cpu_percent(interval=1.0)`), the application maintains persistent collector singletons initialized at startup. All sampling calls pass `interval=None`, instantaneously computing deltas against the previous timestamp.

2. **Component-Level Failure Isolation**:
   Subsystems must never fail as a monolithic block. If the storage subsystem encounters an unreadable partition or the network collector encounters an unsupported interface address family, only that specific node defaults to `None`. The overall metric payload continues streaming with full data integrity.

3. **Decoupled Historical Persistence**:
   Persisting metrics into MongoDB must operate completely asynchronously and out-of-band from user-facing REST requests or WebSocket connections. A dedicated `MetricsPersistenceService` background worker polls the persistent collector at regular intervals, transforms snapshots to omit unbounded per-process lists, and writes lean documents indexed by descending UTC timestamps.

4. **Zero Process Mutation & Safe Observation**:
   The engine acts strictly as an analytical observer and simulator. It does not manipulate real kernel scheduler priorities, task niceness, or kill processes. All algorithmic CPU scheduling is executed in a dedicated, pure simulation sandbox.

---

### 2. High-Level System Architecture Diagram

```
+-----------------------------------------------------------------------------------------+
|                                    USER INTERFACE                                       |
|                  React 19 + TypeScript + Vite + Tailwind CSS + Recharts                 |
+----------------------------+-----------------------------------+------------------------+
                             | HTTP REST                         | WebSocket Stream
                             v                                   v
+-----------------------------------------------------------------------------------------+
|                               FASTAPI APPLICATION TIER                                  |
|                                                                                         |
|  +--------------------+  +--------------------+  +-----------------------------------+  |
|  |   System Routes    |  |   History Routes   |  |         Analysis Routes           |  |
|  | (/api/v1/system/*) |  | (/api/v1/system/   |  |       (/api/v1/analysis/*)        |  |
|  |                    |  |       history/*)   |  |                                   |  |
|  +---------+----------+  +---------+----------+  +---+---------------------------+---+  |
|            |                       |                 |                           |      |
|            |                       |                 v                           v      |
|            |                       |     +-----------------------+   +---------------+  |
|            |                       |     | Performance Analyzer  |   | CPU Scheduler |  |
|            |                       |     | & Bottleneck Detector |   |   Simulator   |  |
|            |                       |     +-----------+-----------+   +---------------+  |
+------------|-----------------------|-----------------|----------------------------------+
             |                       |                 |
             v                       |                 v
+-------------------------------+    |    +-----------------------------+
|    SystemMetricsCollector     |    |    |  MongoDB Persistence Tier   |
| (Application-Scoped Singleton)|    |    |                             |
|  - CPUCollector               |<---+    |  Database:                  |
|  - MemoryCollector            |         |    os_performance_analyzer  |
|  - DiskCollector              |         |  Collection:                |
|  - NetworkCollector           |         |    system_metrics_history   |
|  - ProcessCollector           |         |  Index:                     |
+---------------+---------------+         |    {"timestamp": -1}        |
                |                         +--------------+--------------+
                v                                        ^
+-------------------------------+                        |
|       Operating System        |                        |
| (psutil / procfs / Win32 API) |------------------------+
+-------------------------------+  Background Worker (`MetricsPersistenceService`)
```

---

### 3. Subsystem Breakdown

#### 3.1 Collector Architecture (`backend/app/collectors/`)
- **`CPUCollector`**:
  - Samples `psutil.cpu_times()` and `psutil.cpu_times(percpu=True)`.
  - Calculates delta: $\Delta \text{busy} = \Delta \text{total} - \Delta \text{idle} - \Delta \text{iowait}$.
  - Adheres to first-reading semantics: First snapshot returns `usage_percent = None`; subsequent reads return true utilization. Genuine idle reads return `0.0`.
- **`MemoryCollector`**:
  - Queries `psutil.virtual_memory()` and `psutil.swap_memory()`.
  - Extracts total, available, used, free, percentage, and swap in/out paging rates.
- **`DiskCollector`**:
  - Discovers physical partitions with `psutil.disk_partitions(all=False)`.
  - Prunes in-memory/pseudo filesystems (`tmpfs`, `devtmpfs`, `sysfs`, `proc`) via `PSEUDO_FS_TYPES`.
  - Deduplicates bind-mounts and aggregates cumulative disk I/O counters (`read_bytes`, `write_bytes`, `read_count`, `write_count`).
- **`NetworkCollector`**:
  - Discovers interfaces and operational status (`is_up`, `speed`, `mtu`).
  - Filters out raw host IP addresses to protect privacy while retaining hardware MAC strings and family flags.
  - Dynamically computes throughput deltas:
    $$\text{Rate (bytes/sec)} = \frac{\Delta \text{bytes}}{\Delta t}$$
- **`ProcessCollector`**:
  - Caches `proc.cpu_percent(None)` instances across polling passes to eliminate blocking.
  - Detects PID recycling by validating process creation timestamps (`create_time`).
  - Protects privacy by extracting only base executable names (`os.path.basename`) and omitting command-line arguments and environment variables.
  - Actively purges terminated PIDs from instance cache to prevent memory leaks.

#### 3.2 Analytical Engine (`backend/app/analyzers/`)
- **Health Scoring (`health.py`)**:
  - Model begins at baseline 100 points.
  - Penalties are deducted proportionally for sustained elevated loads ($>75\%$), saturation ($>90\%$), swap thrashing ($>20\%$), disk partition exhaustion ($>85\%$), and packet drops.
  - Produces subsystem operational state: `OPTIMAL`, `NORMAL`, `ELEVATED`, `WARNING`, `CRITICAL`.
- **Bottleneck Detection (`bottlenecks.py`)**:
  - Inspects active hardware constraints.
  - Detects single-core pegging (100% on one core even if overall CPU is moderate).
  - Detects swap thrashing and out-of-memory hazard conditions.
  - Evaluates network transmission drops and socket buffer overruns.
  - Correlates with MongoDB historical documents (last 60 records) to differentiate temporary spikes from sustained saturation.

#### 3.3 CPU Scheduling Engine (`backend/app/algorithms/`)
- Completely decoupled, pure Python simulation engine.
- Implements:
  1. **First-Come First-Served (FCFS)** (Non-preemptive)
  2. **Shortest Job First (SJF)** (Non-preemptive with deterministic tie-breaking)
  3. **Shortest Remaining Time First (SRTF)** (Preemptive)
  4. **Priority Scheduling** (Preemptive and Non-preemptive with configurable priority polarity)
  5. **Round Robin (RR)** (Configurable time quantum and ready-queue cycling)
- Generates continuous, non-overlapping Gantt timeline segments, tracking explicit `IDLE` slots when no tasks are ready.
- Computes $CT$, $TAT$, $WT$, $RT$, CPU Utilization %, and Throughput.

#### 3.4 MongoDB Persistence Engine (`backend/app/services/`)
- Singleton `MetricsPersistenceService` started inside FastAPI's async lifespan context.
- Periodically gathers unified snapshots and stores documents structured as follows:
  ```json
  {
    "timestamp": "2026-11-13T07:06:59.519421Z",
    "cpu": { "usage_percent": 5.5, "per_core_usage": [...], ... },
    "memory": { "percent": 44.3, "used_bytes": 3500000000, ... },
    "disk": { "percent": 0.7, "read_bytes": 1024000, ... },
    "network": { "throughput_recv_bytes_per_sec": 12500.0, ... },
    "total_processes": 142
  }
  ```
- Fast querying ensured via compound descending index on `timestamp`.

---

### 4. Concurrency & Threading Model

- FastAPI async route handlers manage non-blocking I/O.
- Because `psutil` and `pymongo` communicate with the OS kernel and network sockets synchronously, all metric gathering and database calls are executed via `starlette.concurrency.run_in_threadpool`.
- This ensures the main asyncio event loop is never blocked, allowing high-concurrency WebSocket broadcast loops and REST requests to proceed simultaneously.
