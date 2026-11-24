# College Capstone Demonstration & Evaluation Guide

## Integrated OS Performance Analyzer

This guide is designed for presentation and evaluation before a university capstone committee or academic examiner. It provides a structured, live demonstration sequence, sample test workloads, expected observations, and quick troubleshooting steps.

---

## 1. Pre-Demonstration Checklist & Environment Setup

### Prerequisites:
- **OS**: Ubuntu 24.04 (WSL2 or Native Linux) or Windows 10/11.
- **Python**: 3.12+ with `uv` package manager installed.
- **Node.js**: v18+ with `npm`.
- **Database**: MongoDB running locally on port 27017 (`mongodb://localhost:27017`).

### Startup Steps:

#### Step 1: Start MongoDB
Ensure MongoDB is running locally:
```bash
sudo systemctl start mongod || sudo service mongodb start
```
Verify connectivity:
```bash
mongosh --eval "db.adminCommand('ping')"
```

#### Step 2: Start the FastAPI Backend
From the project root:
```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Expected log output:*
- MongoDB connection established.
- Historical metrics persistence worker started (interval: 5.00s).
- Application startup complete on `http://0.0.0.0:8000`.

#### Step 3: Start the React Frontend
In a separate terminal from the project root:
```bash
cd frontend
npm run dev
```
*Expected log output:*
- Vite dev server running at `http://localhost:5173/`.

#### Step 4: Open the Dashboard
Navigate to `http://localhost:5173` in any modern web browser.

---

## 2. Live Demonstration Sequence (Step-by-Step)

### Demo Part 1: Real-Time Operating System Monitoring
1. **Overview Page (`/`)**:
   - Point out the **Live Subsystem Telemetry** cards: CPU utilization, Memory footprint, Storage capacity, and Network throughput.
   - Note the **System Connection Pill**: displays green `WebSocket: Connected` indicating full-duplex live streaming.
   - Highlight the **Live Area Trend Charts**: smooth real-time telemetry streaming at 1-second intervals without page reloads.
2. **CPU Monitoring Page (`/cpu`)**:
   - Showcase the **Logical Core Grid**: per-core CPU utilization visualizer.
   - Point out physical vs logical core discovery and clock frequency reporting.
3. **Memory Monitoring Page (`/memory`)**:
   - Show virtual memory breakdown (RAM total, used, available, free).
   - Show swap space monitoring (used vs total, swap in/out page rates).
4. **Disk & Network Pages (`/disk`, `/network`)**:
   - Disk: Shows physical mount points, file system types (`ext4`, `NTFS`), used/free space, and read/write I/O byte rates.
   - Network: Shows active interfaces (`eth0`, `lo`), operational link states, MTU, packet drop counters, and calculated bytes/sec throughput.
5. **Process Explorer Page (`/processes`)**:
   - Demonstrate the real-time process list.
   - Show real-time search filtering (type `python`, `node`, or PID).
   - Demonstrate sorting by `% CPU` and `Memory (RSS)`.
   - Click any process to open the **Process Detail Inspection Modal** showing thread counts and creation timestamps.
   - Explain privacy engineering: command lines and environment variables are strictly omitted to prevent credential disclosure.

---

### Demo Part 2: MongoDB Historical Telemetry Analytics
1. **History Page (`/history`)**:
   - Explain that data persistence runs autonomously out-of-band via `MetricsPersistenceService` (independent of whether browser tabs are open).
   - Switch range presets: `15m`, `1h`, `6h`, `All`.
   - Review aggregated metrics: Average CPU %, Peak CPU %, Average RAM %, and Network Data Transferred.
   - Demonstrate how descending compound indexes (`{"timestamp": -1}`) in MongoDB ensure fast analytical queries.

---

### Demo Part 3: Automated Performance Analysis & Bottleneck Detection
1. **Performance Analysis Page (`/analysis`)**:
   - Show the **Unified Health Score (0–100)**:
     - Point out the status badge (`EXCELLENT`, `GOOD`, `DEGRADED`, `CRITICAL`).
     - Explain the deduction model: mathematically penalized for CPU saturation, RAM pressure, swap thrashing, disk capacity limits, and packet drops.
   - Show **Subsystem Classification Badges**: CPU, Memory, Storage, and Network evaluated as `OPTIMAL`, `NORMAL`, `ELEVATED`, `WARNING`, or `CRITICAL`.
   - Show the **Active Bottlenecks Section**:
     - If all metrics are healthy: shows clean confirmation that all subsystems are operating nominally.
     - Show the **Historical Telemetry Correlation Banner**: correlates the current state against up to 60 historical MongoDB records, identifying whether high resource utilization is a transient spike or sustained pressure.
   - Review **Automated Remediation Actions**: concrete steps recommended to optimize system health.

---

### Demo Part 4: CPU Scheduling Simulator & Multi-Algorithm Benchmark
1. **CPU Scheduling Page (`/scheduling`)**:
   - Explain that this module is an interactive operating system algorithm simulator with non-preemptive and preemptive scheduling models.

