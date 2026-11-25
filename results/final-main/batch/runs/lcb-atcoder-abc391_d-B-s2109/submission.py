import sys


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(data)
    w = next(data)
    columns = [[] for _ in range(w)]
    for i in range(n):
        x = next(data) - 1
        y = next(data)
        columns[x].append((y, i))

    layers = min(map(len, columns))
    removal = [0] * layers
    rank = [0] * n
    for column in columns:
        column.sort()
        for k, (y, i) in enumerate(column):
            rank[i] = k
            if k < layers and y > removal[k]:
                removal[k] = y

    answers = []
    q = next(data)
    for _ in range(q):
        t = next(data)
        k = rank[next(data) - 1]
        answers.append("Yes" if k >= layers or t < removal[k] else "No")
    sys.stdout.write("\n".join(answers) + "\n")


if __name__ == "__main__":
    main()
