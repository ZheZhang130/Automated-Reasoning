import sys
from heapq import heappop, heappush


def main():
    read = sys.stdin.buffer.readline
    n, m, x = map(int, read().split())
    # States 0..n-1 use the original orientation; the next n use the reverse.
    adj = [[] for _ in range(2 * n)]
    for _ in range(m):
        u, v = map(int, read().split())
        u -= 1
        v -= 1
        adj[u].append(v)
        adj[v + n].append(u + n)

    dist = [10**18] * (2 * n)
    dist[0] = 0
    heap = [(0, 0)]
    while heap:
        cost, state = heappop(heap)
        if cost != dist[state]:
            continue
        if state == n - 1 or state == 2 * n - 1:
            print(cost)
            return

        flipped = state + n if state < n else state - n
        flip_cost = cost + x
        if flip_cost < dist[flipped]:
            dist[flipped] = flip_cost
            heappush(heap, (flip_cost, flipped))

        move_cost = cost + 1
        for nxt in adj[state]:
            if move_cost < dist[nxt]:
                dist[nxt] = move_cost
                heappush(heap, (move_cost, nxt))


if __name__ == "__main__":
    main()
