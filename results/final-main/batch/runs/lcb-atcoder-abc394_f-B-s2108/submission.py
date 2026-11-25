import sys


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(data)
    graph = [[] for _ in range(n)]
    for _ in range(n - 1):
        u = next(data) - 1
        v = next(data) - 1
        graph[u].append(v)
        graph[v].append(u)

    parent = [-1] * n
    order = [0]
    for u in order:
        for v in graph[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)

    # branch[u] assumes u is attached to its parent.
    branch = [1] * n
    answer = -1
    for u in reversed(order):
        p = parent[u]
        if len(graph[u]) - (p != -1) < 3:
            continue

        first = second = third = fourth = 0
        for v in graph[u]:
            if v == p:
                continue
            value = branch[v]
            if value >= first:
                first, second, third, fourth = value, first, second, third
            elif value >= second:
                second, third, fourth = value, second, third
            elif value >= third:
                third, fourth = value, third
            elif value > fourth:
                fourth = value

        branch[u] = 1 + first + second + third
        if p != -1:
            # The parent is the highest vertex and is a leaf.
            answer = max(answer, branch[u] + 1)
        if fourth:
            # The highest vertex is u itself and has four children.
            answer = max(answer, branch[u] + fourth)

    print(answer)


if __name__ == "__main__":
    main()
