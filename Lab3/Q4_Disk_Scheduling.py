def validate(requests, head, minimum, maximum):
    if minimum < 0 or maximum <= minimum:
        raise ValueError("Invalid disk range.")

    if not minimum <= head <= maximum:
        raise ValueError("Head outside disk range.")

    if any(not minimum <= request <= maximum for request in requests):
        raise ValueError("Request outside disk range.")


# CALCULATE TOTAL HEAD MOVEMENT
def movement(path):
    return sum(
        abs(path[i] - path[i - 1])
        for i in range(1, len(path))
    )


# FCFS DISK SCHEDULING
def fcfs(requests, head):
    return [head] + requests[:]


# SSTF DISK SCHEDULING
def sstf(requests, head):
    pending = requests[:]
    path = [head]
    current = head

    while pending:
        next_request = min(
            pending,
            key=lambda value: (abs(value - current), value)
        )

        path.append(next_request)
        pending.remove(next_request)
        current = next_request

    return path


# SCAN DISK SCHEDULING
def scan(requests, head, minimum, maximum, direction):
    left = sorted(
        [request for request in requests if request < head],
        reverse=True
    )

    right = sorted(
        [request for request in requests if request >= head]
    )

    if direction == "right":
        path = [head] + right

        if left:
            path.append(maximum)
            path.append(minimum) if False else None
            path += left

        return path

    else:
        path = [head] + left

        if right:
            path.append(minimum)
            path += right

        return path


# C-SCAN DISK SCHEDULING
def cscan(requests, head, minimum, maximum, direction):
    left = sorted(
        [request for request in requests if request < head]
    )

    right = sorted(
        [request for request in requests if request >= head]
    )

    if direction == "right":
        path = [head] + right

        if left:
            path += [maximum, minimum] + left

        return path

    else:
        path = [head] + left[::-1]

        if right:
            path += [minimum, maximum] + right[::-1]

        return path


# SWAP SPACE MANAGEMENT
class SwapSpace:
    def __init__(self, blocks):
        if blocks <= 0:
            raise ValueError("Swap block count must be positive.")

        self.bitmap = [0] * blocks
        self.allocations = {}

    def display(self):
        print("\nSwap Space Bitmap:", self.bitmap)
        print("Allocations:", self.allocations)
        print("Free Blocks:", self.bitmap.count(0))
        print("Used Blocks:", self.bitmap.count(1))

    def allocate(self, process, count):
        if count <= 0:
            print("Invalid block count.")
            return False

        if process in self.allocations:
            print("Process already has allocated swap space.")
            return False

        free = [
            i for i, value in enumerate(self.bitmap)
            if value == 0
        ]

        if len(free) < count:
            print("Not enough free swap space.")
            return False

        chosen = free[:count]

        for block in chosen:
            self.bitmap[block] = 1

        self.allocations[process] = chosen

        print(f"{process} allocated blocks: {chosen}")
        return True

    def release(self, process):
        if process not in self.allocations:
            print("Process allocation not found.")
            return False

        for block in self.allocations.pop(process):
            self.bitmap[block] = 0

        print(f"Swap space released for {process}.")
        return True


# DISPLAY DISK SCHEDULING RESULTS
def show(name, path, requests):
    total = movement(path)

    print("\n" + "=" * 50)
    print(name)
    print("=" * 50)

    print("Head Movement Path:", path)
    print("Total Head Movement:", total)

    print(
        "Average Movement per Request:",
        round(total / len(requests), 2)
        if requests else 0
    )

    return total


# MAIN PROGRAM
print("=" * 50)
print("DISK SCHEDULING AND SWAP SPACE MANAGEMENT")
print("=" * 50)

try:
    requests = list(map(
        int,
        input("\nEnter disk requests (space separated): ").split()
    ))

    head = int(input("Enter initial head position: "))
    minimum = int(input("Enter minimum disk cylinder: "))
    maximum = int(input("Enter maximum disk cylinder: "))

    direction = input(
        "Enter initial direction (left/right): "
    ).lower()

    if direction not in ("left", "right"):
        raise ValueError("Direction must be left or right.")

    validate(requests, head, minimum, maximum)

    # RUN ALL ALGORITHMS
    results = {}

    results["FCFS"] = show(
        "FCFS",
        fcfs(requests, head),
        requests
    )

    results["SSTF"] = show(
        "SSTF",
        sstf(requests, head),
        requests
    )

    results["SCAN"] = show(
        "SCAN",
        scan(requests, head, minimum, maximum, direction),
        requests
    )

    results["C-SCAN"] = show(
        "C-SCAN",
        cscan(requests, head, minimum, maximum, direction),
        requests
    )

    # COMPARISON
    print("\n--- DISK SCHEDULING COMPARISON ---")

    for name, total in results.items():
        print(f"{name}: {total} cylinders")

    best = min(results, key=results.get)

    print("\nMinimum Head Movement:", best)

    print("\n--- ALGORITHM CHARACTERISTICS ---")
    print("FCFS: Fair, but may cause high head movement.")
    print("SSTF: Reduces movement but may cause starvation.")
    print("SCAN: Moves in one direction and reverses.")
    print("C-SCAN: Services requests in one direction and wraps around.")

    # SWAP SPACE SIMULATION
    print("\n" + "=" * 50)
    print("SWAP SPACE MANAGEMENT")
    print("=" * 50)

    total_blocks = int(input("Enter total swap blocks: "))

    swap = SwapSpace(total_blocks)

    swap.display()

    while True:
        print("\n1. Allocate Swap Space")
        print("2. Release Swap Space")
        print("3. Display Swap Space")
        print("4. Exit Swap Management")

        choice = input("Enter your choice: ")

        if choice == "1":
            process = input("Enter process name: ")
            count = int(input("Enter required blocks: "))

            swap.allocate(process, count)
            swap.display()

        elif choice == "2":
            process = input("Enter process name: ")

            swap.release(process)
            swap.display()

        elif choice == "3":
            swap.display()

        elif choice == "4":
            print("Exiting swap management.")
            break

        else:
            print("Invalid choice.")

    print("\nSimulation completed successfully.")

except ValueError as error:
    print("\nInput Error:", error)
