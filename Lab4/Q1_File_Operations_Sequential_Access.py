import os
import stat


def write_initial_records(filename):
    try:
        with open(filename, "w") as file:
            file.write("101,Aarav,78\n")
            file.write("102,Meera,84\n")
            file.write("103,Kabir,91\n")
        return 0
    except OSError as error:
        print("Error writing file:", error)
        return -1


def append_record(filename):
    try:
        with open(filename, "a") as file:
            file.write("104,Diya,88\n")
        return 0
    except OSError as error:
        print("Error appending record:", error)
        return -1


def read_sequentially(filename):
    try:
        with open(filename, "r") as file:
            print("Sequential file contents:")
            for line in file:
                print(line, end="")
        return 0
    except OSError as error:
        print("Error reading file:", error)
        return -1


def show_metadata(filename):
    try:
        information = os.stat(filename)

        print("File size:", information.st_size, "bytes")

        print(
            "Permission mode:",
            format(stat.S_IMODE(information.st_mode), "03o")
        )

        return 0

    except OSError as error:
        print("Error retrieving file metadata:", error)
        return -1


def main():
    original = "students.txt"
    renamed = "students_renamed.txt"

    if write_initial_records(original) != 0:
        return

    if append_record(original) != 0:
        if os.path.exists(original):
            os.remove(original)
        return

    if read_sequentially(original) != 0:
        if os.path.exists(original):
            os.remove(original)
        return

    try:
        os.rename(original, renamed)
        print("File renamed to", renamed)

    except OSError as error:
        print("Error renaming file:", error)

        if os.path.exists(original):
            os.remove(original)

        return

    if show_metadata(renamed) != 0:
        if os.path.exists(renamed):
            os.remove(renamed)
        return

    try:
        os.remove(renamed)
        print("Controlled test file deleted successfully.")

    except OSError as error:
        print("Error deleting file:", error)


if __name__ == "__main__":
    main()