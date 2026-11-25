import sys
from collections import deque


def solve():
    it = iter(map(int, sys.stdin.buffer.read().split()))
    n, m, s, t = next(it), next(it), next(it) - 1, next(it) - 1
    g = [[] for _ in range(n)]
    for _ in range(m):
        u, v = next(it) - 1, next(it) - 1
        g[u].append(v)
        g[v].append(u)
    deg = list(map(len, g))
    if max(deg) <= 2:
        return n if m == n else -1

    ds = [-1] * n
    par = [-1] * n
    ds[s] = 0
    q = deque([s])
    while q:
        u = q.popleft()
        nd = ds[u] + 1
        for v in g[u]:
            if ds[v] == -1:
                ds[v] = nd
                par[v] = u
                q.append(v)

    d = ds[t]
    p = [t]
    while p[-1] != s:
        p.append(par[p[-1]])
    p.reverse()

    if any(deg[u] >= 3 for u in p[1:-1]):
        # A branch on the shortest path permits a swap with two extra moves.
        # Look for a distinct path of length d or d+1 to improve that bound.
        dt = [-1] * n
        dt[t] = 0
        q.append(t)
        while q:
            u = q.popleft()
            nd = dt[u] + 1
            for v in g[u]:
                if dt[v] == -1:
                    dt[v] = nd
                    q.append(v)
        on_path_pred = [-1] * n
        for i in range(1, len(p)):
            on_path_pred[p[i]] = p[i - 1]
        extra = 2
        for u in range(n):
            if ds[u] > d:
                continue
            for v in g[u]:
                if on_path_pred[v] != u:
                    delta = ds[u] + 1 + dt[v] - d
                    if delta == 0:
                        return 2 * d
                    if delta == 1:
                        extra = 1
        return 2 * d + extra

    # All internal path vertices have degree two. An alternative simple
    # S-T path must avoid the whole path, so deleting its first edge suffices.
    first = p[1]
    alt = [-1] * n
    alt[s] = 0
    q.append(s)
    while q:
        u = q.popleft()
        if u == t:
            break
        nd = alt[u] + 1
        for v in g[u]:
            if alt[v] == -1 and not (u == s and v == first):
                alt[v] = nd
                q.append(v)
    ans = d + alt[t] if alt[t] != -1 else float('inf')

    # Without an alternative S-T traversal, every excursion from the
    # path must return to the endpoint it left. The pieces can reverse
    # order on that side only if both go beyond its degree-two tail.
    for u, prev in ((s, first), (t, p[-2])):
        length = 0
        while deg[u] == 2:
            a, b = g[u]
            prev, u = u, (b if a == prev else a)
            length += 1
        if deg[u] >= 3:
            ans = min(ans, 2 * d + 4 * length + 4)

    return -1 if ans == float('inf') else ans


if __name__ == '__main__':
    print(solve())
