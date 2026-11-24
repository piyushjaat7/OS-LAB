from collections import deque

from app.schemas.scheduling import (
    AlgorithmSummary,
    GanttSegment,
    ProcessSimulationMetric,
    ProcessWorkload,
    SchedulingComparison,
    SimulationResult,
)


def _combine_gantt_segments(segments: list[GanttSegment]) -> list[GanttSegment]:
    """Merge contiguous timeline segments executing the same process or idle state."""
    if not segments:
        return []

    merged: list[GanttSegment] = []
    current = segments[0].model_copy()

    for nxt in segments[1:]:
        if (
            nxt.process_id == current.process_id
            and abs(nxt.start_time - current.end_time) < 1e-6
        ):
            current.end_time = nxt.end_time
            current.duration = round(current.end_time - current.start_time, 4)
        else:
            if current.duration > 1e-6:
                merged.append(current)
            current = nxt.model_copy()

    if current.duration > 1e-6:
        merged.append(current)

    return merged


def _build_simulation_result(
    algorithm: str,
    workload: list[ProcessWorkload],
    raw_segments: list[GanttSegment],
    first_start_times: dict[str, float],
    completion_times: dict[str, float],
    mode: str | None = None,
    time_quantum: float | None = None,
    priority_order: str | None = None,
) -> SimulationResult:
    """Compute aggregate simulation statistics and process metrics."""
    gantt_chart = _combine_gantt_segments(raw_segments)
    total_time = gantt_chart[-1].end_time if gantt_chart else 0.0
    idle_time = sum(s.duration for s in gantt_chart if s.process_id == "IDLE")
    busy_time = total_time - idle_time

    cpu_util = round((busy_time / total_time) * 100.0, 2) if total_time > 0 else 0.0
    throughput = round(len(workload) / total_time, 4) if total_time > 0 else 0.0

    process_metrics: list[ProcessSimulationMetric] = []
    total_wt = 0.0
    total_tat = 0.0
    total_rt = 0.0

    for proc in workload:
        ct = completion_times[proc.process_id]
        tat = round(ct - proc.arrival_time, 4)
        wt = round(tat - proc.burst_time, 4)
        rt = round(first_start_times[proc.process_id] - proc.arrival_time, 4)

        total_wt += wt
        total_tat += tat
        total_rt += rt

        process_metrics.append(
            ProcessSimulationMetric(
                process_id=proc.process_id,
                arrival_time=proc.arrival_time,
                burst_time=proc.burst_time,
                priority=proc.priority,
                completion_time=round(ct, 4),
                turnaround_time=max(0.0, tat),
                waiting_time=max(0.0, wt),
                response_time=max(0.0, rt),
            )
        )

    n = len(workload)
    avg_wt = round(total_wt / n, 2) if n > 0 else 0.0
    avg_tat = round(total_tat / n, 2) if n > 0 else 0.0
    avg_rt = round(total_rt / n, 2) if n > 0 else 0.0

    return SimulationResult(
        algorithm=algorithm,
        mode=mode,
        time_quantum=time_quantum,
        priority_order=priority_order,
        processes=process_metrics,
        gantt_chart=gantt_chart,
        total_simulation_time=round(total_time, 4),
        idle_time=round(idle_time, 4),
        cpu_utilization_percent=cpu_util,
        throughput=throughput,
        avg_waiting_time=avg_wt,
        avg_turnaround_time=avg_tat,
        avg_response_time=avg_rt,
    )


def schedule_fcfs(workload: list[ProcessWorkload]) -> SimulationResult:
    """First-Come, First-Served (FCFS) Non-Preemptive Scheduling."""
    sorted_procs = sorted(workload, key=lambda p: (p.arrival_time, p.process_id))
    current_time = 0.0
    segments: list[GanttSegment] = []
    first_starts: dict[str, float] = {}
    completions: dict[str, float] = {}

    for p in sorted_procs:
        if current_time < p.arrival_time:
            idle_dur = p.arrival_time - current_time
            segments.append(
                GanttSegment(
                    process_id="IDLE",
                    start_time=round(current_time, 4),
                    end_time=round(p.arrival_time, 4),
                    duration=round(idle_dur, 4),
                )
            )
            current_time = p.arrival_time

        start = current_time
        end = start + p.burst_time
        first_starts[p.process_id] = start
        completions[p.process_id] = end

        segments.append(
            GanttSegment(
                process_id=p.process_id,
                start_time=round(start, 4),
                end_time=round(end, 4),
                duration=round(p.burst_time, 4),
            )
        )
        current_time = end

    return _build_simulation_result(
        algorithm="First Come First Serve (FCFS)",
        workload=workload,
        raw_segments=segments,
        first_start_times=first_starts,
        completion_times=completions,
        mode="non-preemptive",
    )


