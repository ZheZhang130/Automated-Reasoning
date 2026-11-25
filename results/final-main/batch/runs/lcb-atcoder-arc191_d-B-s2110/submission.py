import sys
from collections import deque


def solve():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n, m, s, t = next(data), next(data), next(data) - 1, next(data) - 1
    g = [[] for _ in range(n)]
    for _ in range(m):
        u, v = next(data) - 1, next(data) - 1
        g[u].append(v)
        g[v].append(u)

    def bfs(start):
        dist = [-1] * n
        dist[start] = 0
        q = deque([start])
        while q:
            u = q.popleft()
            nd = dist[u] + 1
            for v in g[u]:
                if dist[v] < 0:
                    dist[v] = nd
                    q.append(v)
        return dist

    ds = bfs(s)
    d = ds[t]
    path = [t]
    while path[-1] != s:
        u = path[-1]
        path.append(next(v for v in g[u] if ds[v] == ds[u] - 1))
    path.reverse()

    if any(len(g[u]) > 2 for u in path[1:-1]):
        # A spare neighbor at an interior vertex gives a two-move detour.
        dt = bfs(t)
        if sum(a + b == d for a, b in zip(ds, dt)) > d + 1:
            return 2 * d
        # In a route of length d+1 there is exactly one edge that
        # stays in the same BFS layer, and all others advance a layer.
        for v in range(n):
            if ds[v] + dt[v] == d:
                for u in g[v]:
                    if ds[u] == ds[v]:
                        return 2 * d + 1
        return 2 * d + 2

    # P has no interior exits. Find the shortest route bypassing P.
    seen = [-1] * n
    for u in path[1:-1]:
        seen[u] = -2
    seen[s] = 0
    q = deque([s])
    k = -1
    while q and k < 0:
        u = q.popleft()
        nd = seen[u] + 1
        for v in g[u]:
            if seen[v] != -1 or (d == 1 and u == s and v == t):
                continue
            if v == t:
                k = nd
                break
            seen[v] = nd
            q.append(v)
    ans = d + k if k >= 0 else float('inf')

    if all(len(adj) == 2 for adj in g):
        return ans

    # If the total is less than d+k, neither piece can travel from one
    # endpoint to the other outside P. Every excursion off P therefore
    # returns to its departure endpoint. Track order on P, extending it
    # at both ends along the degree-two tails. The order can only change
    # if both pieces reach past the first branch on the same side.
    # Each then walks at least d + 2*(extra+1) steps. This is achievable
    # by using two separate parking neighbors of the branch. If a
    # parking neighbor is on the approach path, that edge instead gives
    # a bypass with a smaller answer.
    for u, prev in ((s, path[1]), (t, path[-2])):
        extra = 0
        while len(g[u]) == 2:
            x, y = g[u]
            prev, u = u, y if x == prev else x
            extra += 1
        if len(g[u]) >= 3:
            ans = min(ans, 2 * d + 4 * extra + 4)
    return ans if ans != float('inf') else -1


if __name__ == '__main__':
    print(solve())
