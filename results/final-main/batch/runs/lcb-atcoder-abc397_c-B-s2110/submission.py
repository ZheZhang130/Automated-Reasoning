import sys


def main():
    n, *a = map(int, sys.stdin.buffer.read().split())
    remaining = [0] * (n + 1)
    right_distinct = 0
    for x in a:
        if remaining[x] == 0:
            right_distinct += 1
        remaining[x] += 1

    seen = bytearray(n + 1)
    left_distinct = 0
    best = 0
    for i in range(n - 1):
        x = a[i]
        if not seen[x]:
            seen[x] = 1
            left_distinct += 1
        remaining[x] -= 1
        if remaining[x] == 0:
            right_distinct -= 1
        total = left_distinct + right_distinct
        if total > best:
            best = total

    print(best)


if __name__ == "__main__":
    main()
