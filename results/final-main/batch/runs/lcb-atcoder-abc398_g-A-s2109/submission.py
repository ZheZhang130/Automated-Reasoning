import sys
import sys
from sys import stdin

def solve():
    input = stdin.read().split()
    it = iter(input)
    N = int(next(it))
    M = int(next(it))
    
    # Build adjacency list
    adj = [[] for _ in range(N + 1)]
    for _ in range(M):
        u = int(next(it))
        v = int(next(it))
        adj[u].append(v)
        adj[v].append(u)
    
    # The graph is bipartite (no odd cycles).
    # We need to count the number of edges that can be added without creating an odd cycle.
    # An edge (u, v) can be added iff u and v are in the same partition of the bipartite graph.
    # The maximum number of edges in a bipartite graph with partitions of size A and B is A*B.
    # The number of edges we can add is (A*B - M).
    # The game is: players add edges. Each move reduces the "available moves" by 1.
    # The game ends when no more edges can be added.
    # Total moves = A*B - M.
    # If total moves is odd, first player (Aoki) wins.
    # If total moves is even, second player (Takahashi) wins.
    
    # Check bipartiteness and count partition sizes
    color = [-1] * (N + 1)
    from collections import deque
    q = deque()
    
    # We need to handle disconnected components
    for i in range(1, N + 1):
        if color[i] == -1:
            color[i] = 0
            q.append(i)
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if color[v] == -1:
                        color[v] = 1 - color[u]
                        q.append(v)
                    elif color[v] == color[u]:
                        # This should not happen given the problem statement
                        pass
    
    # Count sizes of partitions
    cnt0 = 0
    cnt1 = 0
    for i in range(1, N + 1):
        if color[i] == 0:
            cnt0 += 1
        else:
            cnt1 += 1
    
    max_edges = cnt0 * cnt1
    can_add = max_edges - M
    
    if can_add % 2 == 1:
        print("Aoki")
    else:
        print("Takahashi")

if __name__ == "__main__":
    solve()
