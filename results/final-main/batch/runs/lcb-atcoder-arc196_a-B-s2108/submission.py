import sys
from heapq import heappush, heappushpop


def even_prefix_scores(values):
    lower = []  # Max heap, represented by negated values.
    upper = []
    score = 0
    yield score
    it = iter(values)
    for x, y in zip(it, it):
        # Temporarily insert both new elements into the upper half,
        # then transfer elements to restore the partition and sizes.
        t = heappushpop(upper, x)
        heappush(lower, -t)
        u = -heappushpop(lower, -y)
        heappush(upper, u)
        score += x - y - 2 * t + 2 * u
        yield score


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n, a = data[0], data[1:]
    del data

    # For an even segment, the difference of the half sums is an upper
    # bound. Color the halves differently; repeatedly delete a boundary
    # between the colors to attain it, since their counts stay equal.
    if n % 2 == 0:
        a.sort()
        k = n // 2
        print(sum(a[k:]) - sum(a[:k]))
    else:
        # No deletion can cross the surviving element. Both sides must
        # have even lengths, and their optimum scores are independent.
        left = list(even_prefix_scores(a))
        right = even_prefix_scores(reversed(a))
        print(max(l + r for l, r in zip(reversed(left), right)))


if __name__ == "__main__":
    main()
