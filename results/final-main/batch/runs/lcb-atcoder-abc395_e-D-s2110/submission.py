import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    
    try:
        N = int(next(iterator))
        M = int(next(iterator))
        X = int(next(iterator))
    except StopIteration:
        return

    # Build adjacency lists for original graph and reversed graph
    # Original: u -> v
    # Reversed: v -> u
    adj = [[] for _ in range(N + 1)]
    rev_adj = [[] for _ in range(N + 1)]
    
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        adj[u].append(v)
        rev_adj[v].append(u)

    # We need to find the minimum cost to reach N from 1.
    # States: (vertex, orientation)
    # orientation 0: original edges active
    # orientation 1: reversed edges active
    # Transitions:
    #   From (u, 0):
    #     - Move to v in adj[u]: cost 1, state (v, 0)
    #     - Reverse edges: cost X, state (u, 1)
    #   From (u, 1):
    #     - Move to v in rev_adj[u]: cost 1, state (v, 1)
    #     - Reverse edges: cost X, state (u, 0)
    
    # This is a shortest path problem on a graph with 2*N nodes.
    # We can use Dijkstra's algorithm.
    
    # dist[u][0] = min cost to reach u with original orientation
    # dist[u][1] = min cost to reach u with reversed orientation
    INF = float('inf')
    dist = [[INF, INF] for _ in range(N + 1)]
    dist[1][0] = 0
    
    # Priority queue: (cost, u, orientation)
    import heapq
    pq = [(0, 1, 0)]
    
    while pq:
        d, u, orient = heapq.heappop(pq)
        
        if d > dist[u][orient]:
            continue
        
        if u == N:
            # We found a path to N, but we need to check if there's a cheaper way
            # Actually, Dijkstra guarantees first time we pop N is optimal
            print(d)
            return
        
        # Try moving along edges
        if orient == 0:
            for v in adj[u]:
                if dist[v][0] > d + 1:
                    dist[v][0] = d + 1
                    heapq.heappush(pq, (d + 1, v, 0))
        else:
            for v in rev_adj[u]:
                if dist[v][1] > d + 1:
                    dist[v][1] = d + 1
                    heapq.heappush(pq, (d + 1, v, 1))
        
        # Try reversing edges
        new_orient = 1 - orient
        new_cost = d + X
        if dist[u][new_orient] > new_cost:
            dist[u][new_orient] = new_cost
            heapq.heappush(pq, (new_cost, u, new_orient))
    
    # If we exit the loop without returning, something is wrong (should not happen per problem guarantee)
    print(-1)

if __name__ == "__main__":
    solve()
