import sys
import heapq

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    iterator = iter(data)
    
    N = int(next(iterator))
    M = int(next(iterator))
    X = int(next(iterator))
    
    # We'll store edges and then build the graph
    edges = []
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        edges.append((u, v))
    
    # We model the state as (vertex, orientation) where orientation is 0 or 1.
    # State 0: original graph
    # State 1: reversed graph
    # Nodes: 0 to N-1 for state 0, and N to 2N-1 for state 1.
    # For each original edge u->v (1-indexed):
    #   - In state 0: u->v with cost 1
    #   - In state 1: v->u with cost 1 (because the edge is reversed)
    # Reversal operation: from any node in state 0, go to state 1 with cost X, and vice versa.
    
    num_nodes = 2 * N
    graph = [[] for _ in range(num_nodes)]
    
    for u, v in edges:
        u0 = u - 1
        v0 = v - 1
        
        # In state 0: u->v
        graph[u0].append((v0, 1))
        # In state 1: v->u (because the edge is reversed)
        graph[v0 + N].append((u0 + N, 1))
        
        # Add reversal edges for this vertex pair? No, we add them for all vertices.
        # But we'll add them after the loop.
    
    # Add reversal edges: for each vertex i, from i to i+N with cost X, and from i+N to i with cost X.
    for i in range(N):
        graph[i].append((i + N, X))
        graph[i + N].append((i, X))
    
    # Run Dijkstra from node 0 (vertex 1, state 0)
    dist = [-1] * num_nodes
    dist[0] = 0
    pq = [(0, 0)]  # (cost, node)
    
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            if dist[v] == -1 or dist[v] > d + w:
                dist[v] = d + w
                heapq.heappush(pq, (dist[v], v))
    
    # The answer is min(dist[N-1], dist[N-1 + N])
    ans = min(dist[N-1], dist[N-1 + N])
    print(ans)

if __name__ == '__main__':
    solve()
