from dataclasses import dataclass
from copy import deepcopy


@dataclass
class Process:
    pid: str
    arrival: int
    burst: int
    completion: int = 0
    turnaround: int = 0
    waiting: int = 0


def calculate(process: Process, current: int):
    start = max(current, process.arrival)
    process.completion = start + process.burst
    process.turnaround = process.completion - process.arrival
    process.waiting = process.turnaround - process.burst

    return process.completion, start


# ---------------- FCFS ----------------

def fcfs(items):
    processes = sorted(
        deepcopy(items),
        key=lambda p: (p.arrival, p.pid)
    )

    current = 0
    timeline = []

    for process in processes:

        if current < process.arrival:
            timeline.append(
                ("IDLE", current, process.arrival)
            )
            current = process.arrival

        current, start = calculate(process, current)

        timeline.append(
            (process.pid, start, current)
        )

    return processes, timeline


# ---------------- SJF ----------------

def sjf(items):
    processes = deepcopy(items)

    remaining = processes[:]
    completed = []
    timeline = []

    current = 0

    while remaining:

        ready = [
            process
            for process in remaining
            if process.arrival <= current
        ]

        # CPU idle
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

        # Shortest Job First
        # Tie-breaking:
        # 1. Burst time
        # 2. Arrival time
        # 3. Process ID
        process = min(
            ready,
            key=lambda p: (
                p.burst,
                p.arrival,
                p.pid
            )
        )

        current, start = calculate(
            process,
            current
        )

        timeline.append(
            (process.pid, start, current)
        )

        completed.append(process)
        remaining.remove(process)

    return completed, timeline


# ---------------- Display Results ----------------

def print_result(name, processes, timeline):

    print(f"\n{name}")

    print(
        "PID\tAT\tBT\tCT\tTAT\tWT"
    )

    for process in processes:

        print(
            f"{process.pid}\t"
            f"{process.arrival}\t"
            f"{process.burst}\t"
            f"{process.completion}\t"
            f"{process.turnaround}\t"
            f"{process.waiting}"
        )

    print("\nExecution Timeline:")

    for pid, start, end in timeline:
        print(
            f"{start} -> {end}: {pid}"
        )


# ---------------- Input ----------------

def get_positive_integer(prompt):

    while True:

        try:
            value = int(input(prompt))

            if value < 0:
                print("Error: value cannot be negative.")
                continue

            return value

        except ValueError:
            print("Error: enter a valid integer.")


def get_processes():

    while True:

        try:
            n = int(
                input("Enter number of processes: ")
            )

            if n <= 0:
                print(
                    "Error: number of processes "
                    "must be positive."
                )
                continue

            break

        except ValueError:
            print(
                "Error: enter a valid integer."
            )

    processes = []
    used_ids = set()

    for i in range(n):

        print(f"\nProcess {i + 1}")

        while True:

            pid = input("Enter Process ID: ").strip()

            if not pid:
                print("Error: Process ID cannot be empty.")
                continue

            if pid in used_ids:
                print("Error: Process ID already exists.")
                continue

            break

        arrival = get_positive_integer(
            "Enter Arrival Time: "
        )

        burst = get_positive_integer(
            "Enter Burst Time: "
        )

        if burst == 0:
            print(
                "Error: Burst Time must be greater than 0."
            )

            while burst == 0:
                burst = get_positive_integer(
                    "Enter Burst Time again: "
                )

        processes.append(
            Process(
                pid,
                arrival,
                burst
            )
        )

        used_ids.add(pid)

    return processes


# ---------------- Main ----------------

def main():

    print("================================")
    print("     FCFS AND SJF SCHEDULING")
    print("================================")

    data = get_processes()

    # Same original dataset is used for both algorithms.
    fcfs_result, fcfs_timeline = fcfs(data)

    sjf_result, sjf_timeline = sjf(data)

    print("\n\n========== FCFS ==========")

    print_result(
        "FCFS",
        fcfs_result,
        fcfs_timeline
    )

    print("\n\n========== SJF ==========")

    print_result(
        "SJF",
        sjf_result,
        sjf_timeline
    )


if __name__ == "__main__":
    main()