def schedule_sjf(workload: list[ProcessWorkload]) -> SimulationResult:
    """Shortest Job First (SJF) Non-Preemptive Scheduling."""
    remaining = {p.process_id: p for p in workload}
    current_time = 0.0
    segments: list[GanttSegment] = []
    first_starts: dict[str, float] = {}
    completions: dict[str, float] = {}

    while remaining:
        available = [p for p in remaining.values() if p.arrival_time <= current_time]
        if not available:
            next_arrival = min(p.arrival_time for p in remaining.values())
            segments.append(
                GanttSegment(
                    process_id="IDLE",
                    start_time=round(current_time, 4),
                    end_time=round(next_arrival, 4),
                    duration=round(next_arrival - current_time, 4),
                )
            )
            current_time = next_arrival
            continue

        selected = min(
            available, key=lambda p: (p.burst_time, p.arrival_time, p.process_id)
        )
        start = current_time
        end = start + selected.burst_time
        first_starts[selected.process_id] = start
        completions[selected.process_id] = end

        segments.append(
            GanttSegment(
                process_id=selected.process_id,
                start_time=round(start, 4),
                end_time=round(end, 4),
                duration=round(selected.burst_time, 4),
            )
        )
        current_time = end
        del remaining[selected.process_id]

    return _build_simulation_result(
        algorithm="Shortest Job First (SJF)",
        workload=workload,
        raw_segments=segments,
        first_start_times=first_starts,
        completion_times=completions,
        mode="non-preemptive",
    )


def schedule_srtf(workload: list[ProcessWorkload]) -> SimulationResult:
    """Shortest Remaining Time First (SRTF) Preemptive Scheduling."""
    rem_time = {p.process_id: p.burst_time for p in workload}
    proc_map = {p.process_id: p for p in workload}
    current_time = 0.0
    segments: list[GanttSegment] = []
    first_starts: dict[str, float] = {}
    completions: dict[str, float] = {}

    while any(rem > 1e-6 for rem in rem_time.values()):
        available = [
            proc_map[pid]
            for pid, rem in rem_time.items()
            if rem > 1e-6 and proc_map[pid].arrival_time <= current_time
        ]

        if not available:
            next_arrival = min(
                proc_map[pid].arrival_time
                for pid, rem in rem_time.items()
                if rem > 1e-6
            )
            segments.append(
                GanttSegment(
                    process_id="IDLE",
                    start_time=round(current_time, 4),
                    end_time=round(next_arrival, 4),
                    duration=round(next_arrival - current_time, 4),
                )
            )
            current_time = next_arrival
            continue

        selected = min(
            available,
            key=lambda p: (rem_time[p.process_id], p.arrival_time, p.process_id),
        )

        if selected.process_id not in first_starts:
            first_starts[selected.process_id] = current_time

        future_arrivals = [
            p.arrival_time
            for p in workload
            if p.arrival_time > current_time and rem_time[p.process_id] > 1e-6
        ]
        next_arrival = min(future_arrivals) if future_arrivals else None

        time_to_finish = rem_time[selected.process_id]
        if next_arrival is not None and next_arrival < current_time + time_to_finish:
            run_time = next_arrival - current_time
            rem_time[selected.process_id] -= run_time
            segments.append(
                GanttSegment(
                    process_id=selected.process_id,
                    start_time=round(current_time, 4),
                    end_time=round(next_arrival, 4),
                    duration=round(run_time, 4),
                )
            )
            current_time = next_arrival
        else:
            run_time = time_to_finish
            end_time = current_time + run_time
            rem_time[selected.process_id] = 0.0
            completions[selected.process_id] = end_time
            segments.append(
                GanttSegment(
                    process_id=selected.process_id,
                    start_time=round(current_time, 4),
                    end_time=round(end_time, 4),
                    duration=round(run_time, 4),
                )
            )
            current_time = end_time

    return _build_simulation_result(
        algorithm="Shortest Remaining Time First (SRTF)",
        workload=workload,
        raw_segments=segments,
        first_start_times=first_starts,
        completion_times=completions,
        mode="preemptive",
    )


