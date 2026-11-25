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

    def dfs(vertex, visited, path_xor):
        nonlocal best
        if vertex == target:
            if path_xor < best:
                best = path_xor
            return
        for neighbor, bit, weight in graph[vertex]:
            if not visited & bit:
                dfs(neighbor, visited | bit, path_xor ^ weight)

    dfs(0, 1, 0)
    print(best)


if __name__ == "__main__":
    main()
