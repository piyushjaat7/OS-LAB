from copy import deepcopy

# VALIDATE INPUT
def validate_positive(values, label):
    if not values:
        raise ValueError(f"{label} cannot be empty.")

    if any(value <= 0 for value in values):
        raise ValueError(f"All {label} values must be positive.")


# MEMORY ALLOCATION
def allocate(blocks, processes, method):
    validate_positive(blocks, "Block")
    validate_positive(processes, "Process")

    remaining = deepcopy(blocks)
    result = [-1] * len(processes)

    for process_index, process_size in enumerate(processes):

        candidates = [
            i for i, size in enumerate(remaining)
            if size >= process_size
        ]

        if not candidates:
            continue

        if method == "first":
            chosen = candidates[0]

        elif method == "best":
            chosen = min(
                candidates,
                key=lambda i: remaining[i]
            )

        elif method == "worst":
            chosen = max(
                candidates,
                key=lambda i: remaining[i]
            )

        else:
            raise ValueError("Unknown allocation method.")

        result[process_index] = chosen
        remaining[chosen] -= process_size

    return result, remaining


# ADDRESS TRANSLATION
def translate(base, limit, logical):
    if base < 0 or limit <= 0 or logical < 0:
        raise ValueError("Invalid address translation values.")

    if logical >= limit:
        return None

    return base + logical


# DISPLAY ALLOCATION RESULTS
def print_allocation(name, blocks, processes, allocation, remaining):

    print("\n" + "=" * 55)
    print(name.upper())
    print("=" * 55)

    print(f"{'Process':<12}{'Size':<12}{'Block':<15}")

    for i, size in enumerate(processes):

        block = allocation[i]

        label = (
            "Not allocated"
            if block == -1
            else f"B{block + 1}"
        )

        print(f"P{i + 1:<11}{size:<12}{label:<15}")

    print("\nOriginal Blocks:", blocks)
    print("Remaining Blocks:", remaining)

    print("Total Free Memory:", sum(remaining))


# SWAPPING SIMULATION
class SwapManager:

    def __init__(self, memory_capacity):
        if memory_capacity <= 0:
            raise ValueError("Memory capacity must be positive.")

        self.capacity = memory_capacity
        self.main_memory = {}
        self.backing_store = {}

    def display(self):
        print("\n--- MEMORY STATUS ---")

        print("Main Memory:", self.main_memory)
        print("Backing Store:", self.backing_store)

        used = sum(self.main_memory.values())

        print("Memory Used:", used)
        print("Memory Free:", self.capacity - used)

    def load_process(self, process, size):

        if size <= 0:
            print("Invalid process size.")
            return False

        if process in self.main_memory:
            print("Process is already in main memory.")
            return False

        if process not in self.backing_store:
            print("Process not found in backing store.")
            return False

        if sum(self.main_memory.values()) + size > self.capacity:
            print("Insufficient main memory.")
            return False

        self.main_memory[process] = self.backing_store.pop(process)

        print(f"{process} swapped IN to main memory.")
        self.display()

        return True

    def swap_out(self, process):

        if process not in self.main_memory:
            print("Process is not present in main memory.")
            return False

        size = self.main_memory.pop(process)

        self.backing_store[process] = size

        print(f"{process} swapped OUT to backing store.")
        self.display()

        return True

    def add_process(self, process, size):

        if size <= 0:
            print("Invalid process size.")
            return False

        if process in self.main_memory or process in self.backing_store:
            print("Process already exists.")
            return False

        if sum(self.main_memory.values()) + size <= self.capacity:

            self.main_memory[process] = size

            print(f"{process} loaded into main memory.")
            self.display()

            return True

        else:
            self.backing_store[process] = size

            print(f"{process} placed in backing store.")
            print("Main memory does not have enough space.")

            self.display()

            return False


# MAIN PROGRAM

print("=" * 55)
print("CONTIGUOUS MEMORY ALLOCATION SIMULATION")
print("=" * 55)

try:

    # MEMORY BLOCKS
    blocks = [100, 500, 200, 300, 600]

    # PROCESS SIZES
    processes = [212, 417, 112, 426]

    print("\nMemory Blocks:", blocks)
    print("Process Sizes:", processes)

    # FIRST FIT, BEST FIT AND WORST FIT
    for method in ["first", "best", "worst"]:

        allocation, remaining = allocate(
            blocks,
            processes,
            method
        )

        print_allocation(
            method + " Fit",
            blocks,
            processes,
            allocation,
            remaining
        )

    # ADDRESS TRANSLATION
    print("\n" + "=" * 55)
    print("LOGICAL TO PHYSICAL ADDRESS TRANSLATION")
    print("=" * 55)

    base = 1000
    limit = 400
    logical = 250

    print("Base Address:", base)
    print("Limit:", limit)
    print("Logical Address:", logical)

    physical = translate(base, limit, logical)

    if physical is None:
        print("Invalid logical address.")
    else:
        print("\nPhysical Address = Base + Logical Address")
        print(f"Physical Address = {base} + {logical}")
        print("Physical Address =", physical)

    # INVALID ADDRESS TEST
    print("\nTesting Invalid Logical Address:")

    invalid_logical = 450

    result = translate(base, limit, invalid_logical)

    if result is None:
        print("Logical Address:", invalid_logical)
        print("Error: Address exceeds memory limit.")

    # SWAPPING SIMULATION
    print("\n" + "=" * 55)
    print("PROCESS SWAPPING SIMULATION")
    print("=" * 55)

    swap = SwapManager(1000)

    swap.add_process("P1", 400)
    swap.add_process("P2", 300)
    swap.add_process("P3", 500)

    # Swap P1 out of main memory
    swap.swap_out("P1")

    # Load P3 into main memory
    swap.load_process("P3", 500)

    print("\nFinal Memory Status:")
    swap.display()

    print("\nSimulation completed successfully.")

except ValueError as error:
    print("\nInput Error:", error)
