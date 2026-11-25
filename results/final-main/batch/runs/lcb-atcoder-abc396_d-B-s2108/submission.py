import sys


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n, m = next(data), next(data)
    graph = [[] for _ in range(n)]
    for _ in range(m):
        u, v, w = next(data) - 1, next(data) - 1, next(data)
        graph[u].append((v, 1 << v, w))
        graph[v].append((u, 1 << u, w))

    target = n - 1
    best = 1 << 60

    def dfs(u, seen, value):
        nonlocal best
        if u == target:
            if value < best:
                best = value
            return
        for v, bit, weight in graph[u]:
            if not (seen & bit):
                dfs(v, seen | bit, value ^ weight)
                if best == 0:
                    return

    dfs(0, 1, 0)
    print(best)


if __name__ == "__main__":
    main()
