import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    it = iter(input_data)
    N = int(next(it))
    M = int(next(it))
    S = int(next(it))
    T = int(next(it))
    
    adj = [[] for _ in range(N + 1)]
    for _ in range(M):
        u = int(next(it))
        v = int(next(it))
        adj[u].append(v)
        adj[v].append(u)
    
    # BFS from S to get distances
    dist = [-1] * (N + 1)
    dist[S] = 0
    q = deque([S])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                q.append(v)
    
    d = dist[T]
    
    # Reconstruct one shortest path from S to T
    parent = [0] * (N + 1)
    q = deque([S])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if dist[v] == dist[u] + 1 and parent[v] == 0:
                parent[v] = u
                q.append(v)
    
    path = []
    cur = T
    while cur != S:
        path.append(cur)
        cur = parent[cur]
    path.append(S)
    path.reverse()
    
    # Count shortest paths from S to T
    cnt = [0] * (N + 1)
    cnt[S] = 1
    q = deque([S])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if dist[v] == dist[u] + 1:
                cnt[v] += cnt[u]
                if cnt[v] >= 2:
                    cnt[v] = 2
                q.append(v)
    
    if cnt[T] >= 2:
        print(2 * d)
        return
    
    # Check for path of length d+1
    for u in range(1, N + 1):
        for v in adj[u]:
            if dist[u] == dist[v]:
                if dist[u] + 1 + dist[v] == d + 1:
                    print(2 * d + 1)
                    return
    
    # Check internal vertices of shortest path for degree >= 3
    for i in range(1, len(path) - 1):
        u = path[i]
        if len(adj[u]) >= 3:
            print(2 * d + 2)
            return
    
    # Check for bypass
    dist_bypass = [-1] * (N + 1)
    q = deque([S])
    dist_bypass[S] = 0
    while q:
        u = q.popleft()
        for v in adj[u]:
            if dist_bypass[v] == -1:
                dist_bypass[v] = dist_bypass[u] + 1
                q.append(v)
    
    if dist_bypass[T] != -1:
        print(d + dist_bypass[T])
        return
    
    # Check endpoints for outward chains
    def check_endpoint(start, end):
        # Follow chain from start away from path
        cur = start
        prev = path[0] if start == path[-1] else path[-1]
        steps = 0
        while True:
            neighbors = adj[cur]
            # Find neighbor that is not prev and not end
            off = [v for v in neighbors if v != prev and v != end]
            if len(off) == 0:
                return None
            if len(off) == 1:
                cur = off[0]
                steps += 1
                prev = cur
            else:
                # Branching vertex
                return steps
        return None
    
    # Check S side
    s_side = check_endpoint(S, T)
    if s_side is not None:
        print(2 * d + 4 * s_side + 4)
        return
    
    # Check T side
    t_side = check_endpoint(T, S)
    if t_side is not None:
        print(2 * d + 4 * t_side + 4)
        return
    
    print(-1)

solve()
