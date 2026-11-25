import sys
from collections import deque

def solve():
    data = sys.stdin.read().split()
    it = iter(data)
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
    
    # BFS from S
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
    
    # Case 1: S and T are adjacent
    if T in adj[S]:
        # Check if there's a common neighbor
        common = False
        for v in adj[S]:
            if v != T and v in adj[T]:
                common = True
                break
        if common:
            print(3)
        else:
            print(-1)
    # Case 2: S and T are not adjacent
    else:
        # We need to move A from S to T and B from T to S
        # Since they are not adjacent, they can move independently without colliding
        # The minimum moves is dist[S][T] + dist[T][S] = 2 * dist[S][T]
        print(2 * d)

solve()
