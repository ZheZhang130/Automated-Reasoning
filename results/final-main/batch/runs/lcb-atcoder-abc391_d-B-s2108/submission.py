import sys


def main():
    readline = sys.stdin.buffer.readline
    n, w = map(int, readline().split())
    columns = [[] for _ in range(w)]
    for block in range(n):
        x, y = map(int, readline().split())
        columns[x - 1].append((y, block))

    layers = min(map(len, columns))
    removal = [10**9 + 1] * n
    if layers:
        last_height = [0] * layers
        for column in columns:
            column.sort()
            for rank in range(layers):
                y, _ = column[rank]
                if y > last_height[rank]:
                    last_height[rank] = y

        # After t moves and r row removals, a surviving block at
        # one-based rank k has height max(y - t, k - r): the second
        # term accounts for the surviving blocks underneath it.
        # Thus layer k can be removed at its largest starting height,
        # and these largest heights strictly increase between layers.
        for column in columns:
            for rank, time in enumerate(last_height):
                removal[column[rank][1]] = time

    q = int(readline())
    answers = []
    for _ in range(q):
        t, a = map(int, readline().split())
        answers.append("Yes" if t < removal[a - 1] else "No")
    sys.stdout.write("\n".join(answers) + "\n")


if __name__ == "__main__":
    main()
