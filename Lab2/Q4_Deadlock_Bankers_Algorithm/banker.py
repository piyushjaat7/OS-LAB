
allocation = [
    [0, 1, 0],
    [2, 0, 0],
    [3, 0, 2],
    [2, 1, 1],
    [0, 0, 2]
]

maximum = [
    [7, 5, 3],
    [3, 2, 2],
    [9, 0, 2],
    [2, 2, 2],
    [4, 3, 3]
]

available = [3, 3, 2]

processes = len(allocation)
resources = len(available)

need = [
    [
        maximum[i][j] - allocation[i][j]
        for j in range(resources)
    ]
    for i in range(processes)
]

work = available[:]
finish = [False] * processes
safe_sequence = []

while len(safe_sequence) < processes:
    progress = False

    for i in range(processes):
        if finish[i]:
            continue

        can_finish = all(
            need[i][j] <= work[j]
            for j in range(resources)
        )

        if can_finish:
            for j in range(resources):
                work[j] += allocation[i][j]

            finish[i] = True
            safe_sequence.append(i)
            progress = True

    if not progress:
        break

print("Need matrix:")
for row in need:
    print(row)

if len(safe_sequence) == processes:
    print("Safe state")
    print(
        "Safe sequence:",
        ["P" + str(i) for i in safe_sequence]
    )
else:
    print("Unsafe state")
