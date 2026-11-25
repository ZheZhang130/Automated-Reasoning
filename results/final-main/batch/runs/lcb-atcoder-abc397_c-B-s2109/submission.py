import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    a = data[1:]
    remaining = [0] * (n + 1)
    right = 0
    for x in a:
        if remaining[x] == 0:
            right += 1
        remaining[x] += 1

    seen = bytearray(n + 1)
    left = best = 0
    for i in range(n - 1):
        x = a[i]
        if not seen[x]:
            seen[x] = 1
            left += 1
        remaining[x] -= 1
        if remaining[x] == 0:
            right -= 1
        total = left + right
        if total > best:
            best = total

    print(best)


if __name__ == "__main__":
    main()
