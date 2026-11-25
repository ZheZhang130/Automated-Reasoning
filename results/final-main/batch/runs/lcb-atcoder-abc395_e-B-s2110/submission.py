import sys
from heapq import heappop, heappush


def main():
    readline = sys.stdin.buffer.readline
    n, m, x = map(int, readline().split())
    # State 2*v has the original orientation, and 2*v+1 the reverse.
    adj = [[] for _ in range(2 * n)]
    for _ in range(m):
        u, v = map(int, readline().split())
        u = 2 * (u - 1)
        v = 2 * (v - 1)
        adj[u].append(v)
        adj[v + 1].append(u + 1)

    target = 2 * (n - 1)
    dist = [10**18] * (2 * n)
    dist[0] = 0
    heap = [(0, 0)]
    while heap:
        cost, state = heappop(heap)
        if cost != dist[state]:
            continue
        if state >= target:
            print(cost)
            return

        next_cost = cost + 1
        for nxt in adj[state]:
            if next_cost < dist[nxt]:
                dist[nxt] = next_cost
                heappush(heap, (next_cost, nxt))

        nxt = state ^ 1
        next_cost = cost + x
        if next_cost < dist[nxt]:
            dist[nxt] = next_cost
            heappush(heap, (next_cost, nxt))


if __name__ == "__main__":
    main()
