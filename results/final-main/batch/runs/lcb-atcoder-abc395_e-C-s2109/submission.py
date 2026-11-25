import sys
import heapq

def solve():
    # Read all input from stdin
    input_data = sys.stdin.read().split()
    if not input_data:
        return

    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))
    X = int(next(iterator))

    # Build adjacency lists for both orientations
    # adj[u][0] -> list of v such that u->v exists (original orientation)
    # adj[u][1] -> list of v such that u->v exists in reversed orientation (which means v->u in original)
    # We need N+1 lists for each orientation since vertices are 1-indexed
    adj = [[], []]
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        # Original orientation: u -> v
        adj[0][u].append(v)
        # Reversed orientation: if we reverse edges, the edge becomes v -> u
        # So in the reversed orientation, from v we can go to u
        adj[1][v].append(u)

    # Dijkstra's algorithm
    # State: (vertex, orientation) where orientation is 0 (original) or 1 (reversed)
    # Distance array: dist[vertex][orientation]
    dist = [[float('inf')] * 2 for _ in range(N + 1)]
    dist[1][0] = 0

    # Min-heap: (cost, vertex, orientation)
    heap = [(0, 1, 0)]

    while heap:
        cost, u, orientation = heapq.heappop(heap)

        # If we found a shorter path to this state already, skip
        if cost > dist[u][orientation]:
            continue

        # If we reached vertex N, we can stop (since Dijkstra guarantees shortest path)
        if u == N:
            print(cost)
            return

        # Option 1: Move along an edge in the current orientation
        # Cost: 1
        next_orientation = orientation
        for v in adj[orientation][u]:
            new_cost = cost + 1
            if new_cost < dist[v][next_orientation]:
                dist[v][next_orientation] = new_cost
                heapq.heappush(heap, (new_cost, v, next_orientation))

        # Option 2: Reverse all edges
        # Cost: X
        new_orientation = 1 - orientation
        new_cost = cost + X
        if new_cost < dist[u][new_orientation]:
            dist[u][new_orientation] = new_cost
            heapq.heappush(heap, (new_cost, u, new_orientation))

    # If we exit the loop without returning, it means we couldn't reach N (should not happen per problem guarantee)
    # But just in case, we can check the minimum of the two orientations at N
    ans = min(dist[N][0], dist[N][1])
    print(ans)

if __name__ == "__main__":
    solve()
