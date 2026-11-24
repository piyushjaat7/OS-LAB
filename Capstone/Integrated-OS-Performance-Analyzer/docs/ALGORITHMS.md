# Operating System Algorithms & Analytical Engine Specification

## 1. CPU Scheduling Metrics & Formulae

The scheduling simulation engine computes operating system performance metrics based on standard scheduling theory:

### 1.1 Completion Time ($CT$)
The exact point on the timeline when process $P_i$ executes its final CPU burst instruction:
$$CT(P_i) = t_{\text{finish}}$$

### 1.2 Turnaround Time ($TAT$)
The total elapsed wall-clock time from when the process arrived in the ready queue to its final completion:
$$TAT(P_i) = CT(P_i) - AT(P_i)$$
Where $AT(P_i)$ is the arrival time of process $P_i$.

### 1.3 Waiting Time ($WT$)
The total time the process spent sitting in the ready queue waiting for CPU allocation:
$$WT(P_i) = TAT(P_i) - BT(P_i)$$
Where $BT(P_i)$ is the total CPU burst time required by process $P_i$.

### 1.4 Response Time ($RT$)
The elapsed time from when the process entered the ready queue until the CPU allocated its very first execution slice:
$$RT(P_i) = t_{\text{first\_start}}(P_i) - AT(P_i)$$
In non-preemptive algorithms (such as FCFS and non-preemptive SJF), $RT(P_i) = WT(P_i)$. In preemptive algorithms (such as SRTF, preemptive priority, and Round Robin), $RT(P_i) \le WT(P_i)$.

### 1.5 System-Wide Throughput
The number of processes completed per unit time across the total duration of the workload simulation:
$$\text{Throughput} = \frac{N}{t_{\text{total}}}$$
Where $N$ is the number of processes and $t_{\text{total}} = \max(CT)$.

### 1.6 CPU Utilization Percentage
The proportion of total simulation time during which the CPU was actively running processes versus remaining idle:
$$\text{CPU Utilization} = \left( \frac{t_{\text{total}} - t_{\text{idle}}}{t_{\text{total}}} \right) \times 100\%$$

---

## 2. Scheduling Algorithm Mechanics

### 2.1 First-Come First-Served (FCFS)
- **Policy**: Non-preemptive.
- **Queue Discipline**: FIFO (First-In, First-Out) based on arrival time $AT$.
- **Tie-Breaking**: If arrival times are identical, ordered deterministically by process identifier string (`process_id`).
- **Characteristics**: Simple with zero preemption overhead; prone to the **Convoy Effect** if a long CPU-bound process arrives before shorter I/O-bound processes.

### 2.2 Shortest Job First (SJF)
- **Policy**: Non-preemptive.
- **Selection Rule**: When the CPU is free, select the process from the ready queue ($AT \le t$) with the minimum total burst time $BT$.
- **Tie-Breaking**: Ordered deterministically by `(burst_time, arrival_time, process_id)`.
- **Characteristics**: Minimizes average waiting time among all non-preemptive algorithms, but requires prior knowledge of burst times.

### 2.3 Shortest Remaining Time First (SRTF)
- **Policy**: Preemptive SJF.
- **Selection Rule**: At each unit time tick, inspect all arrived processes and assign CPU to the one with the smallest remaining burst time $BT_{\text{rem}}$.
- **Preemption**: If a newly arrived process has $BT_{\text{new}} < BT_{\text{current\_rem}}$, the running process is immediately preempted and returned to the ready queue.
- **Tie-Breaking**: Ordered deterministically by `(remaining_time, arrival_time, process_id)`.
- **Characteristics**: Provably optimal for minimizing average turnaround and waiting time, but incurs context switching overhead.

### 2.4 Priority Scheduling
- **Policy**: Supports both Preemptive and Non-preemptive modes.
- **Conventions**:
  - `lower_is_higher` (default): Priority $1 > 2 > 3$.
  - `higher_is_higher`: Priority $50 > 20 > 10$.
- **Preemption Rule**: When preemptive mode is enabled, an incoming process with higher priority immediately preempts a lower-priority running process.
- **Tie-Breaking**: Ordered by `(effective_priority, arrival_time, process_id)`.

### 2.5 Round Robin (RR)
- **Policy**: Preemptive time-sliced scheduling.
- **Mechanism**:
  - Configurable time quantum $Q > 0$ (default $2.0$).
  - Ready queue is managed as a FIFO circular buffer.
  - Newly arriving processes are appended to the queue as simulation time advances.
  - If a process executes for $Q$ units without completing, it is preempted and re-queued at the back of the ready queue.