def schedule_priority(
    workload: list[ProcessWorkload],
    preemptive: bool = False,
    priority_order: str = "lower_is_higher",
) -> SimulationResult:
    """Priority Scheduling supporting preemptive and non-preemptive modes."""
    mult = 1 if priority_order == "lower_is_higher" else -1

    if not preemptive:
        remaining = {p.process_id: p for p in workload}
        current_time = 0.0
        segments: list[GanttSegment] = []
        first_starts: dict[str, float] = {}
        completions: dict[str, float] = {}

        while remaining:
            available = [
                p for p in remaining.values() if p.arrival_time <= current_time
            ]
            if not available:
                next_arr = min(p.arrival_time for p in remaining.values())
                segments.append(
                    GanttSegment(
                        process_id="IDLE",
                        start_time=round(current_time, 4),
                        end_time=round(next_arr, 4),
                        duration=round(next_arr - current_time, 4),
                    )
                )
                current_time = next_arr
                continue

            selected = min(
                available,
                key=lambda p: (p.priority * mult, p.arrival_time, p.process_id),
            )
            start = current_time
            end = start + selected.burst_time
            first_starts[selected.process_id] = start
            completions[selected.process_id] = end
            segments.append(
                GanttSegment(
                    process_id=selected.process_id,
                    start_time=round(start, 4),
                    end_time=round(end, 4),
                    duration=round(selected.burst_time, 4),
                )
            )
            current_time = end
            del remaining[selected.process_id]

        return _build_simulation_result(
            algorithm="Priority Scheduling",
            workload=workload,
            raw_segments=segments,
            first_start_times=first_starts,
            completion_times=completions,
            mode="non-preemptive",
            priority_order=priority_order,
        )

    # Preemptive Priority
    rem_time = {p.process_id: p.burst_time for p in workload}
    proc_map = {p.process_id: p for p in workload}
    current_time = 0.0
    segments = []
    first_starts = {}
    completions = {}

    while any(rem > 1e-6 for rem in rem_time.values()):
        available = [
            proc_map[pid]
            for pid, rem in rem_time.items()
            if rem > 1e-6 and proc_map[pid].arrival_time <= current_time
        ]

        if not available:
            next_arrival = min(
                proc_map[pid].arrival_time
                for pid, rem in rem_time.items()
                if rem > 1e-6
            )
            segments.append(
                GanttSegment(
                    process_id="IDLE",
                    start_time=round(current_time, 4),
                    end_time=round(next_arrival, 4),
                    duration=round(next_arrival - current_time, 4),
                )
            )
            current_time = next_arrival
            continue

        selected = min(
            available,
            key=lambda p: (p.priority * mult, p.arrival_time, p.process_id),
        )

        if selected.process_id not in first_starts:
            first_starts[selected.process_id] = current_time

        future_arrivals = [
            p.arrival_time
            for p in workload
            if p.arrival_time > current_time and rem_time[p.process_id] > 1e-6
        ]
        next_arrival = min(future_arrivals) if future_arrivals else None

        time_to_finish = rem_time[selected.process_id]
        if next_arrival is not None and next_arrival < current_time + time_to_finish:
            run_time = next_arrival - current_time
            rem_time[selected.process_id] -= run_time
            segments.append(
                GanttSegment(
                    process_id=selected.process_id,
                    start_time=round(current_time, 4),
                    end_time=round(next_arrival, 4),
                    duration=round(run_time, 4),
                )
            )
            current_time = next_arrival
        else:
            run_time = time_to_finish
            end_time = current_time + run_time
            rem_time[selected.process_id] = 0.0
            completions[selected.process_id] = end_time
            segments.append(
                GanttSegment(
                    process_id=selected.process_id,
                    start_time=round(current_time, 4),
                    end_time=round(end_time, 4),
                    duration=round(run_time, 4),
                )
            )
            current_time = end_time

    return _build_simulation_result(
        algorithm="Priority Scheduling",
        workload=workload,
        raw_segments=segments,
        first_start_times=first_starts,
        completion_times=completions,
        mode="preemptive",
        priority_order=priority_order,
    )


