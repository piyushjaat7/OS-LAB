def paging_translate(page_size, page_table, logical):
    if page_size <= 0:
        raise ValueError("Page size must be positive.")

    if logical < 0:
        raise ValueError("Logical address cannot be negative.")

    print("\n--- PAGING ADDRESS TRANSLATION ---")

    # Calculate page number and offset
    page = logical // page_size
    offset = logical % page_size

    print("Logical Address:", logical)
    print("Page Size:", page_size)
    print("Page Number = Logical Address // Page Size")
    print(f"Page Number = {logical} // {page_size} = {page}")

    print("\nOffset = Logical Address % Page Size")
    print(f"Offset = {logical} % {page_size} = {offset}")

    # Validate page table entry
    if page >= len(page_table):
        print("\nError: Page number is outside the page table.")
        return None

    frame = page_table[page]

    print("\nPage Table:", page_table)
    print("Frame Number:", frame)

    if frame is None or frame < 0:
        print("Error: Page is not mapped or invalid.")
        return None

    # Calculate physical address
    physical = frame * page_size + offset

    print("\nPhysical Address = Frame Number * Page Size + Offset")
    print(f"Physical Address = {frame} * {page_size} + {offset}")
    print("Physical Address =", physical)

    return physical


def segment_translate(segment_table, segment, offset):
    if segment < 0 or offset < 0:
        raise ValueError("Segment and offset must be non-negative.")

    print("\n--- SEGMENTATION ADDRESS TRANSLATION ---")

    print("Segment Number:", segment)
    print("Offset:", offset)

    # Validate segment reference
    if segment >= len(segment_table):
        print("Error: Invalid segment number.")
        return None

    base, limit = segment_table[segment]

    print("Base Address:", base)
    print("Segment Limit:", limit)

    # Validate offset against limit
    print("\nChecking Segment Reference:")

    if offset >= limit:
        print("Error: Offset exceeds segment limit.")
        return None

    # Calculate physical address
    physical = base + offset

    print("Segment is valid.")
    print("\nPhysical Address = Base Address + Offset")
    print(f"Physical Address = {base} + {offset}")
    print("Physical Address =", physical)

    return physical


# MAIN PROGRAM

print("=" * 50)
print("PAGING AND SEGMENTATION SIMULATION")
print("=" * 50)

# PAGING INPUT
print("\nEnter Paging Details")

page_size = int(input("Enter page size: "))

n = int(input("Enter number of page table entries: "))

page_table = []

print("\nEnter frame numbers (-1 for unmapped pages):")

for i in range(n):
    frame = int(input(f"Frame for Page {i}: "))

    if frame == -1:
        page_table.append(None)
    else:
        page_table.append(frame)

logical = int(input("\nEnter logical address: "))

try:
    paging_translate(page_size, page_table, logical)
except ValueError as error:
    print("Error:", error)


# SEGMENTATION INPUT
print("\n" + "=" * 50)
print("Enter Segmentation Details")

count = int(input("Enter number of segments: "))

segment_table = []

for i in range(count):
    print(f"\nSegment {i}")

    base = int(input("Enter base address: "))
    limit = int(input("Enter limit: "))

    segment_table.append((base, limit))

segment = int(input("\nEnter segment number: "))
offset = int(input("Enter segment offset: "))

try:
    segment_translate(segment_table, segment, offset)
except ValueError as error:
    print("Error:", error)


print("\nSimulation completed successfully.")
