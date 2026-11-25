import sys
from collections import Counter


def main():
    cards = map(int, sys.stdin.buffer.read().split())
    counts = sorted(Counter(cards).values(), reverse=True)
    print("Yes" if len(counts) >= 2 and counts[0] >= 3 and counts[1] >= 2 else "No")


if __name__ == "__main__":
    main()
