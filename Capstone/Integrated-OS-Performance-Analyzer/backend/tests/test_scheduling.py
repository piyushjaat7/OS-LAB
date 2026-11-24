"""Tests for CPU scheduling algorithms and simulation engine."""

import pytest
from pydantic import ValidationError

from app.algorithms.scheduling import (
    compare_all_schedulers,
    schedule_fcfs,
    schedule_priority,
    schedule_round_robin,
    schedule_sjf,
    schedule_srtf,
)
from app.schemas.scheduling import ProcessWorkload, SchedulingRequest


def test_fcfs_basic():
    """Test FCFS on a standard 3-process workload."""
    processes = [
        ProcessWorkload(process_id="P1", arrival_time=0.0, burst_time=4.0),
        ProcessWorkload(process_id="P2", arrival_time=1.0, burst_time=3.0),
        ProcessWorkload(process_id="P3", arrival_time=2.0, burst_time=1.0),
    ]

    result = schedule_fcfs(processes)

    assert "FCFS" in result.algorithm
    assert result.mode == "non-preemptive"
    assert result.total_simulation_time == 8.0
    assert result.idle_time == 0.0
    assert result.cpu_utilization_percent == 100.0

    p_map = {m.process_id: m for m in result.processes}
    # P1: start=0, finish=4, TAT=4, WT=0, RT=0
    assert p_map["P1"].completion_time == 4.0
    assert p_map["P1"].turnaround_time == 4.0
    assert p_map["P1"].waiting_time == 0.0
    assert p_map["P1"].response_time == 0.0

    # P2: start=4, finish=7, TAT=6, WT=3, RT=3
    assert p_map["P2"].completion_time == 7.0
    assert p_map["P2"].turnaround_time == 6.0
    assert p_map["P2"].waiting_time == 3.0
    assert p_map["P2"].response_time == 3.0

    # P3: start=7, finish=8, TAT=6, WT=5, RT=5
    assert p_map["P3"].completion_time == 8.0
    assert p_map["P3"].turnaround_time == 6.0
    assert p_map["P3"].waiting_time == 5.0
    assert p_map["P3"].response_time == 5.0

    # Averages: TAT = (4+6+6)/3 = 5.33, WT = (0+3+5)/3 = 2.67
    assert result.avg_turnaround_time == round((4 + 6 + 6) / 3, 2)
    assert result.avg_waiting_time == round((0 + 3 + 5) / 3, 2)

    # Gantt chart
    assert len(result.gantt_chart) == 3
    assert result.gantt_chart[0].process_id == "P1"
    assert result.gantt_chart[0].start_time == 0.0
    assert result.gantt_chart[0].end_time == 4.0
    assert result.gantt_chart[1].process_id == "P2"
    assert result.gantt_chart[1].start_time == 4.0
    assert result.gantt_chart[1].end_time == 7.0
    assert result.gantt_chart[2].process_id == "P3"
    assert result.gantt_chart[2].start_time == 7.0
    assert result.gantt_chart[2].end_time == 8.0


def test_fcfs_with_cpu_idle():
    """Test FCFS when the CPU experiences idle periods before and between tasks."""
    processes = [
        ProcessWorkload(process_id="P1", arrival_time=2.0, burst_time=3.0),
        ProcessWorkload(process_id="P2", arrival_time=7.0, burst_time=2.0),
    ]

    result = schedule_fcfs(processes)

    # Timeline:
    # 0.0 - 2.0: IDLE (2.0)
    # 2.0 - 5.0: P1   (3.0)
    # 5.0 - 7.0: IDLE (2.0)
    # 7.0 - 9.0: P2   (2.0)
    assert result.total_simulation_time == 9.0
    assert result.idle_time == 4.0
    assert result.cpu_utilization_percent == round((5.0 / 9.0) * 100, 2)

    assert len(result.gantt_chart) == 4
    assert result.gantt_chart[0].process_id == "IDLE"
    assert result.gantt_chart[0].start_time == 0.0
    assert result.gantt_chart[0].end_time == 2.0

    assert result.gantt_chart[1].process_id == "P1"
    assert result.gantt_chart[1].start_time == 2.0
    assert result.gantt_chart[1].end_time == 5.0

    assert result.gantt_chart[2].process_id == "IDLE"
    assert result.gantt_chart[2].start_time == 5.0
    assert result.gantt_chart[2].end_time == 7.0

    assert result.gantt_chart[3].process_id == "P2"
    assert result.gantt_chart[3].start_time == 7.0
    assert result.gantt_chart[3].end_time == 9.0


