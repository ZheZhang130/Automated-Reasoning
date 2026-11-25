import sys
from collections import deque

MOD = 998244353


def main():
    n, m, *a = map(int, sys.stdin.buffer.read().split())
    a = [v - 1 for v in a]
    indegree = [0] * n
    for v in a:
        indegree[v] += 1

    q = deque(i for i in range(n) if indegree[i] == 0)
    ways = [None] * n
    leaf = list(range(1, m + 1))

    while q:
        u = q.popleft()
        v = a[u]
        row = ways[u]
        ways[u] = None
        if row is None:
            row = leaf
        else:
            total = 0
            for j, value in enumerate(row):
                total += value
                if total >= MOD:
                    total -= MOD
                row[j] = total

        other = ways[v]
        if other is None:
            ways[v] = leaf.copy() if row is leaf else row
        else:
            ways[v] = [x * y % MOD for x, y in zip(other, row)]

        indegree[v] -= 1
        if indegree[v] == 0:
            q.append(v)

    answer = 1
    for i in range(n):
        if indegree[i] == 0:
            continue
        row = None
        u = i
        while indegree[u]:
            indegree[u] = 0
            other = ways[u]
            if other is not None:
                if row is None:
                    row = other
                else:
                    row = [x * y % MOD for x, y in zip(row, other)]
            u = a[u]
        answer = answer * (m if row is None else sum(row)) % MOD
    print(answer)


if __name__ == "__main__":
    main()
