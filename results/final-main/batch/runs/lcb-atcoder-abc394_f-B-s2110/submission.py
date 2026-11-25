import sys


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(data)
    graph = [[] for _ in range(n)]
    for a, b in zip(data, data):
        a -= 1
        b -= 1
        graph[a].append(b)
        graph[b].append(a)

    parent = [-1] * n
    order = [0]
    for u in order:
        for v in graph[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)

    # With an edge to its parent, a vertex uses either zero or three children.
    branch = [1] * n
    answer = -1
    for u in reversed(order):
        first = second = third = fourth = 0
        for v in graph[u]:
            if v == parent[u]:
                continue
            x = branch[v]
            if x >= first:
                first, second, third, fourth = x, first, second, third
            elif x >= second:
                second, third, fourth = x, second, third
            elif x >= third:
                third, fourth = x, third
            elif x > fourth:
                fourth = x

        if third:
            branch[u] = 1 + first + second + third
            if parent[u] != -1:
                # The parent is the topmost vertex and is a leaf.
                answer = max(answer, branch[u] + 1)
        if fourth:
            # The topmost vertex is internal and uses four children.
            answer = max(answer, 1 + first + second + third + fourth)

    print(answer)


if __name__ == "__main__":
    main()
