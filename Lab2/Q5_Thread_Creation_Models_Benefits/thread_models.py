import threading
import time
import os

# Configuration
NUM_TASKS = 4
WORK_PER_TASK = 2_000_000

def calculate_work(start, end):
    """Perform a consistent CPU-bound workload."""
    total = 0
    for number in range(start, end):
        total += number % 7
    return total


def single_threaded():
    """Execute all tasks sequentially in one thread."""
    print("\n========== SINGLE-THREADED EXECUTION ==========")

    start_time = time.perf_counter()
    results = []

    for task_id in range(NUM_TASKS):
        start = task_id * WORK_PER_TASK
        end = start + WORK_PER_TASK

        print(
            f"Main thread ID: {threading.get_ident()} | "
            f"Task {task_id + 1}/{NUM_TASKS} started"
        )

        result = calculate_work(start, end)
        results.append(result)

        print(f"Task {task_id + 1} completed")

    elapsed = time.perf_counter() - start_time

    print(f"Single-threaded time: {elapsed:.4f} seconds")
    return results, elapsed


def worker(task_id, results, lock):
    """Worker function executed by each thread."""
    thread_id = threading.get_ident()

    print(
        f"[Thread {task_id + 1}] ID: {thread_id} | "
        f"Task started"
    )

    start = task_id * WORK_PER_TASK
    end = start + WORK_PER_TASK

    result = calculate_work(start, end)

    # Protect shared results
    with lock:
        results[task_id] = result

    print(f"[Thread {task_id + 1}] Task completed")


def multi_threaded():
    """Execute independent tasks using multiple threads."""
    print("\n========== MULTITHREADED EXECUTION ==========")

    results = [None] * NUM_TASKS
    lock = threading.Lock()
    threads = []

    start_time = time.perf_counter()

    for task_id in range(NUM_TASKS):
        thread = threading.Thread(
            target=worker,
            args=(task_id, results, lock),
            name=f"Worker-{task_id + 1}"
        )
        threads.append(thread)
        thread.start()

    # Wait for every worker to finish
    for thread in threads:
        thread.join()

    elapsed = time.perf_counter() - start_time

    print("All worker threads have completed.")
    print(f"Multithreaded time: {elapsed:.4f} seconds")

    return results, elapsed


def explain_threading_concepts():
    """Print key theory points for the assignment."""
    print("\n========== THREADING CONCEPTS ==========")

    print("1. User-level threads:")
    print("   Managed by a user-space thread library.")

    print("\n2. Kernel-level threads:")
    print("   Managed and scheduled by the operating system.")

    print("\n3. Multithreading models:")
    print("   Many-to-One, One-to-One, and Many-to-Many.")

    print("\n4. Responsiveness:")
    print("   A separate thread can keep an application responsive.")

    print("\n5. Resource sharing:")
    print("   Threads in a process share memory and process resources.")

    print("\n6. Concurrency:")
    print("   Multiple tasks make progress over overlapping time periods.")

    print("\n7. Parallelism:")
    print("   Tasks execute simultaneously on multiple CPU cores.")

    print("\n8. Race condition:")
    print("   Concurrent access to shared data can cause incorrect results.")

    print("\n9. Deadlock:")
    print("   Threads wait indefinitely for resources held by each other.")

    print("\n10. Overhead:")
    print("    Creating, scheduling, and synchronizing threads costs time.")


def main():
    print("THREAD CREATION, MODELS AND BENEFITS")
    print(f"Python CPU count reported by OS: {os.cpu_count()}")
    print(f"Number of independent tasks: {NUM_TASKS}")
    print(f"Work per task: {WORK_PER_TASK:,} iterations")

    # Both approaches execute the same tasks
    single_results, single_time = single_threaded()
    multi_results, multi_time = multi_threaded()

    print("\n========== PERFORMANCE COMPARISON ==========")

    if single_results == multi_results:
        print("Correctness check: PASS (results match)")
    else:
        print("Correctness check: FAIL (results differ)")

    print(f"Single-threaded time:    {single_time:.4f} seconds")
    print(f"Multithreaded time:      {multi_time:.4f} seconds")

    if multi_time > 0:
        print(f"Time ratio (single/multi): {single_time / multi_time:.2f}x")

    print(
        "\nNote: CPU-bound Python threads may not be faster "
        "because of the CPython GIL and thread overhead."
    )

    explain_threading_concepts()


if __name__ == "__main__":
    main()
