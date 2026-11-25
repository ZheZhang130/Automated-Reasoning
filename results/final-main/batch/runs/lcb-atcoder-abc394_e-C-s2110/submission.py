import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    N = int(input_data[0])
    grid = input_data[1:]
    
    adj = [[] for _ in range(N)]
    for i in range(N):
        row = grid[i]
        for j in range(N):
            c = row[j]
            if c != '-':
                adj[i].append((j, c))
    
    # State: (u, v, char) -> distance
    # char = None means completed palindrome from u to v
    dist = {}
    
    # Initial states:
    # 1. Empty path: (i, i, None) with distance 0
    # 2. Single edge: (i, j, c) with distance 1 if edge i->j exists
    
    queue = deque()
    
    for i in range(N):
        dist[(i, i, None)] = 0
        queue.append((i, i, None))
    
    for i in range(N):
        for j, c in adj[i]:
            if (i, j, c) not in dist:
                dist[(i, j, c)] = 1
                queue.append((i, j, c))
    
    while queue:
        u, v, c = queue.popleft()
        d = dist[(u, v, c)]
        
        if c is None:
            continue
        
        # Try to extend: find incoming edges to u with label c
        # and outgoing edges from v with label c
        # New state: (a, b, c) -> completed (a, b, None)
        
        # Find all a such that a->u has label c
        incoming = []
        for a in range(N):
            for nxt, nxt_c in adj[a]:
                if nxt == u and nxt_c == c:
                    incoming.append(a)
        
        # Find all b such that v->b has label c
        outgoing = []
        for nxt, nxt_c in adj[v]:
            if nxt_c == c:
                outgoing.append(nxt)
        
        for a in incoming:
            for b in outgoing:
                new_state = (a, b, None)
                if new_state not in dist:
                    dist[new_state] = d + 1
                    queue.append(new_state)
    
    # Build answer matrix
    ans = [[-1] * N for _ in range(N)]
    for (u, v, c), d in dist.items():
        if c is None:
            ans[u][v] = d
    
    for row in ans:
        print(' '.join(map(str, row)))

solve()
