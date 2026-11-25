import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    
    N = int(next(iterator))
    M = int(next(iterator))
    X = int(next(iterator))
    
    adj = [[] for _ in range(N + 1)]
    rev_adj = [[] for _ in range(N + 1)]
    
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        adj[u].append(v)
        rev_adj[v].append(u)
    
    # BFS on state (vertex, flipped)
    # flipped = 0: edges in original direction
    # flipped = 1: edges reversed
    # dist[v][f] = minimum cost to reach vertex v with edge direction state f
    
    INF = float('inf')
    dist = [[INF, INF] for _ in range(N + 1)]
    dist[1][0] = 0
    
    queue = deque()
    queue.append((1, 0))
    
    while queue:
        v, f = queue.popleft()
        d = dist[v][f]
        
        if d > dist[v][f]:
            continue
        
        # Option 1: Move along an edge in current direction
        if f == 0:
            for to in adj[v]:
                if dist[to][0] > d + 1:
                    dist[to][0] = d + 1
                    queue.append((to, 0))
        else:
            for to in rev_adj[v]:
                if dist[to][1] > d + 1:
                    dist[to][1] = d + 1
                    queue.append((to, 1))
        
        # Option 2: Reverse all edges (cost X)
        new_f = 1 - f
        new_d = d + X
        if new_d < dist[v][new_f]:
            dist[v][new_f] = new_d
            queue.append((v, new_f))
    
    ans = min(dist[N][0], dist[N][1])
    print(ans)

if __name__ == "__main__":
    solve()
