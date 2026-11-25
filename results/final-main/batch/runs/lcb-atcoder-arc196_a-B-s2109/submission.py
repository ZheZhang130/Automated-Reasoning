import sys
from heapq import heappush, heappushpop


def even_scores(values):
    """Yield the optimal scores for prefixes of lengths 0, 2, 4, ..."""
    # The upper-half sum minus the lower-half sum is an upper bound.
    # It is achieved by repeatedly deleting adjacent elements from opposite
    # halves: while elements remain, the two labels occur equally often.
    lower = []  # Negated values in the lower half.
    upper = []
    score = 0
    yield 0
    it = iter(values)
    for a, b in zip(it, it):
        # Insert a into the larger half and move its minimum to the lower half.
        x = heappushpop(upper, a)
        heappush(lower, -x)
        score += a - 2 * x
        # Insert b into the lower half and move its maximum back to the upper.
        y = -heappushpop(lower, -b)
        score += 2 * y - b
        heappush(upper, y)
        yield score


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    a = data[1:]
    if n % 2 == 0:
        for answer in even_scores(a):
            pass
    else:
        # A surviving element separates two independently deleted even segments.
        suffix = list(even_scores(reversed(a)))
        answer = max(
            left + right for left, right in zip(even_scores(a), reversed(suffix))
        )
    print(answer)


if __name__ == "__main__":
    main()
