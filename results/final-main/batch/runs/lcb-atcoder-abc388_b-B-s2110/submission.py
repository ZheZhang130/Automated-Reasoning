import sys


def main():
    values = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(values)
    d = next(values)
    snakes = [(next(values), next(values)) for _ in range(n)]

    for k in range(1, d + 1):
        print(max(t * (length + k) for t, length in snakes))


if __name__ == "__main__":
    main()
