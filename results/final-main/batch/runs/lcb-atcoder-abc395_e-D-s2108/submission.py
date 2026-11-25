import sys
from collections import deque

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
    
    # BFS on state (vertex, flipped)
    # flipped = 0 means edges are in original direction
    # flipped = 1 means edges are reversed
    # We want shortest path from (1, 0) to any state where vertex == N
    
    # However, note: when we reverse edges, we stay at the same vertex.
    # So from (u, 0) we can go to (u, 1) with cost X.
    # From (u, 0) we can go to (v, 0) for each v in adj[u] with cost 1.
    # From (u, 1) we can go to (u, 0) with cost X.
    # From (u, 1) we can go to (v, 1) for each v in rev_adj[u] with cost 1.
    
    # We'll use Dijkstra since edge weights are 1 and X (X can be large).
    # But note: we have only two states per vertex, so we can use 0-1 BFS if we normalize,
    # but since X can be large, we use Dijkstra with a priority queue.
    
    import heapq
    
    # dist[u][flipped] = minimum cost to reach vertex u with flipped state
    dist = [[float('inf')] * 2 for _ in range(N + 1)]
    dist[1][0] = 0
    
    pq = [(0, 1, 0)]  # (cost, u, flipped)
    
    while pq:
        d, u, flipped = heapq.heappop(pq)
        
        if d > dist[u][flipped]:
            continue
        
        if u == N:
            print(d)
            return
        
        # Option 1: Reverse edges (stay at u, flip state)
        new_flipped = 1 - flipped
        new_cost = d + X
        if new_cost < dist[u][new_flipped]:
            dist[u][new_flipped] = new_cost
            heapq.heappush(pq, (new_cost, u, new_flipped))
        
        # Option 2: Move along edges
        if flipped == 0:
            # Original direction: from u to v in adj[u]
            for v in adj[u]:
                new_cost = d + 1
                if new_cost < dist[v][0]:
                    dist[v][0] = new_cost
                    heapq.heappush(pq, (new_cost, v, 0))
        else:
            # Reversed direction: from u to v in rev_adj[u]
            for v in rev_adj[u]:
                new_cost = d + 1
                if new_cost < dist[v][1]:
                    dist[v][1] = new_cost
                    heapq.heappush(pq, (new_cost, v, 1))
    
    # If we exit the loop without reaching N, it means it's impossible, but the problem guarantees reachability.
    # So we should have returned already.
    # However, if for some reason we didn't, we can check the final answer.
    ans = min(dist[N][0], dist[N][1])
    print(ans)

if __name__ == "__main__":
    solve()
