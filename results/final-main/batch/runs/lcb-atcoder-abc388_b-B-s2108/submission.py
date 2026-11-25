import sys


def main():
    values = iter(map(int, sys.stdin.buffer.read().split()))
    n, d = next(values), next(values)
    snakes = [(next(values), next(values)) for _ in range(n)]
    for k in range(1, d + 1):
        print(max(thickness * (length + k) for thickness, length in snakes))


if __name__ == "__main__":
    main()
