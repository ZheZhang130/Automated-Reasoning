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
    if d == -1:
        print(-1)
        return

    # Reconstruct one shortest path from S to T
    parent = [0] * (N + 1)
    q = deque([S])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if dist[v] == dist[u] + 1 and parent[v] == 0:
                parent[v] = u
                q.append(v)
                if v == T:
                    break
    path = []
    cur = T
    while cur != S:
        path.append(cur)
        cur = parent[cur]
    path.append(S)
    path.reverse()
    internal_nodes = set(path[1:-1])

    # Count shortest paths from S to T
    num_paths = [0] * (N + 1)
    num_paths[S] = 1
    order = sorted(range(1, N + 1), key=lambda x: dist[x])
    for u in order:
        if num_paths[u] == 0:
            continue
        for v in adj[u]:
            if dist[v] == dist[u] + 1:
                num_paths[v] += num_paths[u]
                if num_paths[v] > 2:
                    num_paths[v] = 2
    if num_paths[T] >= 2:
        print(2 * d)
        return

    # Check for path of length d+1
    for u in range(1, N + 1):
        for v in adj[u]:
            if dist[u] == dist[v] and dist[u] + 1 + dist[v] == d + 1:
                print(2 * d + 1)
                return

    # Check internal nodes of shortest path for degree >= 3
    for u in internal_nodes:
        if len(adj[u]) >= 3:
            print(2 * d + 2)
            return

    # BFS from S ignoring edges of the shortest path
    dist_no_path = [-1] * (N + 1)
    dist_no_path[S] = 0
    q = deque([S])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if dist_no_path[v] == -1:
                # Check if edge (u,v) is on the shortest path
                if u == path[0] and v == path[1]:
                    continue
                if u == path[-1] and v == path[-2]:
                    continue
                if u in internal_nodes and v in internal_nodes and abs(dist[u] - dist[v]) == 1:
                    continue
                dist_no_path[v] = dist_no_path[u] + 1
                q.append(v)
                if v == T:
                    break
    bypass = dist_no_path[T]
    if bypass != -1:
        print(d + bypass)
        return

    # Check outward sides of endpoints
    def check_endpoint(start, end, path_nodes):
        # Build the chain from start away from the shortest path
        cur = start
        prev = None
        dist_a = 0
        while True:
            neighbors = adj[cur]
            next_candidates = [n for n in neighbors if n != prev]
            if len(next_candidates) == 0:
                return None
            if len(next_candidates) == 1:
                cand = next_candidates[0]
                if cand in path_nodes:
                    prev = cur
                    cur = cand
                    dist_a += 1
                    continue
                else:
                    break
            else:
                break
        # Now cur is the branching vertex
        valid_neighbors = []
        for n in adj[cur]:
            if n != prev and n not in path_nodes:
                valid_neighbors.append(n)
        if len(valid_neighbors) >= 2:
            return 2 * d + 4 * dist_a + 4
        return None

    s_side = check_endpoint(S, T, set(path))
    if s_side is not None:
        print(s_side)
    else:
        t_side = check_endpoint(T, S, set(path))
        if t_side is not None:
            print(t_side)
        else:
            print(-1)

solve()
