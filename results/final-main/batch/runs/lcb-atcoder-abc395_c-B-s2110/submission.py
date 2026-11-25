import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    last = {}
    best = n + 1
    for i in range(1, n + 1):
        value = data[i]
        previous = last.get(value, 0)
        if previous:
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
