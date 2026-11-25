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
    
    # We'll build the graph for Dijkstra directly.
    # Nodes: 0 to N-1 for state 0 (original graph), N to 2N-1 for state 1 (reversed graph)
    num_nodes = 2 * N
    graph = [[] for _ in range(num_nodes)]
    
    # For each original edge u->v (convert to 0-indexed: u-1, v-1)
    for _ in range(M):
        u = int(next(iterator)) - 1
        v = int(next(iterator)) - 1
        
        # In state 0: u->v with cost 1
        graph[u].append((v, 1))
        # In state 1: v->u with cost 1 (because the edge is reversed)
        graph[v + N].append((u + N, 1))
        
        # Also, we can reverse edges from any node in state 0 to state 1, and vice versa.
        # From any node i in state 0, we can go to i+N in state 1 with cost X.
        # From any node i+N in state 1, we can go to i in state 0 with cost X.
        # We'll add these edges for all nodes after reading all edges.
    
    # Add reversal edges: for each vertex i, from i to i+N with cost X, and from i+N to i with cost X.
    for i in range(N):
        graph[i].append((i + N, X))
        graph[i + N].append((i, X))
    
    # Now run Dijkstra from node 0 (vertex 1, state 0)
    dist = [-1] * num_nodes
    dist[0] = 0
    pq = [(0, 0)]  # (cost, node)
    
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        if u == N - 1:
            # We reached vertex N (0-indexed N-1) in state 0.
            # But we might also reach it in state 1, so we continue to find the minimum.
            pass
        
        for v, w in graph[u]:
            if dist[v] == -1 or dist[v] > d + w:
                dist[v] = d + w
                heapq.heappush(pq, (dist[v], v))
    
    # The answer is min(dist[N-1], dist[N-1 + N])
    ans = min(dist[N-1], dist[N-1 + N])
    print(ans)

if __name__ == '__main__':
    solve()
