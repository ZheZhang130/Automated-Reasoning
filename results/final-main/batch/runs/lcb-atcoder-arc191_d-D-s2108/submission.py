import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
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
    
    # BFS from S to get distance to T
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
    
    # If N=2, they are adjacent and there's no other vertex to park, so impossible.
    if N == 2:
        print(-1)
    else:
        # If they are adjacent (d=1), we need 3 moves.
        # Otherwise, we need 2*d moves.
        if d == 1:
            print(3)
        else:
            print(2 * d)

if __name__ == "__main__":
    solve()
