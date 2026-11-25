import sys
from collections import deque

def solve():
    input_data = sys.stdin.read
    data = input_data().split()
    it = iter(data)
    
    try:
        N = int(next(it))
        M = int(next(it))
    except StopIteration:
        return

    adj = [[] for _ in range(N + 1)]
    for _ in range(M):
        u = int(next(it))
        v = int(next(it))
        adj[u].append(v)
        adj[v].append(u)

    # Check bipartition and assign colors
    color = [-1] * (N + 1)
    for i in range(1, N + 1):
        if color[i] == -1:
            q = deque([i])
            color[i] = 0
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if color[v] == -1:
                        color[v] = color[u] ^ 1
                        q.append(v)
                    elif color[v] == color[u]:
                        pass

    # Count vertices in each component and their partition sizes
    visited = [False] * (N + 1)
    comp_id = [-1] * (N + 1)
    comp_count = 0
    for i in range(1, N + 1):
        if not visited[i]:
            q = deque([i])
            visited[i] = True
            comp_id[i] = comp_count
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if not visited[v]:
                        visited[v] = True
                        comp_id[v] = comp_count
                        q.append(v)
            comp_count += 1

    comp_a = [0] * comp_count
    comp_b = [0] * comp_count
    for i in range(1, N + 1):
        cid = comp_id[i]
        if color[i] == 0:
            comp_a[cid] += 1
        else:
            comp_b[cid] += 1

    # Count edges per component (each edge once)
    comp_edges = [0] * comp_count
    for u in range(1, N + 1):
        for v in adj[u]:
            if u < v:
                if comp_id[u] == comp_id[v]:
                    comp_edges[comp_id[u]] += 1

    total_moves = 0
    for cid in range(comp_count):
        a = comp_a[cid]
        b = comp_b[cid]
        max_edges = a * b
        current_edges = comp_edges[cid]
        total_moves += (max_edges - current_edges)

    if total_moves % 2 == 1:
        print("Aoki")
    else:
        print("Takahashi")

solve()