def test_sjf_non_preemptive():
    """Test Shortest Job First non-preemptive algorithm."""
    processes = [
        ProcessWorkload(process_id="P1", arrival_time=0.0, burst_time=7.0),
        ProcessWorkload(process_id="P2", arrival_time=2.0, burst_time=4.0),
        ProcessWorkload(process_id="P3", arrival_time=4.0, burst_time=1.0),
        ProcessWorkload(process_id="P4", arrival_time=5.0, burst_time=4.0),
    ]

    result = schedule_sjf(processes)

    assert "SJF" in result.algorithm
    assert result.mode == "non-preemptive"
    assert result.total_simulation_time == 16.0

    # P1 runs 0-7. At t=7, P3(1), P2(4), P4(4) are ready.
    # P3 has shortest burst (1.0), runs 7-8.
    # P2 and P4 both have burst 4. P2 arrived at 2, P4 at 5 -> P2 runs 8-12.
    # P4 runs 12-16.
    seq = [seg.process_id for seg in result.gantt_chart]
    assert seq == ["P1", "P3", "P2", "P4"]

    p_map = {m.process_id: m for m in result.processes}
    assert p_map["P1"].completion_time == 7.0
    assert p_map["P3"].completion_time == 8.0
    assert p_map["P2"].completion_time == 12.0
    assert p_map["P4"].completion_time == 16.0


def test_srtf_preemption():
    """Test Shortest Remaining Time First preemptive algorithm."""
    processes = [
        ProcessWorkload(process_id="P1", arrival_time=0.0, burst_time=8.0),
        ProcessWorkload(process_id="P2", arrival_time=1.0, burst_time=4.0),
        ProcessWorkload(process_id="P3", arrival_time=2.0, burst_time=9.0),
        ProcessWorkload(process_id="P4", arrival_time=3.0, burst_time=5.0),
    ]

    result = schedule_srtf(processes)

    assert "SRTF" in result.algorithm
    assert result.mode == "preemptive"
    assert result.total_simulation_time == 26.0

    # At t=0: P1 runs (remaining 8)
    # At t=1: P2 arrives (burst 4). P1 remaining is 7. 4 < 7 -> P2 preempts P1!
    # P2 runs until t=5 (burst 4 completed)
    # At t=5: ready queue has P1(7), P3(9), P4(5). P4 has shortest (5) -> P4 runs 5-10
    # At t=10: P1(7), P3(9) -> P1 runs 10-17
    # At t=17: P3(9) runs 17-26
    seq = [seg.process_id for seg in result.gantt_chart]
    assert seq == ["P1", "P2", "P4", "P1", "P3"]

    p_map = {m.process_id: m for m in result.processes}
    assert p_map["P2"].completion_time == 5.0
    assert p_map["P4"].completion_time == 10.0
    assert p_map["P1"].completion_time == 17.0
    assert p_map["P3"].completion_time == 26.0

    # P1 was first responded to at t=0, so response_time = 0
    assert p_map["P1"].response_time == 0.0
    # P2 responded at t=1, arrival=1 -> response_time = 0
    assert p_map["P2"].response_time == 0.0
    # P4 responded at t=5, arrival=3 -> response_time = 2.0
    assert p_map["P4"].response_time == 2.0


def test_priority_non_preemptive():
    """Test Priority scheduling in non-preemptive mode."""
    # Default: lower number = higher priority (1 is highest)
    processes = [
        ProcessWorkload(process_id="P1", arrival_time=0.0, burst_time=4.0, priority=3),
        ProcessWorkload(process_id="P2", arrival_time=1.0, burst_time=3.0, priority=1),
        ProcessWorkload(process_id="P3", arrival_time=2.0, burst_time=2.0, priority=2),
    ]

    result = schedule_priority(
        processes, preemptive=False, priority_order="lower_is_higher"
    )

    # P1 arrives at 0, runs non-preemptively until t=4.
    # At t=4, P2 (priority 1) and P3 (priority 2) are ready.
    # P2 runs 4-7.
    # P3 runs 7-9.
    seq = [seg.process_id for seg in result.gantt_chart]
    assert seq == ["P1", "P2", "P3"]

    p_map = {m.process_id: m for m in result.processes}
    assert p_map["P1"].completion_time == 4.0
    assert p_map["P2"].completion_time == 7.0
    assert p_map["P3"].completion_time == 9.0


def test_priority_preemptive():
    """Test Priority scheduling in preemptive mode."""
    processes = [
        ProcessWorkload(process_id="P1", arrival_time=0.0, burst_time=6.0, priority=3),
        ProcessWorkload(process_id="P2", arrival_time=1.0, burst_time=2.0, priority=1),
        ProcessWorkload(process_id="P3", arrival_time=2.0, burst_time=1.0, priority=2),
    ]

    result = schedule_priority(
        processes, preemptive=True, priority_order="lower_is_higher"
    )

    # t=0: P1 (prio 3) starts
    # t=1: P2 (prio 1) arrives -> preempts P1! P2 runs 1-3.
    # t=2: P3 (prio 2) arrives. But P2 is running (prio 1), so P2 finishes at t=3.
    # t=3: P3 (prio 2) vs P1 (prio 3). P3 runs 3-4.
    # t=4: P1 finishes remaining 5 units -> runs 4-9.
    seq = [seg.process_id for seg in result.gantt_chart]
    assert seq == ["P1", "P2", "P3", "P1"]

    p_map = {m.process_id: m for m in result.processes}
    assert p_map["P2"].completion_time == 3.0
    assert p_map["P3"].completion_time == 4.0
    assert p_map["P1"].completion_time == 9.0


