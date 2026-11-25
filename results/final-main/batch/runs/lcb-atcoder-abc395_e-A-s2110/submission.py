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
    
    # dist[v][0] = minimum cost to reach vertex v with normal edge direction
    # dist[v][1] = minimum cost to reach vertex v with reversed edge direction
    INF = float('inf')
    dist = [[INF] * 2 for _ in range(N + 1)]
    dist[1][0] = 0
    
    # Priority queue: (cost, vertex, direction)
    pq = [(0, 1, 0)]
    
    while pq:
        d, u, direction = heapq.heappop(pq)
        
        if d > dist[u][direction]:
            continue
        
        if direction == 0:
            # Normal direction: can move along forward edges
            for v in adj[u]:
                new_cost = d + 1
                if new_cost < dist[v][0]:
                    dist[v][0] = new_cost
                    heapq.heappush(pq, (new_cost, v, 0))
            
            # Can reverse edges
            new_cost = d + X
            if new_cost < dist[u][1]:
                dist[u][1] = new_cost
                heapq.heappush(pq, (new_cost, u, 1))
        else:
            # Reversed direction: can move along backward edges (edges that go to u in original graph)
            for v in rev_adj[u]:
                new_cost = d + 1
                if new_cost < dist[v][1]:
                    dist[v][1] = new_cost
                    heapq.heappush(pq, (new_cost, v, 1))
            
            # Can reverse edges back
            new_cost = d + X
            if new_cost < dist[u][0]:
                dist[u][0] = new_cost
                heapq.heappush(pq, (new_cost, u, 0))
    
    # The answer is min(dist[N][0], dist[N][1])
    ans = min(dist[N][0], dist[N][1])
    print(ans)

if __name__ == "__main__":
    solve()
