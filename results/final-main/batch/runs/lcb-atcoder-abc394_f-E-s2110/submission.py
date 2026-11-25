import sys
from collections import deque

def solve():
    input = sys.stdin.read
    data = input().split()
    it = iter(data)
    N = int(next(it))
    adj = [[] for _ in range(N + 1)]
    for _ in range(N - 1):
        u = int(next(it))
        v = int(next(it))
        adj[u].append(v)
        adj[v].append(u)

    # We need to find a subgraph that is a tree where every vertex has degree 1 or 4,
    # and at least one vertex has degree 4.
    # This means the subgraph is a "4-regular tree with some leaves".
    # In such a subgraph, internal nodes have degree 4, leaves have degree 1.
    # Let k be the number of internal nodes (degree 4).
    # Let l be the number of leaves (degree 1).
    # Total vertices = k + l.
    # Sum of degrees = 4*k + l = 2*(k+l-1)  (since it's a tree with k+l vertices)
    # 4k + l = 2k + 2l - 2
    # 2k = l - 2  => l = 2k + 2
    # Total vertices = k + (2k + 2) = 3k + 2.
    # So we need to find a connected subgraph with k internal nodes (degree 4) and 2k+2 leaves (degree 1).
    # The internal nodes must form a connected structure where each has 4 neighbors in the subgraph.
    # Actually, the internal nodes themselves don't have to be connected to each other directly,
    # but the whole subgraph must be connected.
    # However, if we pick a set of internal nodes, each must have exactly 4 neighbors in the subgraph.
    # Since the subgraph is a tree, the internal nodes must be connected via paths that go through leaves?
    # No, that doesn't make sense. In a tree, if you have internal nodes, they must be connected.
    # But if an internal node is connected to another internal node, that edge counts for both.
    # Let's think differently.
    # We are looking for a subtree where some nodes have degree 4 and others degree 1.
    # Let S be the set of vertices in the subgraph.
    # For each v in S, deg_S(v) is 1 or 4.
    # And there is at least one v with deg_S(v) = 4.
    # Let I be the set of internal nodes (deg 4), L be the set of leaves (deg 1).
    # |I| = k, |L| = l.
    # Sum of degrees = 4k + l = 2(|I| + |L| - 1) = 2(k+l-1).
    # 4k + l = 2k + 2l - 2 => 2k = l - 2 => l = 2k + 2.
    # Total vertices = k + l = 3k + 2.
    # So we need to find a connected subgraph with k internal nodes such that each internal node
    # has exactly 4 neighbors in the subgraph, and the remaining neighbors (to make the subgraph connected)
    # are leaves.
    # Actually, the internal nodes must form a connected component? Not necessarily directly connected,
    # but the whole subgraph is connected.
    # However, if an internal node is connected to a leaf, that leaf has degree 1.
    # If two internal nodes are connected, that edge contributes to both.
    # Let's consider the structure: the internal nodes must be connected to each other?
    # Suppose we have a set of internal nodes I. Each v in I must have 4 neighbors in S.
    # Some neighbors are in I, some are in L.
    # Let d_I(v) be the number of neighbors of v in I, and d_L(v) be the number of neighbors in L.
    # d_I(v) + d_L(v) = 4.
    # Also, the subgraph induced by I must be connected? Not necessarily, but the whole S must be connected.
    # However, if I is not connected, then there must be paths between components of I going through L.
    # But L nodes have degree 1, so they can only be endpoints. They cannot be part of a path between two I nodes.
    # Therefore, the subgraph induced by I must be connected.
    # So I must induce a connected subgraph (a tree itself).
    # And each v in I has d_I(v) neighbors in I, and 4 - d_I(v) neighbors in L.
    # The total number of leaves l = sum_{v in I} (4 - d_I(v)).
    # But we also know l = 2k + 2.
    # So sum_{v in I} (4 - d_I(v)) = 2k + 2.
    # 4k - sum_{v in I} d_I(v) = 2k + 2.
    # sum_{v in I} d_I(v) = 2k - 2.
    # But sum_{v in I} d_I(v) = 2 * |E(I)|, where E(I) is the set of edges within I.
    # Since I induces a tree, |E(I)| = k - 1.
    # So sum_{v in I} d_I(v) = 2(k - 1) = 2k - 2.
    # This matches! So the condition is automatically satisfied if I induces a tree.
    # Therefore, we just need to find a connected subgraph I such that for every v in I,
    # the degree of v in the original tree T is at least 4.
    # Because if deg_T(v) >= 4, we can choose 4 neighbors for v in S.
    # But we need to choose exactly 4 neighbors in S, and some of them must be in I and some in L.
    # Specifically, if v has d_I(v) neighbors in I, then it must have 4 - d_I(v) neighbors in L.
    # So we need deg_T(v) >= 4 - d_I(v) + d_I(v) = 4? No.
    # The neighbors in L must be actual neighbors in T.
    # So for each v in I, we need deg_T(v) >= 4.
    # And we need to be able to select exactly 4 neighbors for v in S.
    # The neighbors in I are fixed (they are the edges within I).
    # The neighbors in L must be chosen from the remaining neighbors of v in T.
    # So we need deg_T(v) - d_I(v) >= 4 - d_I(v) => deg_T(v) >= 4.
    # So the condition is: I is a connected subgraph (induced by edges in T) such that every v in I has deg_T(v) >= 4.
    # And then we can always complete it to a valid alkane by adding leaves.
    # The number of vertices would be 3k + 2, where k = |I|.
    # So we need to find the largest connected subgraph I such that every node in I has deg_T(v) >= 4.
    # This is equivalent to finding the largest connected component in the subgraph of T induced by vertices with deg_T(v) >= 4.
    # Let V4 = {v | deg_T(v) >= 4}.
    # Find the largest connected component in the subgraph induced by V4.
    # Let its size be k.
    # Then the answer is 3k + 2.
    # But wait, we need at least one vertex of degree 4. So k >= 1.
    # If there is no vertex with deg >= 4, then answer is -1.
    # Also, we need to check if the component is non-empty.
    # So algorithm:
    # 1. Compute degrees of all vertices in T.
    # 2. Identify vertices with deg >= 4.
    # 3. Build a subgraph of T containing only these vertices and edges between them.
    # 4. Find the largest connected component in this subgraph.
    # 5. Let k be the size of the largest component.
    # 6. If k == 0, output -1.
    # 7. Else, output 3*k + 2.

    deg = [0] * (N + 1)
    for u in range(1, N + 1):
        deg[u] = len(adj[u])

    V4 = [i for i in range(1, N + 1) if deg[i] >= 4]
    if not V4:
        print(-1)
        return

    # Build adjacency for V4 subgraph
    adj_v4 = {v: [] for v in V4}
    for u in V4:
        for v in adj[u]:
            if v in V4:
                adj_v4[u].append(v)

    visited = set()
    max_k = 0
    for start in V4:
        if start not in visited:
            stack = [start]
            visited.add(start)
            component = []
            while stack:
                u = stack.pop()
                component.append(u)
                for v in adj_v4[u]:
                    if v not in visited:
                        visited.add(v)
                        stack.append(v)
            k = len(component)
            if k > max_k:
                max_k = k

    if max_k == 0:
        print(-1)
    else:
        print(3 * max_k + 2)

solve()
