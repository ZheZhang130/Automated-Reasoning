import sys
from bisect import bisect_left


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(data)
    x = next(data)
    groups = [[], [], []]
    for _ in range(n):
        v = next(data)
        a = next(data)
        c = next(data)
        groups[v - 1].append((a, c))

    if not all(groups):
        print(0)
        return

    tables = []
    for foods in groups:
        # dp[b] is the greatest intake achievable with at most b calories.
        limit = min(x, sum(c for _, c in foods))
        dp = [0] * (limit + 1)
        for a, c in foods:
            for b in range(limit, c - 1, -1):
                candidate = dp[b - c] + a
                if candidate > dp[b]:
                    dp[b] = candidate
        tables.append(dp)

    first, second, third = tables
    low = 0
    high = min(first[-1], second[-1], third[-1]) + 1
    while high - low > 1:
        mid = (low + high) // 2
        cost = (bisect_left(first, mid) + bisect_left(second, mid)
                + bisect_left(third, mid))
        if cost <= x:
            low = mid
        else:
            high = mid
    print(low)


if __name__ == "__main__":
    main()
