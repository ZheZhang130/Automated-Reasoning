import sys


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(data)
    w = next(data)
    columns = [[] for _ in range(w)]
    for i in range(n):
        x = next(data)
        y = next(data)
        columns[x - 1].append((y, i))

    removed_at = [10**9 + 1] * n
    if all(columns):
        for column in columns:
            column.sort()

        # Before tick t, the lowest remaining block of a column is at
        # max(1, initial_height - (t - 1)). Thus a layer clears at the
        # maximum of its initial heights, or after the preceding clear.
        # The layer maxima strictly increase, so the latter bound is automatic.
        for layer in zip(*columns):
            time = max(layer)[0]
            for _, i in layer:
                removed_at[i] = time

    q = next(data)
    answers = []
    for _ in range(q):
        time = next(data)
        i = next(data) - 1
        answers.append("Yes" if time < removed_at[i] else "No")
    sys.stdout.write("\n".join(answers) + "\n")


if __name__ == "__main__":
    main()
