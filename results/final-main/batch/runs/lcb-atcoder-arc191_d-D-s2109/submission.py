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

    # BFS to find shortest path from S to T
    dist = [-1] * (N + 1)
    dist[S] = 0
    q = deque([S])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                q.append(v)

    if dist[T] == -1:
        print(-1)
        return

    # If N == 2, only two vertices exist, so no buffer vertex.
    if N == 2:
        print(-1)
        return

    # Compute distances from T to all nodes
    dist_from_T = [-1] * (N + 1)
    dist_from_T[T] = 0
    q = deque([T])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if dist_from_T[v] == -1:
                dist_from_T[v] = dist_from_T[u] + 1
                q.append(v)

    # Find min dist(w, T) for w in neighbors(S) such that w != T
    min_dist = float('inf')
    for w in adj[S]:
        if w != T:
            min_dist = min(min_dist, dist_from_T[w])

    # If min_dist is still inf, it means all neighbors of S are T, which is impossible for N > 2.
    if min_dist == float('inf'):
        print(-1)
    else:
        # The answer is dist(S, T) + 1 + min_dist
        # But wait, let's reconsider the sample.
        # Sample 1: S=3, T=4. dist(S,T)=1. Neighbors of S=3: 4, 2. Exclude 4, so w=2.
        # dist(2, T=4) = 1. Answer = 1 + 1 + 1 = 3. Correct.
        # Sample 3: S=3, T=5. Let's compute dist(S,T).
        # Edges: 1-2, 2-3, 1-5, 2-4, 1-3, 2-5.
        # Path from 3 to 5: 3-1-5 (length 2) or 3-2-5 (length 2).
        # So dist(S,T)=2.
        # Neighbors of S=3: 2, 1.
        # dist_from_T[2] = dist(2,5) = 1 (edge 2-5).
        # dist_from_T[1] = dist(1,5) = 1 (edge 1-5).
        # min_dist = 1.
        # Answer = 2 + 1 + 1 = 4. Correct!
        print(dist[T] + 1 + min_dist)

if __name__ == "__main__":
    solve()