def schedule_round_robin(
    workload: list[ProcessWorkload],
    time_quantum: float = 2.0,
) -> SimulationResult:
    """Round Robin (RR) Preemptive Scheduling with configurable time quantum."""
    if time_quantum <= 0:
        raise ValueError("time_quantum must be strictly positive (> 0)")

    sorted_workload = sorted(workload, key=lambda p: (p.arrival_time, p.process_id))
    rem_time = {p.process_id: p.burst_time for p in workload}
    first_starts: dict[str, float] = {}
    completions: dict[str, float] = {}
    segments: list[GanttSegment] = []

    ready_queue: deque[ProcessWorkload] = deque()
    unvisited = sorted_workload.copy()
    current_time = 0.0

    while unvisited and unvisited[0].arrival_time <= current_time:
        ready_queue.append(unvisited.pop(0))

    while ready_queue or unvisited:
        if not ready_queue:
            next_p = unvisited.pop(0)
            segments.append(
                GanttSegment(
                    process_id="IDLE",
                    start_time=round(current_time, 4),
                    end_time=round(next_p.arrival_time, 4),
                    duration=round(next_p.arrival_time - current_time, 4),
                )
            )
            current_time = next_p.arrival_time
            ready_queue.append(next_p)
            while unvisited and unvisited[0].arrival_time <= current_time:
                ready_queue.append(unvisited.pop(0))

        curr_p = ready_queue.popleft()
        if curr_p.process_id not in first_starts:
            first_starts[curr_p.process_id] = current_time

        run_time = min(time_quantum, rem_time[curr_p.process_id])
        start = current_time
        end = start + run_time
        rem_time[curr_p.process_id] -= run_time
        current_time = end

        segments.append(
            GanttSegment(
                process_id=curr_p.process_id,
                start_time=round(start, 4),
                end_time=round(end, 4),
                duration=round(run_time, 4),
            )
        )

        while unvisited and unvisited[0].arrival_time <= current_time:
            ready_queue.append(unvisited.pop(0))

        if rem_time[curr_p.process_id] > 1e-6:
            ready_queue.append(curr_p)
        else:
            completions[curr_p.process_id] = end

    return _build_simulation_result(
        algorithm="Round Robin (RR)",
        workload=workload,
        raw_segments=segments,
        first_start_times=first_starts,
        completion_times=completions,
        mode="preemptive",
        time_quantum=time_quantum,
    )


def compare_all_schedulers(
    workload: list[ProcessWorkload],
    time_quantum: float = 2.0,
    priority_order: str = "lower_is_higher",
) -> SchedulingComparison:
    """Execute all five scheduling algorithms on identical workload and generate comparison."""
    fcfs = schedule_fcfs(workload)
    sjf = schedule_sjf(workload)
    srtf = schedule_srtf(workload)
    p_non = schedule_priority(workload, preemptive=False, priority_order=priority_order)
    p_pre = schedule_priority(workload, preemptive=True, priority_order=priority_order)
    rr = schedule_round_robin(workload, time_quantum=time_quantum)

    results = {
        "FCFS": fcfs,
        "SJF": sjf,
        "SRTF": srtf,
        "Priority (Non-Preemptive)": p_non,
        "Priority (Preemptive)": p_pre,
        "Round Robin": rr,
    }

    summary: list[AlgorithmSummary] = []
    for name, sim in results.items():
        summary.append(
            AlgorithmSummary(
                algorithm=name,
                mode=sim.mode,
                avg_waiting_time=sim.avg_waiting_time,
                avg_turnaround_time=sim.avg_turnaround_time,
                avg_response_time=sim.avg_response_time,
                cpu_utilization_percent=sim.cpu_utilization_percent,
                throughput=sim.throughput,
            )
        )

    # Sort summary by average waiting time ascending for reference
    summary.sort(key=lambda s: s.avg_waiting_time)

    commentary = (
        f"Comparative analysis of {len(workload)} simulated processes: "
        f"SRTF typically yields the lowest average waiting time ({srtf.avg_waiting_time}s) "
        f"by prioritizing shortest remaining execution, while Round Robin (q={time_quantum}s) "
        f"provides balanced interactivity with average response time of {rr.avg_response_time}s. "
        "The optimal scheduling algorithm is workload-dependent and involves trade-offs between "
        "turnaround efficiency, CPU context-switch overhead, and responsiveness guarantees."
    )

    return SchedulingComparison(
        workload_size=len(workload),
        algorithms=results,
        summary_table=summary,
        workload_analysis=commentary,
    )
