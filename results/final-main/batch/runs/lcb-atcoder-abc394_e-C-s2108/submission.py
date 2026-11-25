import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    grid = input_data[1:]
    
    # Build adjacency lists
    adj = [[] for _ in range(N)]
    rev_adj = [[] for _ in range(N)]
    
    for i in range(N):
        row = grid[i]
        for j in range(N):
            c = row[j]
            if c != '-':
                adj[i].append((j, c))
                rev_adj[j].append((i, c))
    
    INF = 10**9
    dist = [[INF] * N for _ in range(N)]
    q = deque()
    
    # Initialize with empty paths (length 0) for self-loops
    for i in range(N):
        dist[i][i] = 0
        q.append((i, i, 0))
    
    # Initialize with single edges (length 1)
    for u in range(N):
        for v, c in adj[u]:
            if dist[u][v] == INF:
                dist[u][v] = 1
                q.append((u, v, 1))
    
    # BFS
    while q:
        u, v, d = q.popleft()
        
        # Try to extend: find incoming edge to u with label c
        # and outgoing edge from v with label c
        for a, c in rev_adj[u]:
            for b, c2 in adj[v]:
                if c == c2:
                    if dist[a][b] == INF:
                        dist[a][b] = d + 2
                        q.append((a, b, d + 2))
    
    # Output
    result = []
    for i in range(N):
        row = []
        for j in range(N):
            if dist[i][j] == INF:
                row.append(-1)
            else:
                row.append(dist[i][j])
        result.append(' '.join(map(str, row)))
    
    print('\n'.join(result))

solve()
