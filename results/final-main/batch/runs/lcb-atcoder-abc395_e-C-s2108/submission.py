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
    
    # Build adjacency lists for both orientations
    # adj[0][u] = list of v such that u->v exists (original orientation)
    # adj[1][u] = list of v such that u->v exists in reversed orientation
    # In reversed orientation, an edge u->v becomes v->u
    # So if we have u->v in original, in reversed we have v->u
    # We'll build adj[1] by reversing the edges
    
    adj0 = [[] for _ in range(N + 1)]
    adj1 = [[] for _ in range(N + 1)]
    
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        adj0[u].append(v)
        adj1[v].append(u)  # In reversed orientation, edge becomes v->u
    
    # Dijkstra's algorithm
    # State: (vertex, orientation) where orientation 0 = original, 1 = reversed
    # Distance array
    dist = [float('inf')] * (2 * (N + 1))
    dist[0] = 0  # Start at vertex 1, orientation 0
    
    # Min-heap: (cost, vertex, orientation)
    heap = [(0, 1, 0)]
    
    while heap:
        d, u, orientation = heapq.heappop(heap)
        
        if d > dist[orientation * N + u]:
            continue
        
        # If we reached vertex N, we can stop since Dijkstra guarantees shortest path
        if u == N:
            print(d)
            return
        
        # Try moving along edges in current orientation
        if orientation == 0:
            neighbors = adj0[u]
        else:
            neighbors = adj1[u]
        
        for v in neighbors:
            new_dist = d + 1
            if new_dist < dist[orientation * N + v]:
                dist[orientation * N + v] = new_dist
                heapq.heappush(heap, (new_dist, v, orientation))
        
        # Try reversing edges
        new_dist = d + X
        if new_dist < dist[(1 - orientation) * N + u]:
            dist[(1 - orientation) * N + u] = new_dist
            heapq.heappush(heap, (new_dist, u, 1 - orientation))

if __name__ == "__main__":
    solve()