- **Characteristics**: Guarantees bounded response times and prevents process starvation. As $Q \to \infty$, RR degenerates to FCFS; as $Q \to 0$, context-switch overhead dominates.

---

## 3. Timeline & Gantt Chart Synthesis

- **Idle Period Tracking**: If simulation time $t$ has not reached the arrival of the next process, the CPU enters an idle state. An explicit segment with `process_id: "IDLE"` is recorded:
  $$\text{Segment: } [\text{start: } t_1, \text{end: } t_2, \text{duration: } t_2 - t_1]$$
- **Contiguity**: All Gantt segments form a continuous, non-overlapping partition of $[0, t_{\text{total}}]$.
- **Segment Merging**: If the same process runs continuously across adjacent quantum steps without an intervening task, segments are merged into a single slice for clear visual presentation.

---

## 4. Performance Health Scoring Model

The system health score is a calibrated metric starting at 100 points:

$$\text{Health Score} = \max\left(0, \min\left(100, 100 - \sum \text{Penalties}\right)\right)$$

### Penalty Deductions:
| Subsystem | Condition | Penalty | Status Level |
|---|---|---|---|
| **CPU** | Overall usage $\ge 90\%$ or Core $\ge 98\%$ | $-25$ pts | `CRITICAL` |
| | Overall usage $\ge 75\%$ or Core $\ge 90\%$ | $-15$ pts | `WARNING` |
| | Overall usage $\ge 60\%$ | $-8$ pts | `ELEVATED` |
| **RAM** | Virtual Memory usage $\ge 90\%$ | $-25$ pts | `CRITICAL` |
| | Virtual Memory usage $\ge 80\%$ | $-15$ pts | `WARNING` |
| | Virtual Memory usage $\ge 70\%$ | $-8$ pts | `ELEVATED` |
| **Swap** | Swap usage $\ge 50\%$ (Paging hazard) | $-20$ pts | `CRITICAL` |
| | Swap usage $\ge 20\%$ | $-10$ pts | `WARNING` |
| | Swap usage $\ge 5\%$ | $-5$ pts | `ELEVATED` |
| **Disk** | Max partition capacity $\ge 95\%$ | $-25$ pts | `CRITICAL` |
| | Max partition capacity $\ge 85\%$ | $-15$ pts | `WARNING` |
| | Max partition capacity $\ge 75\%$ | $-8$ pts | `ELEVATED` |
| **Network** | Interface packet drops $> 100$ or errors $> 50$ | $-10$ pts | `WARNING` |
| | Interface packet drops $> 0$ or errors $> 0$ | $-3$ pts | `ELEVATED` |

### Health Status Categorization:
- **`EXCELLENT`**: $\text{Score} \ge 85$
- **`GOOD`**: $70 \le \text{Score} < 85$
- **`DEGRADED`**: $50 \le \text{Score} < 70$
- **`CRITICAL`**: $\text{Score} < 50$

---

## 5. Subsystem Bottleneck Detection Heuristics

1. **CPU Saturation**:
   - Condition: Overall CPU $\ge 80\%$ OR peak single core $\ge 92\%$.
   - Evidence: Captures overall load, max core load, and the top 3 CPU-consuming processes.
   - Analysis: Identifies run-queue thread contention and context-switch latency.

2. **Memory Exhaustion & Thrashing**:
   - Condition: RAM $\ge 80\%$ OR Swap $\ge 20\%$.
   - Evidence: Captures physical RAM used/available MB, swap used %, and top resident processes.
   - Analysis: Warns of OS out-of-memory hazard and virtual memory paging degradation.

3. **Disk Storage Exhaustion**:
   - Condition: Mount point used capacity $\ge 85\%$.
   - Evidence: Mountpoint path, percentage full, and remaining free space in GB.
   - Limitation Note: Highlights that OS kernel disk await latency is a device-specific kernel counter not universally exposed across all user environments.

4. **Network Congestion & Buffer Overrun**:
   - Condition: Cumulative packet drops $> 0$ or interface transmission errors $> 0$.
   - Throughput Context: Explicitly documents that high throughput alone is not bottleneck evidence; packet drops signify interface buffer overruns or cable/duplex degradation.

5. **Historical Correlation**:
   - Evaluates recent historical records stored in MongoDB (up to 60 snapshots).
   - If average CPU $\ge 70\%$ or average RAM $\ge 75\%$ over the sampling window, flags `historical_pressure_detected = true` to confirm sustained pressure versus transient spikes.
