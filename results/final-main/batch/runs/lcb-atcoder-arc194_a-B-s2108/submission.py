import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]

    # Surviving pushes split the other operations into balanced blocks.
    # Each block has even length and can be replaced by push-pop pairs.
    # Thus each prefix can end in a surviving push or a zero-value pair.
    prev2, prev1 = 0, data[1]
    for i in range(2, n + 1):
        prev2, prev1 = prev1, max(prev1 + data[i], prev2)
    print(prev1)


if __name__ == "__main__":
    main()
