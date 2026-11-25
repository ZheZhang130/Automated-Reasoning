import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    N = int(input_data[0])
    grid = input_data[1:N+1]
    
    adj = [[None]*N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            c = grid[i][j]
            if c != '-':
                adj[i][j] = c
    
    # State: (u, v, char) -> distance
    dist = {}
    
    # Initialize: all self-loops have distance 0
    for i in range(N):
        dist[(i, i, None)] = 0
    
    # Initialize: all direct edges have distance 1
    for i in range(N):
        for j in range(N):
            if adj[i][j] is not None:
                dist[(i, j, adj[i][j])] = 1
    
    # BFS queue
    q = deque()
    for key, d in dist.items():
        q.append((d, key))
    
    # Process BFS
    while q:
        d, (u, v, c) = q.popleft()
        
        # Try to extend: find incoming edges to u with label c
        # and outgoing edges from v with label c
        # New state: (incoming_node, outgoing_node, c) with distance d+1
        
        # Find all a such that a->u has label c
        for a in range(N):
            if adj[a][u] == c:
                # Find all b such that v->b has label c
                for b in range(N):
                    if adj[v][b] == c:
                        new_key = (a, b, c)
                        if new_key not in dist:
                            dist[new_key] = d + 1
                            q.append((d + 1, new_key))
    
    # Build answer matrix
    ans = [[-1]*N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            key = (i, j, None)
            if key in dist:
                ans[i][j] = dist[key]
            else:
                ans[i][j] = -1
    
    # Output
    for i in range(N):
        print(*(ans[i]))

if __name__ == "__main__":
    solve()
