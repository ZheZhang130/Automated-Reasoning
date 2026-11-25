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

    # branch[u] is the best size when the edge to u's parent is used.
    branch = [1] * n
    answer = -1
    for u in reversed(order):
        a = b = c = d = 0
        for v in graph[u]:
            if v == parent[u]:
                continue
            x = branch[v]
            if x >= a:
                a, b, c, d = x, a, b, c
            elif x >= b:
                b, c, d = x, b, c
            elif x >= c:
                c, d = x, c
            elif x > d:
                d = x
        if c:
            branch[u] = 1 + a + b + c
        # The topmost vertex is either internal or a leaf.
        if d:
            answer = max(answer, 1 + a + b + c + d)
        if a > 1:
            answer = max(answer, 1 + a)
    print(answer)


if __name__ == "__main__":
    main()
