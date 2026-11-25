import sys
from collections import deque

def solve():
    input = sys.stdin.read
    data = input().split()
    it = iter(data)
    
    N = int(next(it))
    M = int(next(it))
    
    adj = [[] for _ in range(N + 1)]
    for _ in range(M):
        u = int(next(it))
        v = int(next(it))
        adj[u].append(v)
        adj[v].append(u)
    
    # The graph is bipartite (no odd cycles).
    # We need to find the maximum matching size in the bipartite graph.
    # Let the two parts be A and B.
    # The game is equivalent to: players add edges that maintain bipartiteness.
    # Adding an edge between two nodes in the same partition is forbidden.
    # Adding an edge between two nodes in different partitions is allowed if not already present.
    # This is exactly the game of playing on a bipartite graph where players add edges.
    # The game ends when the graph is a complete bipartite graph between the two partitions.
    # The number of moves available is |A| * |B| - M.
    # Since Aoki goes first, if (|A| * |B| - M) is odd, Aoki wins.
    # If even, Takahashi wins.
    
    # We need to color the bipartite graph.
    color = [-1] * (N + 1)
    count_a = 0
    count_b = 0
    
    for i in range(1, N + 1):
        if color[i] == -1:
            color[i] = 0
            count_a += 1
            q = deque([i])
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if color[v] == -1:
                        color[v] = 1 - color[u]
                        q.append(v)
                    elif color[v] != 1 - color[u]:
                        # This should not happen given the problem statement
                        pass
    
    # Count nodes in each partition
    # We need to be careful: the graph might be disconnected.
    # The above loop handles disconnected components.
    
    # However, the above loop only counts nodes in the first component.
    # We need to count all nodes.
    # Let's redo the counting properly.
    
    color = [-1] * (N + 1)
    count_a = 0
    count_b = 0
    
    for i in range(1, N + 1):
        if color[i] == -1:
            color[i] = 0
            q = deque([i])
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if color[v] == -1:
                        color[v] = 1 - color[u]
                        q.append(v)
                # Count the current node
                if color[u] == 0:
                    count_a += 1
                else:
                    count_b += 1
    
    # Wait, the above counting is wrong because we count inside the BFS.
    # Let's fix it.
    
    color = [-1] * (N + 1)
    count_a = 0
    count_b = 0
    
    for i in range(1, N + 1):
        if color[i] == -1:
            color[i] = 0
            q = deque([i])
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if color[v] == -1:
                        color[v] = 1 - color[u]
                        q.append(v)
    
    for i in range(1, N + 1):
        if color[i] == 0:
            count_a += 1
        else:
            count_b += 1
    
    total_edges = count_a * count_b - M
    if total_edges % 2 == 1:
        print("Aoki")
    else:
        print("Takahashi")

solve()
