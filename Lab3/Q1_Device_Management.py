from collections import deque

class Device:
    def __init__(self, name, device_type):
        self.name = name
        self.device_type = device_type
        self.status = "Available"
        self.owner = None
        self.queue = deque()

    def display(self):
        print(f"\nDevice: {self.name}")
        print(f"Type: {self.device_type}")
        print(f"Status: {self.status}")
        print(f"Owner: {self.owner}")
        print(f"Request Queue: {list(self.queue)}")

    def request(self, process):
        print(f"\nEvent: {process} requests {self.name}")

        if self.device_type == "dedicated":
            if self.owner is None:
                self.owner = process
                self.status = "Busy"
                print(f"{self.name} allocated to {process}")
            else:
                print(f"Request rejected! {self.name} is already assigned.")

        else:
            self.queue.append(process)
            print(f"{process} added to shared-device queue.")

        self.display()

    def release(self, process):
        print(f"\nEvent: {process} releases {self.name}")

        if self.device_type != "dedicated":
            print("Release operation applies to dedicated devices only.")
            return

        if self.owner != process:
            print("Error: Process does not own this device.")
            return

        self.owner = None
        self.status = "Available"
        print(f"{process} released {self.name}.")

        self.display()

    def service_next(self):
        print(f"\nEvent: Service next request for {self.name}")

        if not self.queue:
            print("No waiting requests.")
        else:
            process = self.queue.popleft()
            print(f"{self.name} is now serving {process}.")

        self.display()


class VirtualDevice(Device):
    def __init__(self, name):
        super().__init__(name, "virtual")

    def request(self, process):
        print(f"\nEvent: {process} requests {self.name}")
        print("Virtual device creates a software representation")
        print("of the physical device.")

        self.queue.append(process)
        print(f"{process} request submitted successfully.")

        self.display()


class Buffer:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("Buffer capacity must be positive.")

        self.capacity = capacity
        self.items = deque()

    def display(self):
        print("\nBuffer State:")
        print("Items:", list(self.items))
        print("Capacity:", self.capacity)
        print("Used:", len(self.items))
        print("Free:", self.capacity - len(self.items))

        if not self.items:
            print("Buffer is EMPTY.")
        elif len(self.items) == self.capacity:
            print("Buffer is FULL.")
        else:
            print("Buffer is PARTIALLY FILLED.")

    def put(self, item):
        print(f"\nEvent: Insert {item}")

        if len(self.items) >= self.capacity:
            print("Buffer FULL! Cannot insert.")
        else:
            self.items.append(item)
            print(f"{item} inserted successfully.")

        self.display()

    def get(self):
        print("\nEvent: Remove item")

        if not self.items:
            print("Buffer EMPTY! Nothing to remove.")
        else:
            item = self.items.popleft()
            print(f"{item} removed successfully.")

        self.display()


# MAIN PROGRAM

print("=" * 50)
print("DEVICE MANAGEMENT SIMULATION")
print("=" * 50)

# 1. Create devices
printer = Device("Printer", "dedicated")
disk = Device("SharedDisk", "shared")
virtual = VirtualDevice("VirtualPrinter")

# 2. Dedicated device allocation
print("\n--- DEDICATED DEVICE ---")

printer.request("P1")
printer.request("P2")

printer.release("P1")
printer.request("P2")

printer.release("P2")

# 3. Shared device request queue
print("\n--- SHARED DEVICE ---")

disk.request("P3")
disk.request("P4")
disk.request("P5")

disk.service_next()
disk.service_next()
disk.service_next()
disk.service_next()

# 4. Virtual device simulation
print("\n--- VIRTUAL DEVICE ---")

virtual.request("P6")
virtual.request("P7")
virtual.service_next()

# 5. Finite buffer simulation
print("\n--- FINITE BUFFER ---")

buffer = Buffer(3)

buffer.display()

buffer.put("A")
buffer.put("B")
buffer.put("C")
buffer.put("D")

buffer.get()
buffer.get()
buffer.get()
buffer.get()

# 6. CPU and device independence
print("\n--- CPU AND DEVICE INDEPENDENCE ---")

print("CPU submits an I/O request to the device.")
print("Device performs the I/O operation independently.")
print("CPU can execute other processes meanwhile.")
print("Device generates an interrupt after completion.")
print("CPU handles the interrupt and continues execution.")

print("\nSimulation completed successfully.")
