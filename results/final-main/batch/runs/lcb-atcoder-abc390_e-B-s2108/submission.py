import sys
from bisect import bisect_left


def main():
    read = sys.stdin.buffer.readline
    n, budget = map(int, read().split())
    best = [[0] * (budget + 1) for _ in range(3)]

    for _ in range(n):
        vitamin, amount, calories = map(int, read().split())
        dp = best[vitamin - 1]
        # Descending capacities prevent using the same food twice.
        for capacity in range(budget, calories - 1, -1):
            candidate = dp[capacity - calories] + amount
            if candidate > dp[capacity]:
                dp[capacity] = candidate

    first, second, third = best
    low, high = 0, min(first[-1], second[-1], third[-1]) + 1
    while high - low > 1:
        target = (low + high) // 2
        # Each row is nondecreasing, so the first qualifying index
        # gives the least calories needed for that vitamin.
        needed = (
            bisect_left(first, target)
            + bisect_left(second, target)
            + bisect_left(third, target)
        )
        if needed <= budget:
            low = target
        else:
            high = target
    print(low)


if __name__ == "__main__":
    main()
