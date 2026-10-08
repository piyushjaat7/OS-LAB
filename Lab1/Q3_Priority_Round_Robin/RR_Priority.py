from concurrent.futures import process
from dataclasses import dataclass
from copy import deepcopy
from collections import deque
from pdb import run
from pdb import run
import queue
from unicodedata import name


@dataclass
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int
    remaining: int = 0
    completion: int = 0
    turnaround: int = 0
    waiting: int = 0


def finalize(process: Process):
    process.turnaround = (
        process.completion - process.arrival
    )
    process.waiting = (
        process.turnaround - process.burst
    )


def priority_schedule(items):

    remaining = deepcopy(items)
    completed = []
    timeline = []
    current = 0

    while remaining:

        ready = [
            process
            for process in remaining
            if process.arrival <= current
        ]

        if not ready:

            next_arrival = min(
                process.arrival
                for process in remaining
            )

            timeline.append(
                ("IDLE", current, next_arrival)
            )

            current = next_arrival
            continue

        process = min(
            ready,
            key=lambda p: (
                p.priority,
                p.arrival,
                p.pid
            )
        )

        start = current
        current += process.burst

        process.completion = current

        finalize(process)

        timeline.append(
            (process.pid, start, current)
        )

        completed.append(process)
        remaining.remove(process)

    return completed, timeline


def round_robin(items, quantum):

    if quantum <= 0:
        raise ValueError(
            "Quantum must be positive"
        )

    processes = sorted(
        deepcopy(items),
        key=lambda p: (
            p.arrival,
            p.pid
        )
    )

    for process in processes:
        process.remaining = process.burst

    queue = deque()
    timeline = []
    completed = []

    current = 0
    index = 0

    while len(completed) < len(processes):

        while (
            index < len(processes)
            and processes[index].arrival <= current
        ):
            queue.append(processes[index])
            index += 1

        if not queue:

            next_arrival = processes[index].arrival

            timeline.append(
                ("IDLE", current, next_arrival)
            )

            current = next_arrival
            continue

        process = queue.popleft()

        start = current

        run = min(
            quantum,
            process.remaining
        )

        current += run
        process.remaining -= run

        timeline.append(
            (process.pid, start, current)
        )

        while (
            index < len(processes)
            and processes[index].arrival <= current
        ):
            queue.append(processes[index])
            index += 1

        if process.remaining > 0:
            queue.append(process)

        else:
            process.completion = current

            finalize(process)

            completed.append(process)

    return completed, timeline


def print_result(name, processes, timeline):

    print(f"\n{name}")

    print(
        "PID AT BT PR CT TAT WT"
    )

    for process in processes:

        print(
            process.pid,
            process.arrival,
            process.burst,
            process.priority,
            process.completion,
            process.turnaround,
            process.waiting
        )

    print("Timeline:", timeline)


data = [
    Process("P1", 0, 7, 2),
    Process("P2", 2, 4, 1),
    Process("P3", 4, 1, 3),
    Process("P4", 5, 4, 2)
]


priority_result, priority_timeline = (
    priority_schedule(data)
)

rr_result, rr_timeline = round_robin(
    data,
    2
)

print_result(
    "Priority Scheduling",
    priority_result,
    priority_timeline
)

print_result(
    "Round Robin",
    rr_result,
    rr_timeline
)