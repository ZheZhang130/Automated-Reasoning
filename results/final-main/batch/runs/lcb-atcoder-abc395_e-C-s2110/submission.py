import sys
import heapq

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))
    X = int(next(iterator))
    
    # Build adjacency lists
    # adj[0][u] -> list of v for edges u->v (original orientation)
    # adj[1][u] -> list of v for edges u->v (reversed orientation, which means edges v->u in original)
    # So for each input edge u->v:
    #   In original orientation: from u we can go to v
    #   In reversed orientation: from v we can go to u
    
    adj = [[] for _ in range(N + 1)]
    rev_adj = [[] for _ in range(N + 1)]
    
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        adj[u].append(v)
        rev_adj[v].append(u)
    
    # Dijkstra's algorithm
    # State: (vertex, orientation) where orientation is 0 or 1
    # Distance array: dist[vertex][orientation]
    dist = [[float('inf')] * 2 for _ in range(N + 1)]
    
    # Priority queue: (cost, vertex, orientation)
    pq = [(0, 1, 0)]  # Start at vertex 1 in original orientation (0)
    dist[1][0] = 0
    
    while pq:
        cost, u, orientation = heapq.heappop(pq)
        
        if cost > dist[u][orientation]:
            continue
        
        # If we reached vertex N, we can stop since Dijkstra guarantees shortest path
        if u == N:
            print(cost)
            return
        
        # Option 1: Move along an edge (cost 1)
        # This keeps the same orientation
        if orientation == 0:
            for v in adj[u]:
                new_cost = cost + 1
                if new_cost < dist[v][0]:
                    dist[v][0] = new_cost
                    heapq.heappush(pq, (new_cost, v, 0))
        else:
            for v in rev_adj[u]:
                new_cost = cost + 1
                if new_cost < dist[v][1]:
                    dist[v][1] = new_cost
                    heapq.heappush(pq, (new_cost, v, 1))
        
        # Option 2: Reverse all edges (cost X)
        # This switches orientation but keeps the same vertex
        new_orientation = 1 - orientation
        new_cost = cost + X
        if new_cost < dist[u][new_orientation]:
            dist[u][new_orientation] = new_cost
            heapq.heappush(pq, (new_cost, u, new_orientation))

if __name__ == "__main__":
    solve()
