import sys


def main():
    n, m, *values = map(int, sys.stdin.buffer.read().split())
    present = set(values)
    missing = [x for x in range(1, n + 1) if x not in present]
    print(len(missing))
    print(*missing)


if __name__ == "__main__":
    main()
