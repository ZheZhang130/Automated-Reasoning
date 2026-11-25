import sys
from heapq import heappop, heappush


def main():
    read = sys.stdin.buffer.readline
    n, m, x = map(int, read().split())
    graph = [[] for _ in range(2 * n)]
    for _ in range(m):
        u, v = map(int, read().split())
        u = 2 * (u - 1)
        v = 2 * (v - 1)
        graph[u].append(v)
        graph[v ^ 1].append(u ^ 1)

    # A state's low bit records whether the edges are reversed.
    dist = [10**18] * (2 * n)
    dist[0] = 0
    heap = [(0, 0)]
    goal = 2 * (n - 1)
    while heap:
        cost, state = heappop(heap)
        if cost != dist[state]:
            continue
        if state >= goal:
            print(cost)
            return

        flipped = state ^ 1
        flip_cost = cost + x
        if flip_cost < dist[flipped]:
            dist[flipped] = flip_cost
            heappush(heap, (flip_cost, flipped))

        move_cost = cost + 1
        for neighbor in graph[state]:
            if move_cost < dist[neighbor]:
                dist[neighbor] = move_cost
                heappush(heap, (move_cost, neighbor))


if __name__ == "__main__":
    main()
