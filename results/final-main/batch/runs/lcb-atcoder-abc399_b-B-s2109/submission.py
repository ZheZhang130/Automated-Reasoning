import sys
from collections import Counter


def main():
    _, *scores = map(int, sys.stdin.buffer.read().split())
    counts = Counter(scores)
    ranks = {}
    rank = 1
    for score in sorted(counts, reverse=True):
        ranks[score] = rank
        rank += counts[score]
    print("\n".join(str(ranks[score]) for score in scores))


if __name__ == "__main__":
    main()