def test_priority_higher_is_higher():
    """Test Priority scheduling when higher number means higher priority."""
    processes = [
        ProcessWorkload(process_id="P1", arrival_time=0.0, burst_time=3.0, priority=10),
        ProcessWorkload(process_id="P2", arrival_time=0.0, burst_time=3.0, priority=50),
    ]

    result = schedule_priority(
        processes, preemptive=False, priority_order="higher_is_higher"
    )
    # P2 has priority 50 > 10, so P2 runs first
    assert result.gantt_chart[0].process_id == "P2"
    assert result.gantt_chart[1].process_id == "P1"


def test_round_robin():
    """Test Round Robin algorithm with time quantum = 2."""
    processes = [
        ProcessWorkload(process_id="P1", arrival_time=0.0, burst_time=5.0),
        ProcessWorkload(process_id="P2", arrival_time=1.0, burst_time=3.0),
        ProcessWorkload(process_id="P3", arrival_time=2.0, burst_time=1.0),
    ]

    result = schedule_round_robin(processes, time_quantum=2.0)

    assert "Round Robin" in result.algorithm
    assert result.mode == "preemptive"
    assert result.time_quantum == 2.0
    assert result.total_simulation_time == 9.0

    # Trace:
    # t=0: P1 starts (quantum 2).
    # t=1: P2 arrives.
    # t=2: P3 arrives. P1's quantum expires at t=2 (remaining 3). Ready queue: [P2, P3, P1].
    # t=2-4: P2 runs (quantum 2, remaining 1). Ready queue: [P3, P1, P2].
    # t=4-5: P3 runs (burst 1, finished at 5). Ready queue: [P1, P2].
    # t=5-7: P1 runs (quantum 2, remaining 1). Ready queue: [P2, P1].
    # t=7-8: P2 runs (burst 1, finished at 8). Ready queue: [P1].
    # t=8-9: P1 runs (burst 1, finished at 9).
    seq = [seg.process_id for seg in result.gantt_chart]
    assert seq == ["P1", "P2", "P3", "P1", "P2", "P1"]

    p_map = {m.process_id: m for m in result.processes}
    assert p_map["P3"].completion_time == 5.0
    assert p_map["P2"].completion_time == 8.0
    assert p_map["P1"].completion_time == 9.0


def test_compare_all_schedulers():
    """Test the comparative benchmark across all scheduling algorithms."""
    processes = [
        ProcessWorkload(process_id="P1", arrival_time=0.0, burst_time=6.0, priority=2),
        ProcessWorkload(process_id="P2", arrival_time=1.0, burst_time=4.0, priority=1),
        ProcessWorkload(process_id="P3", arrival_time=2.0, burst_time=2.0, priority=3),
    ]

    comp = compare_all_schedulers(processes, time_quantum=2.0)

    assert len(comp.summary_table) >= 5
    assert "FCFS" in comp.algorithms
    assert "SJF" in comp.algorithms
    assert "SRTF" in comp.algorithms
    assert "Round Robin" in comp.algorithms

    assert len(comp.workload_analysis) > 10


def test_validation_errors():
    """Test validation catches invalid inputs."""
    # Negative arrival time
    with pytest.raises(ValidationError):
        ProcessWorkload(process_id="P1", arrival_time=-1.0, burst_time=4.0)

    # Zero or negative burst time
    with pytest.raises(ValidationError):
        ProcessWorkload(process_id="P1", arrival_time=0.0, burst_time=0.0)

    with pytest.raises(ValidationError):
        ProcessWorkload(process_id="P1", arrival_time=0.0, burst_time=-2.0)

    # Duplicate process IDs
    with pytest.raises(ValidationError):
        SchedulingRequest(
            processes=[
                ProcessWorkload(process_id="P1", arrival_time=0.0, burst_time=4.0),
                ProcessWorkload(process_id="P1", arrival_time=1.0, burst_time=2.0),
            ]
        )


def test_gantt_continuity():
    """Test that Gantt segments form a continuous timeline without gaps."""
    processes = [
        ProcessWorkload(process_id="P1", arrival_time=1.0, burst_time=3.0),
        ProcessWorkload(process_id="P2", arrival_time=6.0, burst_time=2.0),
    ]

    result = schedule_fcfs(processes)
    gantt = result.gantt_chart

    # Starts at 0.0
    assert gantt[0].start_time == 0.0

    for i in range(len(gantt) - 1):
        # End of segment i must equal start of segment i+1
        assert abs(gantt[i].end_time - gantt[i + 1].start_time) < 1e-6

    assert abs(gantt[-1].end_time - result.total_simulation_time) < 1e-6
