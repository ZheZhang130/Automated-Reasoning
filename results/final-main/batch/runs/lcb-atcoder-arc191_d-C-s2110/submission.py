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
    path = []
    curr = T
    while curr != S:
        path.append(curr)
        for nxt in adj[curr]:
            if dist[nxt] == dist[curr] - 1:
                curr = nxt
                break
    path.append(S)
    path.reverse()
    
    # Count shortest paths from S to T (capped at 2)
    sp_count = 0
    for u in path[:-1]:
        cnt = 0
        for v in adj[u]:
            if dist[v] == dist[u] + 1:
                cnt += 1
        if cnt > 2:
            sp_count = 2
            break
        sp_count += cnt - 1
    sp_count += 1
    
    if sp_count >= 2:
        print(2 * d)
        return
    
    # Check for path of length d+1 (one same-layer edge)
    for u in path[:-1]:
        for v in adj[u]:
            if dist[v] == dist[u] + 1:
                continue
            if dist[v] == dist[u]:
                if dist[v] + dist[u] + 1 == d + 1:
                    print(2 * d + 1)
                    return
    
    # Check for branching vertex on shortest path
    for i in range(1, len(path) - 1):
        u = path[i]
        if len(adj[u]) >= 3:
            print(2 * d + 2)
            return
    
    # Check for bypass (path not using shortest path edges)
    dist_no_path = [-1] * (N + 1)
    dist_no_path[S] = 0
    q = deque([S])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if dist[v] == dist[u] + 1 and v in path:
                continue
            if dist_no_path[v] == -1:
                dist_no_path[v] = dist_no_path[u] + 1
                q.append(v)
    
    bypass_len = dist_no_path[T]
    if bypass_len != -1:
        print(d + bypass_len)
        return
    
    # Check outward chains from endpoints
    # From S
    chain_s = []
    curr = S
    while len(adj[curr]) == 2:
        chain_s.append(curr)
        nxt = None
        for v in adj[curr]:
            if v != path[0] and v != path[1]:
                nxt = v
                break
        if nxt is None:
            break
        curr = nxt
    
    if curr != S and len(adj[curr]) >= 3:
        off_neighbors = [v for v in adj[curr] if v not in path]
        if len(off_neighbors) >= 2:
            a = len(chain_s)
            print(2 * d + 4 * a + 4)
            return
    
    # From T
    chain_t = []
    curr = T
    while len(adj[curr]) == 2:
        chain_t.append(curr)
        nxt = None
        for v in adj[curr]:
            if v != path[-2] and v != path[-1]:
                nxt = v
                break
        if nxt is None:
            break
        curr = nxt
    
    if curr != T and len(adj[curr]) >= 3:
        off_neighbors = [v for v in adj[curr] if v not in path]
        if len(off_neighbors) >= 2:
            a = len(chain_t)
            print(2 * d + 4 * a + 4)
            return
    
    print(-1)

solve()
