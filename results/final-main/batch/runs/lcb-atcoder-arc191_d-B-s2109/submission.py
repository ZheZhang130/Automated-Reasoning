import sys
from collections import deque


def distances(graph, start):
    dist = [-1] * len(graph)
    dist[start] = 0
    queue = deque([start])
    while queue:
        u = queue.popleft()
        step = dist[u] + 1
        for v in graph[u]:
            if dist[v] == -1:
                dist[v] = step
                queue.append(v)
    return dist


def solve():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n, m, s, t = next(data), next(data), next(data) - 1, next(data) - 1
    graph = [[] for _ in range(n)]
    for _ in range(m):
        u, v = next(data) - 1, next(data) - 1
        graph[u].append(v)
        graph[v].append(u)

    degree = list(map(len, graph))
    if all(d == 2 for d in degree):
        return n

    ds = distances(graph, s)
    d = ds[t]
    path = [t]
    while path[-1] != s:
        u = path[-1]
        for v in graph[u]:
            if ds[v] == ds[u] - 1:
                path.append(v)
                break
    path.reverse()

    if any(degree[u] >= 3 for u in path[1:-1]):
        # The vertex's third edge allows a swap for 2*d + 2 moves.
        # Any better solution must use two distinct simple routes.
        dt = distances(graph, t)
        shortest = [u for u in range(n) if ds[u] + dt[u] == d]
        if len(shortest) > d + 1:
            return 2 * d
        for u in shortest:
            if any(ds[v] == ds[u] for v in graph[u]):
                return 2 * d + 1
        return 2 * d + 2

    # Extend the corridor to its first non-degree-two vertex on each side.
    inner = bytearray(n)
    for u in path[1:-1]:
        inner[u] = 1

    def extend(u, previous):
        offset = 0
        while degree[u] == 2:
            inner[u] = 1
            a, b = graph[u]
            u, previous = (b if a == previous else a), u
            offset += 1
        return u, offset

    left, x = extend(s, path[1])
    right, y = extend(t, path[-2])
    length = x + d + y

    inf = 10**18
    best = inf
    if degree[left] >= 3:
        best = min(best, 2 * d + 4 * x + 4)
    if degree[right] >= 3:
        best = min(best, 2 * d + 4 * y + 4)

    # A swap can also use a cycle consisting of the corridor and a
    # shortest external connection.
    if left == right:
        best = min(best, length)
    elif degree[left] >= 3 and degree[right] >= 3:
        dist = [-1] * n
        dist[left] = 0
        queue = deque([left])
        while queue:
            u = queue.popleft()
            if u == right:
                best = min(best, length + dist[u])
                break
            for v in graph[u]:
                if inner[v] or dist[v] != -1:
                    continue
                if length == 1 and u == left and v == right:
                    continue
                dist[v] = dist[u] + 1
                queue.append(v)

    return best if best != inf else -1


if __name__ == '__main__':
    print(solve())
