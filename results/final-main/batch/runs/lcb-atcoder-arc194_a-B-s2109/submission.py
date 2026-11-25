import sys


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(data)
    prev2, prev1 = 0, next(data)
    # Between consecutive surviving pushes (also before the first and
    # after the last), all operations are matched push/pop pairs.
    # Each such even-length gap can be replaced by adjacent pairs.
    # Thus each prefix can end in a survivor or a two-operation pair.
    for _ in range(1, n):
        a = next(data)
        prev2, prev1 = prev1, max(prev1 + a, prev2)
    print(prev1)


if __name__ == "__main__":
    main()
