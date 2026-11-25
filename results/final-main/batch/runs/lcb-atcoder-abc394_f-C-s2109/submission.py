import sys
sys.setrecursionlimit(300000)

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    it = iter(data)
    N = int(next(it))
    if N == 1:
        print(-1)
        return

    adj = [[] for _ in range(N + 1)]
    for _ in range(N - 1):
        u = int(next(it))
        v = int(next(it))
        adj[u].append(v)
        adj[v].append(u)

    # BFS to get parent pointers and order
    parent = [0] * (N + 1)
    order = []
    stack = [1]
    visited = [False] * (N + 1)
    visited[1] = True
    while stack:
        u = stack.pop()
        order.append(u)
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                stack.append(v)

    # dp[u] = max degree-4 vertices in subtree of u when u is connected to parent
    dp = [0] * (N + 1)
    for u in reversed(order):
        child_vals = [dp[v] for v in adj[u] if v != parent[u]]
        child_vals.sort(reverse=True)
        cnt = 0
        s = 0
        for x in child_vals:
            if x > 0:
                cnt += 1
                s += x
                if cnt == 3:
                    break
        dp[u] = 1 + s if cnt >= 3 else 0

    # For each vertex, try both cases
    best = -1
    for u in range(1, N + 1):
        child_vals = [dp[v] for v in adj[u] if v != parent[u]]
        child_vals.sort(reverse=True)
        
        # Case 1: use parent edge (need 3 children with dp > 0)
        if parent[u] != 0:
            cnt = 0
            s = 0
            for x in child_vals:
                if x > 0:
                    cnt += 1
                    s += x
                    if cnt == 3:
                        break
            if cnt >= 3:
                best = max(best, 1 + s)
        
        # Case 2: don't use parent edge (need 4 children with dp > 0)
        cnt = 0
        s = 0
        for x in child_vals:
            if x > 0:
                cnt += 1
                s += x
                if cnt == 4:
                    break
        if cnt >= 4:
            best = max(best, 1 + s)

    if best == -1:
        print(-1)
    else:
        print(3 * best + 2)

solve()
