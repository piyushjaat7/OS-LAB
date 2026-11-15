def validate(reference, capacity):
    if not reference:
        raise ValueError("Reference string cannot be empty.")

    if capacity <= 0:
        raise ValueError("Frame count must be positive.")


# FIFO PAGE REPLACEMENT
def fifo(reference, capacity):
    validate(reference, capacity)

    frames = []
    pointer = 0
    hits = 0
    faults = 0
    trace = []

    for page in reference:
        if page in frames:
            hits += 1
            status = "HIT"
        else:
            faults += 1
            status = "PAGE FAULT"

            if len(frames) < capacity:
                frames.append(page)
            else:
                frames[pointer] = page
                pointer = (pointer + 1) % capacity

        trace.append((page, frames[:], status))

    return hits, faults, trace


# LRU PAGE REPLACEMENT
def lru(reference, capacity):
    validate(reference, capacity)

    frames = []
    last_used = {}
    hits = 0
    faults = 0
    trace = []

    for position, page in enumerate(reference):
        if page in frames:
            hits += 1
            status = "HIT"
        else:
            faults += 1
            status = "PAGE FAULT"

            if len(frames) < capacity:
                frames.append(page)
            else:
                victim = min(
                    frames,
                    key=lambda item: last_used[item]
                )

                index = frames.index(victim)
                frames[index] = page

        last_used[page] = position

        trace.append((page, frames[:], status))

    return hits, faults, trace


# OPTIMAL PAGE REPLACEMENT
def optimal(reference, capacity):
    validate(reference, capacity)

    frames = []
    hits = 0
    faults = 0
    trace = []

    for position, page in enumerate(reference):
        if page in frames:
            hits += 1
            status = "HIT"
        else:
            faults += 1
            status = "PAGE FAULT"

            if len(frames) < capacity:
                frames.append(page)
            else:
                future = reference[position + 1:]

                distances = []

                for loaded in frames:
                    if loaded in future:
                        distances.append(future.index(loaded))
                    else:
                        distances.append(float("inf"))

                victim_index = max(
                    range(len(frames)),
                    key=lambda i: distances[i]
                )

                frames[victim_index] = page

        trace.append((page, frames[:], status))

    return hits, faults, trace


# DISPLAY RESULTS
def show(name, result, total):
    hits, faults, trace = result

    print("\n" + "=" * 55)
    print(name, "PAGE REPLACEMENT")
    print("=" * 55)

    print("\nPage\tFrames\t\tStatus")

    for page, frames, status in trace:
        print(f"{page}\t{str(frames):<16}\t{status}")

    hit_ratio = hits / total
    fault_ratio = faults / total

    print("\nTotal References:", total)
    print("Total Hits:", hits)
    print("Total Page Faults:", faults)

    print("Hit Ratio:", round(hit_ratio, 3))
    print("Fault Ratio:", round(fault_ratio, 3))

    print("Hit Percentage:", round(hit_ratio * 100, 2), "%")
    print("Fault Percentage:", round(fault_ratio * 100, 2), "%")

    return faults


# MAIN PROGRAM
print("=" * 55)
print("DEMAND PAGING AND PAGE REPLACEMENT SIMULATION")
print("=" * 55)

try:
    reference = list(map(
        int,
        input("\nEnter page reference string (space separated): ").split()
    ))

    frame_counts = list(map(
        int,
        input("Enter frame counts to test (space separated): ").split()
    ))

    if not reference:
        raise ValueError("Reference string cannot be empty.")

    if not frame_counts or any(count <= 0 for count in frame_counts):
        raise ValueError("All frame counts must be positive.")

    for capacity in frame_counts:

        print("\n\n" + "#" * 55)
        print("NUMBER OF FRAMES:", capacity)
        print("#" * 55)

        total = len(reference)

        fifo_faults = show(
            "FIFO",
            fifo(reference, capacity),
            total
        )

        lru_faults = show(
            "LRU",
            lru(reference, capacity),
            total
        )

        optimal_faults = show(
            "OPTIMAL",
            optimal(reference, capacity),
            total
        )

        # PERFORMANCE COMPARISON
        print("\n--- PERFORMANCE COMPARISON ---")

        print("FIFO Page Faults:", fifo_faults)
        print("LRU Page Faults:", lru_faults)
        print("Optimal Page Faults:", optimal_faults)

        if fifo_faults <= lru_faults and fifo_faults <= optimal_faults:
            best = "FIFO"
        elif lru_faults <= optimal_faults:
            best = "LRU"
        else:
            best = "OPTIMAL"

        print("Lowest Page Faults:", best)

        # THRASHING DETECTION
        print("\n--- THRASHING ANALYSIS ---")

        fault_ratio = max(
            fifo_faults,
            lru_faults,
            optimal_faults
        ) / total

        print("Highest Fault Ratio:", round(fault_ratio, 3))

        if fault_ratio >= 0.75:
            print("High page fault rate detected.")
            print("This is a simplified example of THRASHING.")
        else:
            print("No high page fault case detected.")

    print("\nSimulation completed successfully.")

except ValueError as error:
    print("\nInput Error:", error)
