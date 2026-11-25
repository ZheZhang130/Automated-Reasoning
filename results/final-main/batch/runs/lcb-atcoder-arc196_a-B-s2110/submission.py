import sys
from heapq import heappush, heapreplace


def even_scores(a, start, stop, step):
    lower = []
    upper = []
    score = 0
    yield score
    for i in range(start, stop, 2 * step):
        x, y = a[i], a[i + step]
        if x > y:
            x, y = y, x
        heappush(lower, -x)
        heappush(upper, y)
        score += y - x
        lo, hi = -lower[0], upper[0]
        if lo > hi:
            heapreplace(lower, -hi)
            heapreplace(upper, lo)
            score += 2 * (lo - hi)
        yield score


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n, a = data[0], data[1:]
    # For an even interval, the upper half minus the lower half is an
    # upper bound. Label the halves and repeatedly delete adjacent
    # opposite labels: equal counts guarantee such a pair until empty.
    if n % 2 == 0:
        for ans in even_scores(a, 0, n, 1):
            pass
        print(ans)
    else:
        # No pair can cross the surviving element, so both sides must
        # have even length and can be optimized independently.
        prefix = list(even_scores(a, 0, n - 1, 1))
        print(max(left + right for left, right in
                  zip(reversed(prefix), even_scores(a, n - 1, 0, -1))))


if __name__ == '__main__':
    main()
