class FileSystem:

    def __init__(self, block_count):
        if block_count <= 0:
            raise ValueError("Block count must be positive")

        self.blocks = [None] * block_count
        self.files = {}

    def free_blocks(self):
        return [
            i
            for i, owner in enumerate(self.blocks)
            if owner is None
        ]

    def check_request(self, name, size):
        if not name:
            raise ValueError("File name cannot be empty")

        if name in self.files:
            raise ValueError("Duplicate file name")

        if size <= 0:
            raise ValueError("File size must be positive")

    def allocate_contiguous(self, name, size):
        self.check_request(name, size)

        for start in range(len(self.blocks) - size + 1):
            candidate = range(start, start + size)

            if all(self.blocks[i] is None for i in candidate):
                chosen = list(candidate)

                for block in chosen:
                    self.blocks[block] = name

                self.files[name] = {
                    "method": "contiguous",
                    "blocks": chosen
                }

                return True

        return False

    def allocate_linked(self, name, size):
        self.check_request(name, size)

        free = self.free_blocks()

        if len(free) < size:
            return False

        chosen = free[:size]

        for block in chosen:
            self.blocks[block] = name

        links = [
            (
                chosen[i],
                chosen[i + 1] if i + 1 < len(chosen) else None
            )
            for i in range(len(chosen))
        ]

        self.files[name] = {
            "method": "linked",
            "blocks": chosen,
            "links": links
        }

        return True

    def allocate_indexed(self, name, size):
        self.check_request(name, size)

        free = self.free_blocks()

        if len(free) < size + 1:
            return False

        index_block = free[0]
        data_blocks = free[1:size + 1]

        self.blocks[index_block] = name + ":index"

        for block in data_blocks:
            self.blocks[block] = name

        self.files[name] = {
            "method": "indexed",
            "index": index_block,
            "blocks": data_blocks
        }

        return True

    def delete(self, name):
        if name not in self.files:
            return False

        information = self.files.pop(name)

        for block in information["blocks"]:
            self.blocks[block] = None

        if information["method"] == "indexed":
            self.blocks[information["index"]] = None

        return True

    def display(self):
        print("\nFile allocation table:")

        for name, information in self.files.items():
            print(name, information)

        print("Disk map:")

        for index, owner in enumerate(self.blocks):
            print(
                index,
                owner if owner is not None else "FREE"
            )


disk = FileSystem(20)

print("A contiguous:", disk.allocate_contiguous("A", 4))

print("B linked:", disk.allocate_linked("B", 3))

print("C indexed:", disk.allocate_indexed("C", 4))

disk.display()

print("\nDelete B:", disk.delete("B"))

disk.display()