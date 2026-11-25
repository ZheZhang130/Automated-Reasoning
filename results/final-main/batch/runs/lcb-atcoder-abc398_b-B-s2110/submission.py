import sys
from collections import Counter


def main():
    counts = Counter(map(int, sys.stdin.buffer.read().split()))
    frequencies = sorted(counts.values(), reverse=True)
    print("Yes" if len(frequencies) >= 2 and frequencies[0] >= 3 and frequencies[1] >= 2 else "No")


if __name__ == "__main__":
    main()
