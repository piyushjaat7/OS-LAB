import os
import stat


class FreeSpaceManager:

    def __init__(self, blocks):
        if blocks <= 0:
            raise ValueError("Block count must be positive")

        self.bitmap = [0] * blocks
        self.allocations = {}

    def free_list(self):
        return [
            i
            for i, value in enumerate(self.bitmap)
            if value == 0
        ]

    def allocate(self, filename, count):
        if filename in self.allocations:
            raise ValueError("Duplicate file")

        if count <= 0:
            raise ValueError("Count must be positive")

        free = self.free_list()

        if len(free) < count:
            return False

        chosen = free[:count]

        for block in chosen:
            self.bitmap[block] = 1

        self.allocations[filename] = chosen

        return True

    def release(self, filename):
        if filename not in self.allocations:
            return False

        for block in self.allocations.pop(filename):
            self.bitmap[block] = 0

        return True

    def consistent(self):
        allocated = {
            block
            for blocks in self.allocations.values()
            for block in blocks
        }

        bitmap_allocated = {
            i
            for i, value in enumerate(self.bitmap)
            if value == 1
        }

        return allocated == bitmap_allocated


manager = FreeSpaceManager(12)

print(
    "Allocate report:",
    manager.allocate("report.txt", 4)
)

print(
    "Allocate data:",
    manager.allocate("data.csv", 5)
)

print("Bitmap:", manager.bitmap)

print("Free list:", manager.free_list())

print("Consistent:", manager.consistent())

print(
    "Release report:",
    manager.release("report.txt")
)

print("Bitmap after release:", manager.bitmap)


test_directory = "test-files"

os.makedirs(
    test_directory,
    exist_ok=True
)

path = os.path.join(
    test_directory,
    "sample.txt"
)

with open(
    path,
    "w",
    encoding="utf-8"
) as file:
    file.write("Operating Systems Lab\n")

os.chmod(path, 0o640)

mode = stat.S_IMODE(os.stat(path).st_mode)

print("Permission mode:", oct(mode))

owner_read = bool(mode & stat.S_IRUSR)

owner_write = bool(mode & stat.S_IWUSR)

group_read = bool(mode & stat.S_IRGRP)

others_access = bool(
    mode
    & (
        stat.S_IROTH
        | stat.S_IWOTH
        | stat.S_IXOTH
    )
)

print("Owner read:", owner_read)

print("Owner write:", owner_write)

print("Group read:", group_read)

print("Others have access:", others_access)

os.remove(path)
os.rmdir(test_directory)