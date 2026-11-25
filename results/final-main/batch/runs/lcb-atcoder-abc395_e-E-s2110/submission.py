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
    
    adj = [[] for _ in range(N + 1)]
    rev_adj = [[] for _ in range(N + 1)]
    
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        adj[u].append(v)
        rev_adj[v].append(u)
    
    # dist[v][0] = min cost to reach vertex v in original orientation
    # dist[v][1] = min cost to reach vertex v in reversed orientation
    INF = float('inf')
    dist = [[INF, INF] for _ in range(N + 1)]
    dist[1][0] = 0
    
    # Priority queue: (cost, vertex, orientation)
    pq = [(0, 1, 0)]
    
    while pq:
        d, u, orientation = heapq.heappop(pq)
        
        if d > dist[u][orientation]:
            continue
        
        # Option 1: Move along a directed edge from u to v
        # If orientation is 0 (original), use adj
        # If orientation is 1 (reversed), use rev_adj
        if orientation == 0:
            neighbors = adj[u]
        else:
            neighbors = rev_adj[u]
        
        for v in neighbors:
            new_cost = d + 1
            if new_cost < dist[v][orientation]:
                dist[v][orientation] = new_cost
                heapq.heappush(pq, (new_cost, v, orientation))
        
        # Option 2: Reverse all edges
        # This toggles orientation and stays at the same vertex
        new_orientation = 1 - orientation
        new_cost = d + X
        if new_cost < dist[u][new_orientation]:
            dist[u][new_orientation] = new_cost
            heapq.heappush(pq, (new_cost, u, new_orientation))
    
    # The answer is the minimum cost to reach vertex N in either orientation
    print(min(dist[N][0], dist[N][1]))

if __name__ == "__main__":
    solve()
