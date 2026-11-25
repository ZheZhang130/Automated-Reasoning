import sys


def main():
    tokens = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(tokens)
    last = {}
    best = n + 1

    for i, value in enumerate(tokens):
        previous = last.get(value)
        if previous is not None:
            length = i - previous + 1
            if length == 2:
                print(2)
                return
            if length < best:
                best = length
        last[value] = i

    print(best if best <= n else -1)


if __name__ == "__main__":
    main()
