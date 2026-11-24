import struct
from dataclasses import dataclass, field


RECORD_FORMAT = "i20sf"
RECORD_SIZE = struct.calcsize(RECORD_FORMAT)

records = [
    (101, "Aarav", 78.0),
    (102, "Meera", 84.0),
    (103, "Kabir", 91.0),
    (104, "Diya", 88.0)
]


def encode_name(name):
    return name.encode("utf-8")[:20].ljust(20, b"\0")


def write_records(filename, items):
    with open(filename, "wb") as file:
        for roll, name, marks in items:
            file.write(
                struct.pack(
                    RECORD_FORMAT,
                    roll,
                    encode_name(name),
                    marks
                )
            )


def read_direct(filename, position):
    if position < 0:
        raise ValueError("Position cannot be negative")

    with open(filename, "rb") as file:
        file.seek(position * RECORD_SIZE)
        data = file.read(RECORD_SIZE)

    if len(data) != RECORD_SIZE:
        return None

    roll, raw_name, marks = struct.unpack(
        RECORD_FORMAT,
        data
    )

    name = (
        raw_name
        .split(b"\0", 1)[0]
        .decode("utf-8")
    )

    return roll, name, round(marks, 2)


index = {
    roll: position
    for position, (roll, _, _) in enumerate(records)
}


def read_indexed(filename, roll):
    if roll not in index:
        return None

    return read_direct(
        filename,
        index[roll]
    )


@dataclass
class Directory:
    name: str
    files: set = field(default_factory=set)
    children: dict = field(default_factory=dict)

    def add_file(self, filename):
        if filename in self.files or filename in self.children:
            return False

        self.files.add(filename)
        return True

    def add_directory(self, name):
        if name in self.files or name in self.children:
            return None

        child = Directory(name)
        self.children[name] = child
        return child

    def delete_file(self, filename):
        if filename not in self.files:
            return False

        self.files.remove(filename)
        return True

    def display(self, level=0):
        indent = " " * level

        print(f"{indent}[{self.name}]")

        for filename in sorted(self.files):
            print(f"{indent} - {filename}")

        for child in self.children.values():
            child.display(level + 1)


filename = "student_records.bin"

write_records(filename, records)

print(
    "Direct record 2:",
    read_direct(filename, 1)
)

print(
    "Indexed roll 103:",
    read_indexed(filename, 103)
)

print(
    "Missing roll 999:",
    read_indexed(filename, 999)
)

root = Directory("root")

student = root.add_directory("student")
lab1 = student.add_directory("Lab1")

lab1.add_file("program.c")
lab1.add_file("output.txt")

root.add_file("README.md")

print("\nDirectory tree:")
root.display()

print(
    "Duplicate file accepted:",
    lab1.add_file("program.c")
)

print(
    "Delete output:",
    lab1.delete_file("output.txt")
)