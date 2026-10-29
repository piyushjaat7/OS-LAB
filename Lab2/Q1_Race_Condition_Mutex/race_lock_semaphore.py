import threading
import time

# Configuration
NUM_THREADS = 4
INCREMENTS = 200_000

# Shared counter
counter = 0


def worker_unprotected():
    """Update shared counter without synchronization."""
    global counter

    for _ in range(INCREMENTS):
        counter += 1


def worker_with_lock(lock):
    """Update shared counter using a Lock."""
    global counter

    for _ in range(INCREMENTS):
        with lock:
            counter += 1


def worker_with_semaphore(semaphore):
    """Update shared counter using a Semaphore."""
    global counter

    for _ in range(INCREMENTS):
        with semaphore:
            counter += 1


def run_test(test_name, worker_function, sync_object=None):
    """Run the same workload with multiple threads."""
    global counter

    counter = 0
    expected = NUM_THREADS * INCREMENTS
    threads = []

    print(f"\n========== {test_name} ==========")
    print(f"Expected counter: {expected}")

    start_time = time.perf_counter()

    for thread_number in range(NUM_THREADS):
        if sync_object is None:
            thread = threading.Thread(
                target=worker_function,
                name=f"Worker-{thread_number + 1}"
            )
        else:
            thread = threading.Thread(
                target=worker_function,
                args=(sync_object,),
                name=f"Worker-{thread_number + 1}"
            )

        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    elapsed = time.perf_counter() - start_time

    print(f"Actual counter:   {counter}")
    print(f"Execution time:   {elapsed:.4f} seconds")
    print(
        "Correctness:      "
        + ("PASS" if counter == expected else "FAIL")
    )

    return elapsed, counter == expected


def main():
    print("RACE CONDITION, LOCK AND SEMAPHORE")
    print(f"Threads: {NUM_THREADS}")
    print(f"Increments per thread: {INCREMENTS:,}")
    print(f"Expected total: {NUM_THREADS * INCREMENTS:,}")

    # Version 1: No synchronization
    unsafe_time, unsafe_ok = run_test(
        "1. UNPROTECTED COUNTER",
        worker_unprotected
    )

    # Version 2: Lock-based synchronization
    lock = threading.Lock()
    lock_time, lock_ok = run_test(
        "2. LOCK-BASED COUNTER",
        worker_with_lock,
        lock
    )

    # Version 3: Semaphore-based synchronization
    semaphore = threading.Semaphore(1)
    semaphore_time, semaphore_ok = run_test(
        "3. SEMAPHORE-BASED COUNTER",
        worker_with_semaphore,
        semaphore
    )

    print("\n========== FINAL COMPARISON ==========")
    print(f"Unprotected: {unsafe_time:.4f} seconds")
    print(f"Lock:        {lock_time:.4f} seconds")
    print(f"Semaphore:   {semaphore_time:.4f} seconds")

    print("\nCorrectness summary:")
    print(f"Unprotected: {'PASS' if unsafe_ok else 'FAIL'}")
    print(f"Lock:        {'PASS' if lock_ok else 'FAIL'}")
    print(f"Semaphore:   {'PASS' if semaphore_ok else 'FAIL'}")

    print("\nConcepts demonstrated:")
    print("1. Race condition: unsynchronized shared-data access.")
    print("2. Lock: mutual exclusion using a mutex-like lock.")
    print("3. Semaphore: limits access to a shared resource.")
    print("4. Synchronization has execution-time overhead.")
    print(
        "5. Actual results and timings depend on the runtime "
        "and scheduling."
    )


if __name__ == "__main__":
    main()