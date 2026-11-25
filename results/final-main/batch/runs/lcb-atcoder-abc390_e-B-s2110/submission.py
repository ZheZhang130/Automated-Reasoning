import sys
from bisect import bisect_left


def main():
    read = sys.stdin.buffer.readline
    n, budget = map(int, read().split())
    groups = [[], [], []]
    for _ in range(n):
        vitamin, amount, cost = map(int, read().split())
        groups[vitamin - 1].append((amount, cost))

    if any(not group for group in groups):
        print(0)
        return

    best = []
    for group in groups:
        limit = min(budget, sum(cost for _, cost in group))
        dp = [0] * (limit + 1)
        for amount, cost in group:
            for calories in range(limit, cost - 1, -1):
                candidate = dp[calories - cost] + amount
                if candidate > dp[calories]:
                    dp[calories] = candidate
        best.append(dp)

    # Each row is nondecreasing: dp[c] allows spending at most c calories.
    # Find the cheapest way to meet a target independently for each vitamin.
    first, second, third = best
    low = 0
    high = min(first[-1], second[-1], third[-1]) + 1
    while high - low > 1:
        target = (low + high) // 2
        required = (bisect_left(first, target)
                    + bisect_left(second, target)
                    + bisect_left(third, target))
        if required <= budget:
            low = target
        else:
            high = target
    print(low)


if __name__ == "__main__":
    main()
