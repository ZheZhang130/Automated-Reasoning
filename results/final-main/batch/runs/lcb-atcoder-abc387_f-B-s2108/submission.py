import sys
from collections import deque

MOD = 998244353


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n, m = data[:2]
    parent = [a - 1 for a in data[2:]]
    indegree = [0] * n
    for p in parent:
        indegree[p] += 1

    # ways[v][k] counts assignments below v when x_v = k + 1.
    # None represents an array of ones.
    ways = [None] * n
    queue = deque(v for v in range(n) if indegree[v] == 0)
    while queue:
        v = queue.popleft()
        p = parent[v]
        row = ways[v]
        ways[v] = None
        if row is None:
            row = list(range(1, m + 1))
        else:
            total = 0
            for k, value in enumerate(row):
                total += value
                if total >= MOD:
                    total -= MOD
                row[k] = total

        current = ways[p]
        if current is None:
            ways[p] = row
        else:
            for k, value in enumerate(row):
                current[k] = current[k] * value % MOD

        indegree[p] -= 1
        if indegree[p] == 0:
            queue.append(p)

    # Each remaining directed cycle must use one common value.
    answer = 1
    for start in range(n):
        if indegree[start] == 0:
            continue
        product = None
        v = start
        while indegree[v]:
            indegree[v] = 0
            row = ways[v]
            if row is not None:
                if product is None:
                    product = row
                else:
                    for k, value in enumerate(row):
                        product[k] = product[k] * value % MOD
            v = parent[v]
        count = m if product is None else sum(product)
        answer = answer * count % MOD
    print(answer)


if __name__ == "__main__":
    main()