2. **Run Workload 1: Convoy Effect (FCFS vs SJF / SRTF)**:
   - Select preset **"CPU Bound (Long Burst)"** or enter:
     - `P1`: Arrival `0.0`, Burst `8.0`
     - `P2`: Arrival `1.0`, Burst `4.0`
     - `P3`: Arrival `2.0`, Burst `9.0`
     - `P4`: Arrival `3.0`, Burst `5.0`
   - Select **FCFS** and click **Run Single Simulation**:
     - Point out the Gantt Chart: $P_1$ runs for 8 units, forcing $P_2, P_3, P_4$ to wait. Average Turnaround Time is high ($15.0\text{s}$).
   - Switch to **SRTF** and click **Run Single Simulation**:
     - Point out the Gantt Chart: When $P_2$ arrives at $t=1$, its burst ($4.0$) is shorter than $P_1$'s remaining burst ($7.0$), so $P_2$ **preempts** $P_1$ immediately.
     - Notice the average turnaround time drops significantly, demonstrating theoretical optimality.

3. **Run Workload 2: Priority Preemption**:
   - Enter:
     - `P1`: Arrival `0.0`, Burst `6.0`, Priority `3`
     - `P2`: Arrival `1.0`, Burst `2.0`, Priority `1`
     - `P3`: Arrival `2.0`, Burst `1.0`, Priority `2`
   - Select **Priority Scheduling**, enable **Preemptive Mode**, select **Lower number = Higher priority**.
   - Click **Run Single Simulation**:
     - Show the Gantt chart: $P_1$ starts at $0$, gets preempted at $t=1$ by $P_2$ (Priority 1), $P_2$ completes at $3$, $P_3$ (Priority 2) runs next until $4$, and $P_1$ finishes from $4$ to $9$.

4. **Run Workload 3: Round Robin Time Quantum Fair Slicing**:
   - Select **Round Robin**, set Time Quantum = `2.0s`.
   - Click **Run Single Simulation**:
     - Show how the Gantt chart slices execution into uniform 2-second quanta, rotating fairly among ready tasks.

5. **Run Multi-Algorithm Comparative Benchmark**:
   - Click **Compare All Schedulers**:
     - Instantly executes FCFS, SJF, SRTF, Priority (Non-preemptive), Priority (Preemptive), and Round Robin against the exact same workload.
     - Shows the **Benchmark Summary Table**: compares Average Turnaround, Average Waiting, Average Response, CPU Utilization, and Throughput.
     - Highlights the **Algorithmic Workload Analysis Card**: automated assessment explaining trade-offs and recommending the best algorithm for the workload.

---

## 3. Sample Workloads Table for Viva / Defense

| Workload Name | Processes (PID, Arrival, Burst, Priority) | Key Demonstration Point |
|---|---|---|
| **Textbook Mixed** | P1(0, 4, p2), P2(1, 3, p1), P3(2, 1, p3), P4(3, 2, p2) | General balance across all algorithms; shows Gantt segment synthesis. |
| **Convoy Effect** | P1(0, 8, p1), P2(1, 4, p2), P3(2, 9, p3), P4(3, 5, p1) | Demonstrates FCFS convoy latency vs SRTF preemption efficiency. |
| **SJF Optimality** | P1(0, 7, p3), P2(2, 4, p1), P3(4, 1, p2), P4(5, 4, p3) | Shows non-preemptive SJF queue ordering and shortest burst prioritization. |
| **CPU Idle Gaps** | P1(2, 3, p1), P2(7, 2, p2) | Demonstrates CPU idle intervals ($0\text{--}2\text{s}$ and $5\text{--}7\text{s}$) and utilization calculations. |
| **Round Robin Variation**| P1(0, 5), P2(1, 3), P3(2, 1) with $Q=1.0$ vs $Q=3.0$ | Demonstrates responsiveness vs context-switch overhead across varying quanta. |

---

## 4. Presentation Troubleshooting

1. **MongoDB is offline**:
   - *Symptom*: TopNav displays `MongoDB: Disconnected` or `/health` returns 503.
   - *Fix*: Start MongoDB service with `sudo systemctl start mongod` or `sudo service mongodb start`.
   - *Note*: Even if MongoDB is offline, the REST metrics and scheduling simulator remain fully functional due to component failure isolation.
2. **WebSocket connection drops**:
   - *Symptom*: Dashboard shows `WebSocket: Reconnecting`.
   - *Fix*: The frontend client features built-in exponential backoff and automatically reconnects once backend traffic resumes.
3. **WSL2 vs Windows Host metrics**:
   - *Explanation to Committee*: When executed inside WSL2, metrics reflect the Linux VM environment (virtual disk mounts, virtual interfaces, memory allocated to WSL2). In native Linux or Windows, metrics reflect the full bare-metal host.
