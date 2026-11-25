import sys


def main():
    values = list(map(int, sys.stdin.buffer.read().split()))
    n = values[0]
    last = [0] * (n + 1)
    right = 0
    for i in range(1, n + 1):
        x = values[i]
        if last[x] == 0:
            right += 1
        last[x] = i

    seen = bytearray(n + 1)
    left = best = 0
    for i in range(1, n):
        x = values[i]
        if not seen[x]:
            seen[x] = 1
            left += 1
        if last[x] == i:
            right -= 1
        total = left + right
        if total > best:
            best = total

    print(best)


if __name__ == "__main__":
    main()
