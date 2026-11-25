import sys


def main():
    data = map(int, sys.stdin.buffer.read().split())
    n = next(data)
    last = {}
    best = n + 1

    for i, value in enumerate(data):
        previous = last.get(value)
        if previous is not None:
            best = min(best, i - previous + 1)
            if best == 2:
                break
        last[value] = i

    print(best if best <= n else -1)


if __name__ == "__main__":
    main()
