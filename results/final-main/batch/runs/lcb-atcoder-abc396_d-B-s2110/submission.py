import sys


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(data)
    m = next(data)
    graph = [[] for _ in range(n)]
    for _ in range(m):
        u = next(data) - 1
        v = next(data) - 1
        w = next(data)
        graph[u].append((v, 1 << v, w))
        graph[v].append((u, 1 << u, w))

    target = n - 1
    best = 1 << 60

    def dfs(u, visited, value):
        nonlocal best
        if u == target:
            if value < best:
                best = value
            return
        for v, bit, weight in graph[u]:
            if not visited & bit:
                dfs(v, visited | bit, value ^ weight)
                if best == 0:
                    return

    dfs(0, 1, 0)
    print(best)


if __name__ == "__main__":
    main()
