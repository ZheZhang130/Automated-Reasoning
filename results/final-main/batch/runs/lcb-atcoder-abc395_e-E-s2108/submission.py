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
    
    # dist[v][0] = minimum cost to reach vertex v in original orientation
    # dist[v][1] = minimum cost to reach vertex v in reversed orientation
    INF = float('inf')
    dist = [[INF, INF] for _ in range(N + 1)]
    dist[1][0] = 0
    
    # Priority queue: (cost, vertex, orientation)
    pq = [(0, 1, 0)]
    
    while pq:
        d, u, orientation = heapq.heappop(pq)
        
        # If we found a shorter path to (u, orientation), skip
        if d > dist[u][orientation]:
            continue
        
        if orientation == 0:
            # Original orientation: can move along adj[u]
            for v in adj[u]:
                new_cost = d + 1
                if new_cost < dist[v][0]:
                    dist[v][0] = new_cost
                    heapq.heappush(pq, (new_cost, v, 0))
            
            # Can flip edges: stay at u, switch to orientation 1, cost X
            new_cost = d + X
            if new_cost < dist[u][1]:
                dist[u][1] = new_cost
                heapq.heappush(pq, (new_cost, u, 1))
        else:
            # Reversed orientation: can move along rev_adj[u]
            for v in rev_adj[u]:
                new_cost = d + 1
                if new_cost < dist[v][1]:
                    dist[v][1] = new_cost
                    heapq.heappush(pq, (new_cost, v, 1))
            
            # Can flip edges: stay at u, switch to orientation 0, cost X
            new_cost = d + X
            if new_cost < dist[u][0]:
                dist[u][0] = new_cost
                heapq.heappush(pq, (new_cost, u, 0))
    
    # Answer is min(dist[N][0], dist[N][1])
    print(min(dist[N][0], dist[N][1]))

if __name__ == "__main__":
    solve()
