import sys


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(data)
    m = next(data)

    # Terminal graphs are complete bipartite (including the one-vertex case).
    # For odd n their edge counts are always even.
    if n % 2:
        print("Aoki" if m % 2 else "Takahashi")
        return

    graph = [[] for _ in range(n)]
    for _ in range(m):
        u = next(data) - 1
        v = next(data) - 1
        graph[u].append(v)
        graph[v].append(u)

    color = [-1] * n
    singletons = 0
    odd_nontrivial = 0
    even_side_parity = 0
    for root in range(n):
        if not graph[root]:
            singletons += 1
            continue
        if color[root] != -1:
            continue
        color[root] = 0
        stack = [root]
        size = 0
        ones = 0
        while stack:
            v = stack.pop()
            size += 1
            ones += color[v]
            for u in graph[v]:
                if color[u] == -1:
                    color[u] = color[v] ^ 1
                    stack.append(u)
        if size % 2:
            odd_nontrivial += 1
        else:
            even_side_parity ^= ones % 2

    if odd_nontrivial == 0:
        # Joining two singletons flips both m and even_side_parity, and
        # decreases singletons // 2 by one. Other moves that stay in this
        # case flip only m in the expression below.
        first_wins = (m ^ even_side_parity ^ (singletons // 2)) & 1
    elif odd_nontrivial <= 2:
        # Merge the lone odd component with a singleton, or merge the
        # two odd components. Both orientations are possible and give
        # opposite side parities for the resulting even component.
        first_wins = True
    else:
        # One move cannot take this case directly to zero odd nontrivial
        # components. With odd m we can stay in this case: merge two
        # nontrivial odd components if there are at least five, merge
        # two singletons, or merge an even component with an odd one.
        # If none applies, all components have even internal capacities,
        # so odd m guarantees a missing internal edge.
        first_wins = m % 2

    print("Aoki" if first_wins else "Takahashi")


if __name__ == "__main__":
    main()
