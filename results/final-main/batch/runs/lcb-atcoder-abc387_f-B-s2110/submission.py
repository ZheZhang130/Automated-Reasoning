import sys
from collections import deque

MOD = 998244353


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n, m = data[:2]
    parent = [x - 1 for x in data[2:]]
    indeg = [0] * n
    for v in parent:
        indeg[v] += 1

    # A missing row represents an all-ones row. Otherwise row[t] is
    # the number of assignments below the vertex when its value is t+1.
    rows = [None] * n
    queue = deque(i for i in range(n) if indeg[i] == 0)
    while queue:
        u = queue.popleft()
        v = parent[u]
        row = rows[u]
        rows[u] = None
        if row is None:
            row = list(range(1, m + 1))
        else:
            total = 0
            for j, count in enumerate(row):
                total += count
                if total >= MOD:
                    total -= MOD
                row[j] = total

        other = rows[v]
        if other is None:
            rows[v] = row
        else:
            rows[v] = [a * b % MOD for a, b in zip(other, row)]
        indeg[v] -= 1
        if indeg[v] == 0:
            queue.append(v)

    # Every remaining vertex belongs to a cycle, whose values must agree.
    ans = 1
    for start in range(n):
        if indeg[start] == 0:
            continue
        product = None
        u = start
        while indeg[u]:
            indeg[u] = 0
            row = rows[u]
            if row is not None:
                if product is None:
                    product = row
                else:
                    product = [a * b % MOD for a, b in zip(product, row)]
            u = parent[u]
        ans = ans * (m if product is None else sum(product)) % MOD
    print(ans)


if __name__ == "__main__":
    main()
