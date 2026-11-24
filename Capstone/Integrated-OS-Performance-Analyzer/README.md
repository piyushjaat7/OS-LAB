# Integrated OS Performance Analyzer

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0+-61DAFB?style=flat&logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-3178C6?style=flat&logo=typescript)](https://www.typescriptlang.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-47A248?style=flat&logo=mongodb)](https://www.mongodb.com)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python)](https://www.python.org)
[![Vite](https://img.shields.io/badge/Vite-6.2+-646CFF?style=flat&logo=vite)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4+-06B6D4?style=flat&logo=tailwindcss)](https://tailwindcss.com)

A cross-platform operating system performance monitoring, heuristic bottleneck detection, and algorithmic CPU scheduling simulation platform. Built as a B.Tech Computer Science Capstone Project.

---

## 1. Project Overview & Problem Statement

### Problem Statement
Standard operating system resource monitors (such as Windows Task Manager or Linux top/htop) provide raw instantaneous utilization figures without contextual analytical intelligence. They do not correlate multi-subsystem pressure, fail to identify root-cause hardware bottlenecks, cannot correlate transient spikes with long-term historical records out-of-the-box, and offer no educational link between real-time OS telemetry and classic operating system process scheduling theory.

### Project Objective
The **Integrated OS Performance Analyzer** bridges real-world systems telemetry and theoretical operating systems concepts:
1. **Real-Time Telemetry**: Non-blocking observation of CPU, Memory, Disk, Network, and Process subsystems.
2. **Failure Isolation**: Component-level fault tolerance ensuring individual subsystem errors do not crash monitoring.
3. **Historical Persistence**: Asynchronous, background time-series metrics logging into MongoDB with compound index optimization.
4. **Heuristic Performance Engine**: Automated 0–100 health scoring, resource classification, and bottleneck saturation diagnosis correlated with historical trends.
5. **Algorithmic CPU Scheduling Sandbox**: Pure Python execution of classic operating system scheduling algorithms (FCFS, SJF, SRTF, Priority, Round Robin) with interactive Gantt timeline charts and multi-algorithm comparative benchmarks.

---

## 2. Key Features

- **CPU Telemetry**: System-wide utilization, per-core load visualizer, physical/logical core discovery, and clock frequency tracking.
- **Memory & Swap**: Physical RAM utilization, used/available/free breakdown, swap space consumption, and swap in/out page rates.
- **Disk & Storage**: Physical partition discovery, mount point capacity analysis, in-memory pseudo-fs filtering, and cumulative disk I/O rates.
- **Network Throughput**: Network interface enumeration, link state, MTU, packet drop/error detection, safe address extraction (IP privacy preservation), and calculated bytes/sec throughput deltas.
- **Process Management**: Top resource-consuming processes, real-time search, sorting, pagination, and inspection modal with PID recycling protection and privacy shielding.
- **WebSocket Push Streaming**: Full-duplex live metrics streaming at configurable intervals (0.5s to 60.0s) with automatic client disconnect handling.
- **Autonomous MongoDB Persistence**: Independent background worker logging time-series metrics snapshots every 5 seconds without blocking user requests.
- **Performance Analysis & Health Scoring**: Mathematically calibrated 0–100 health score, subsystem operational states, critical alerts, and actionable remediation steps.
- **Hardware Bottleneck Detection**: Heuristic identification of CPU saturation, memory thrashing, partition exhaustion, and network buffer overruns correlated against historical records.
- **Interactive CPU Scheduling Simulator**:
  - First-Come First-Served (FCFS)
  - Shortest Job First (SJF - Non-Preemptive)
  - Shortest Remaining Time First (SRTF - Preemptive)
  - Priority Scheduling (Preemptive & Non-Preemptive, customizable priority polarity)
  - Round Robin (Configurable time quantum)
  - Interactive, color-coded Gantt chart timeline with idle intervals and tooltip inspection.
  - Multi-Algorithm comparative benchmark and automated workload analysis.

---

## 3. Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.12, FastAPI, Pydantic v2, `psutil`, `pymongo`, `uvicorn`, `anyio` / `starlette` |
| **Database** | MongoDB 7.0+ (with descending timestamp index optimization) |
| **Frontend** | React 19, TypeScript, Vite 6, Tailwind CSS, Recharts, Lucide React |
| **Tooling & Tests** | `uv` (Fast Python package manager), `pytest`, `ruff` (linter/formatter), `vitest` |

---

## 4. System Architecture

```
                                  +------------------------------------+
                                  |     React 19 Frontend Dashboard    |
                                  | (Overview, Telemetry, Sched, Perf) |
                                  +-----------------+------------------+
                                                    | HTTP REST / WebSockets
                                                    v
+------------------------------------------------------------------------------------------------------+
| FastAPI Application Layer (`backend/app/main.py`)                                                    |
|                                                                                                      |
|  +--------------------+  +--------------------+  +--------------------+  +------------------------+  |
|  |   System Routes    |  |   History Routes   |  |   Analysis Routes  |  |  Scheduling Endpoints  |  |
|  | (/api/v1/system/*) |  | (/api/v1/system/   |  | (/api/v1/analysis/ |  | (/api/v1/analysis/     |  |
|  | - Live REST        |  |        history/*)  |  |        health,     |  |   scheduling/*)        |  |
|  | - WebSocket Stream |  | - Query & Summary  |  |        bottlenecks)|  | - FCFS, SJF, SRTF, RR  |  |
|  +---------+----------+  +---------+----------+  +---------+----------+  +-----------+------------+  |
+------------|-----------------------|-----------------------|-------------------------|---------------+
             |                       |                       |                         |
             v                       |                       v                         v
+-------------------------------+    |           +-----------------------+ +-----------------------+
|    SystemMetricsCollector     |    |           |   Analytical Engine   | | CPU Scheduling Engine |
| (Application-Scoped Singleton)|<---+           | - Health Scoring      | | - Gantt Chart Synth   |
|  - CPUCollector               |                | - Bottleneck Detector | | - Metric Computation  |
|  - MemoryCollector            |                +-----------+-----------+ +-----------------------+
|  - DiskCollector              |                            |
|  - NetworkCollector           |                            v
|  - ProcessCollector           |                +-----------------------+
+---------------+---------------+                | MongoDB Persistence   |
                |                                | - Timeseries History  |
                v                                | - Descending Index    |
+-------------------------------+                +-----------------------+
|  Operating System Subsystems  |
|  (Linux kernel / Win32 API)   |
+-------------------------------+
```

---

## 5. Repository Structure

```
Integrated-OS-Performance-Analyzer/
├── backend/                         # FastAPI Backend
│   ├── app/
│   │   ├── algorithms/              # Pure CPU Scheduling Simulation Engine
│   │   │   ├── __init__.py
│   │   │   └── scheduling.py        # FCFS, SJF, SRTF, Priority, RR & Comparison
│   │   ├── analyzers/               # Analytical & Diagnostic Engines
│   │   │   ├── __init__.py
│   │   │   ├── bottlenecks.py       # Bottleneck Detection & Historical Correlation
│   │   │   └── health.py            # Health Score & Subsystem Classification
│   │   ├── api/                     # REST & WebSocket Route Handlers
│   │   │   ├── dependencies.py      # Dependency Injection (Collector & DB)
│   │   │   └── routes/
│   │   │       ├── analysis.py      # Health, Bottlenecks & Scheduling Routes
│   │   │       ├── history.py       # MongoDB Query & Aggregation Routes
│   │   │       └── system.py        # System Telemetry & WebSocket Stream
│   │   ├── collectors/              # Non-blocking psutil Hardware Collectors
│   │   │   ├── cpu.py               # CPU & Core Metrics
│   │   │   ├── disk.py              # Partition & Disk I/O Metrics
│   │   │   ├── memory.py            # Virtual & Swap Memory Metrics
│   │   │   ├── network.py           # Network Interface & Throughput Metrics
│   │   │   ├── process.py           # Process Telemetry & Cache Management
│   │   │   └── system.py            # Consolidated System Collector
│   │   ├── core/                    # Application Configuration & Settings
│   │   ├── database/                # MongoDB Connection Lifecycle Manager
│   │   ├── schemas/                 # Pydantic v2 Models & API Contracts
│   │   ├── services/                # Background Persistence Worker
│   │   └── main.py                  # Application Entrypoint & Lifespan
│   ├── tests/                       # 207 Automated Pytest Test Cases
│   ├── pyproject.toml               # Python Dependencies & Metadata
│   └── uv.lock                      # Deterministic Python Lockfile
├── frontend/                        # React 19 Frontend
│   ├── src/
│   │   ├── components/              # Modular UI Components
│   │   │   ├── charts/              # GanttChart, LiveAreaChart, CoreUsageGrid
│   │   │   ├── common/              # MetricCards, StatusPills, Spinners
│   │   │   └── layout/              # Sidebar & TopNav
│   │   ├── context/                 # MetricsContext & Live Buffer Management
│   │   ├── pages/                   # Overview, CPU, Memory, Disk, Net, Process,
│   │   │                            # History, Analysis, Scheduling, Settings
│   │   ├── services/                # HTTP API Client & WebSocket Service
│   │   ├── types/                   # TypeScript Interfaces & API Contracts
│   │   ├── utils/                   # Unit & DateTime Formatters
│   │   └── __tests__/               # Vitest Unit Tests
│   ├── vite.config.ts               # Vite Config with Vendor Chunk Splitting
│   ├── package.json                 # Node.js Dependencies & Scripts
│   └── tailwind.config.js           # Tailwind CSS Configuration
└── docs/                            # Comprehensive Project Documentation
    ├── ALGORITHMS.md                # Mathematical Definitions & Scheduling Theory
    ├── API_REFERENCE.md             # Complete REST & WebSocket API Specification
    ├── ARCHITECTURE.md              # In-Depth Subsystem Design Document
    └── DEMO_GUIDE.md                # Viva & Capstone Defense Step-by-Step Script
```

---

## 6. Installation & Execution Guide

### Prerequisites
- Python 3.12+ with `uv` (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Node.js 18+ and `npm`
- MongoDB 7.0+ running on `localhost:27017`

### 1. Database Setup
Start the local MongoDB daemon:
```bash
# Ubuntu / Debian / WSL2:
sudo systemctl start mongod || sudo service mongodb start

# macOS:
brew services start mongodb-community

# Windows:
net start MongoDB
```

### 2. Backend Setup
```bash
cd backend

# Install dependencies and sync virtual environment
uv sync

# Run the backend development server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The FastAPI backend will start at `http://localhost:8000`. Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

### 3. Frontend Setup
In a new terminal window:
```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
The application dashboard is available at `http://localhost:5173`.

---

## 7. Testing & Quality Assurance

### Backend Automated Test Suite (207 Tests)
```bash
cd backend
uv run pytest -v
```

### Backend Linting & Formatting Check
```bash
cd backend
uv run ruff check .
uv run ruff format --check .
```

### Frontend Unit Tests & Production Build
```bash
cd frontend
npm test
npm run build
```

---

## 8. Cross-Platform Behavior & Limitations

| Platform | Capabilities & Validation Status | Platform-Specific Notes |
|---|---|---|
| **Ubuntu Linux (WSL2)** | **Fully Tested & Verified** | Reflects WSL2 virtualized environment. Frequency may return `None` if virtual kernel does not expose `/sys/devices/system/cpu/cpufreq`. Partitions reflect virtual mounts. |
| **Native Linux** | **Fully Supported** | Direct bare-metal access to `/proc`, `/sys`, physical block devices (`/dev/sda`), and native network interfaces. |
| **Native Windows** | **Fully Supported Architecture** | Mount points map to drive letters (`C:\`, `D:\`). Filesystems report `NTFS`/`FAT32`. Process usernames format as `DOMAIN\User`. |

---

## 9. College Demonstration Guide

For a step-by-step walkthrough script for examiners, sample scheduling workloads, and viva troubleshooting, refer to [docs/DEMO_GUIDE.md](file:///home/piyush_rathi/os-lab/Capstone/Integrated-OS-Performance-Analyzer/docs/DEMO_GUIDE.md).

For formal scheduling equations and analysis rules, refer to [docs/ALGORITHMS.md](file:///home/piyush_rathi/os-lab/Capstone/Integrated-OS-Performance-Analyzer/docs/ALGORITHMS.md).

For the full REST/WebSocket specification, refer to [docs/API_REFERENCE.md](file:///home/piyush_rathi/os-lab/Capstone/Integrated-OS-Performance-Analyzer/docs/API_REFERENCE.md).

---

## 10. License

Developed for academic capstone presentation under the MIT License.
