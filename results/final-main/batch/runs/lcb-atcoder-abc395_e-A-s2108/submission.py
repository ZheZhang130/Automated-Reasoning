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
    
    # dist[v][0] = minimum cost to reach vertex v in normal graph
    # dist[v][1] = minimum cost to reach vertex v in reversed graph
    INF = float('inf')
    dist = [[INF] * 2 for _ in range(N + 1)]
    dist[1][0] = 0
    
    # Priority queue: (cost, vertex, state)
    pq = [(0, 1, 0)]
    
    while pq:
        d, u, state = heapq.heappop(pq)
        
        # If we found a shorter path to (u, state), skip
        if d > dist[u][state]:
            continue
        
        if state == 0:
            # Option 1: Move along a directed edge from u to v (stay in state 0)
            for v in adj[u]:
                new_cost = d + 1
                if new_cost < dist[v][0]:
                    dist[v][0] = new_cost
                    heapq.heappush(pq, (new_cost, v, 0))
            
            # Option 2: Reverse all edges (move to state 1)
            new_cost = d + X
            if new_cost < dist[u][1]:
                dist[u][1] = new_cost
                heapq.heappush(pq, (new_cost, u, 1))
        else:
            # state == 1: reversed graph
            # Option 1: Move along a directed edge from u to v in reversed graph
            # This means moving from u to v where there was an edge v->u in original graph
            for v in rev_adj[u]:
                new_cost = d + 1
                if new_cost < dist[v][1]:
                    dist[v][1] = new_cost
                    heapq.heappush(pq, (new_cost, v, 1))
            
            # Option 2: Reverse all edges (move to state 0)
            new_cost = d + X
            if new_cost < dist[u][0]:
                dist[u][0] = new_cost
                heapq.heappush(pq, (new_cost, u, 0))
    
    # The answer is the minimum of dist[N][0] and dist[N][1]
    ans = min(dist[N][0], dist[N][1])
    print(ans)

if __name__ == "__main__":
    solve()
