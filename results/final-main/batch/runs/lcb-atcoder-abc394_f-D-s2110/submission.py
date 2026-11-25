import sys
sys.setrecursionlimit(300000)

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    N = int(next(iterator))
    adj = [[] for _ in range(N + 1)]
    for _ in range(N - 1):
        u = int(next(iterator))
        v = int(next(iterator))
        adj[u].append(v)
        adj[v].append(u)

    # dp[u] = max vertices in an alkane subgraph within the subtree of u
    # that includes u and where u has degree 4 in the subgraph.
    # If u cannot be degree 4, dp[u] = -1.
    # We also need to know if u can be degree 1 (leaf) in a valid alkane.
    # Actually, the structure is: one central "core" of degree-4 nodes, and leaves.
    # But the definition says EVERY vertex has degree 1 or 4.
    # So the alkane is a tree where some nodes are degree 4 and some are degree 1.
    # This is a specific type of tree.
    # Key insight: In such a tree, if we remove all degree-4 nodes, we get isolated leaves.
    # Actually, let's think recursively.
    # For a node u to be part of an alkane:
    # Option 1: u is a leaf (degree 1). Then we need to connect u to one neighbor v,
    #          and v must be part of an alkane where v has degree 4 (or v is also a leaf? No, at least one degree 4).
    # Option 2: u is degree 4. Then u must have 4 neighbors, each of which is either a leaf or part of an alkane branch.
    # But wait, if u is degree 4, all 4 neighbors must be leaves? No.
    # Example: A central node connected to 4 branches. Each branch is a path ending in a leaf.
    # But the condition is EVERY vertex has degree 1 or 4.
    # So if u is degree 4, its neighbors must have degree 1 (leaves) or degree 4.
    # If a neighbor has degree 4, then it must have 4 neighbors.
    # This suggests the structure is a "star-like" structure where degree-4 nodes form a connected component?
    # Actually, consider the degrees. Sum of degrees = 2*(V-1).
    # Let k be number of degree-4 nodes, and (V-k) be number of degree-1 nodes.
    # 4k + 1*(V-k) = 2V - 2  =>  4k + V - k = 2V - 2  =>  3k = V - 2  =>  V = 3k + 2.
    # So the number of vertices is determined by the number of degree-4 nodes.
    # Also, the graph must be connected (tree).
    # Structure: The degree-4 nodes must form a connected subgraph? Not necessarily, but they must be connected via paths of degree-1 nodes?
    # No, if a degree-1 node is between two degree-4 nodes, its degree would be 2, which is not allowed.
    # Therefore, degree-1 nodes can only be leaves attached to degree-4 nodes.
    # This means the degree-4 nodes must form a connected component (a tree themselves), and all other nodes are leaves attached to this component.
    # But wait, if two degree-4 nodes are connected, the edge between them counts for both.
    # So the "core" is a tree of degree-4 nodes. Let the core have C vertices.
    # Each vertex in the core has degree 4 in the whole alkane.
    # In the core tree, a vertex has some degree d_core (1 <= d_core <= 3, since it's a tree).
    # The remaining 4 - d_core edges must go to leaves (degree-1 nodes).
    # So each core vertex can have at most 4 leaves attached.
    # Total vertices V = C + (sum over core vertices of (4 - d_core)).
    # Sum of d_core over core vertices = 2*(C-1) (since core is a tree).
    # Total leaves = sum(4 - d_core) = 4C - 2(C-1) = 2C + 2.
    # Total V = C + 2C + 2 = 3C + 2. Matches the formula.
    # So the problem reduces to: Find a connected subgraph of the original tree consisting of C vertices
    # such that each vertex in the subgraph has degree <= 4 in the original tree?
    # No. The degree in the alkane subgraph must be 4.
    # In the alkane subgraph, the core vertices have degree d_core (within core) + leaves = 4.
    # So d_core + leaves = 4.
    # This means in the original tree, the degree of a core vertex must be at least d_core.
    # But we can choose which neighbors are leaves and which are core neighbors.
    # However, the core must be connected.
    # And for a vertex to be in the core, its degree in the original tree must be at least 1 (to connect to core) and at most 4?
    # Actually, if a vertex is in the core, its degree in the alkane is 4.
    # Its neighbors in the alkane are either core neighbors or leaves.
    # So in the original tree, the vertex must have degree at least 1 (if C>1) or 0 (if C=1, but C=1 => V=5, degree 4, so original degree must be >=4).
    # Wait, if C=1, V=5. The single core vertex has 4 leaves. So original degree must be >=4.
    # If C=2, V=8. Two core vertices connected. Each has 3 leaves. Total leaves 6.
    # In original tree, each core vertex must have degree at least 1 (for the edge between them) + 3 leaves = 4.
    # So each core vertex must have original degree >= 4?
    # Not necessarily. The leaves in the alkane must be neighbors in the original tree.
    # So yes, for a vertex to be in the core, it must have at least (4 - d_core) neighbors that we designate as leaves.
    # And d_core neighbors that are in the core.
    # So the original degree must be at least 4.
    # Wait, what if the original degree is 3? Then it cannot be in the core because max degree in alkane is 4, and we need 4 neighbors.
    # So every vertex in the core must have original degree >= 4.
    # And vertices with original degree < 4 cannot be in the core. They can only be leaves?
    # But leaves in the alkane must be connected to the core.
    # So if a vertex has original degree < 4, it cannot be in the core. Can it be a leaf?
    # A leaf in the alkane has degree 1. It is connected to one core vertex.
    # So if a vertex has original degree < 4, it cannot be in the core. It can be a leaf only if it is connected to a core vertex.
    # But if it is a leaf in the alkane, it has degree 1. So it uses 1 edge.
    # The problem: We need to select a connected subgraph (the core) of vertices with original degree >= 4.
    # Then, for each vertex in the core, we can attach up to (4 - d_core_in_core) leaves from its neighbors.
    # But the leaves must be vertices from the original tree.
    # And we want to maximize V = 3C + 2.
    # So we want to maximize C, the size of the core.
    # The core must be a connected subgraph of the original tree, consisting only of vertices with original degree >= 4.
    # Is that sufficient?
    # For each vertex u in the core, let d_orig(u) be its degree in the original tree.
    # Let d_core(u) be its degree within the core subgraph.
    # We need d_core(u) + (number of leaves attached to u) = 4.
    # So we need d_orig(u) >= d_core(u) + (4 - d_core(u)) = 4.
    # So yes, every vertex in the core must have original degree >= 4.
    # And we can attach leaves as long as there are enough neighbors.
    # Specifically, we need d_orig(u) >= 4.
    # And the number of leaves we can attach is min(4 - d_core(u), d_orig(u) - d_core(u)).
    # But since d_orig(u) >= 4, and d_core(u) >= 1 (if C>1), then d_orig(u) - d_core(u) >= 4 - d_core(u) is not guaranteed.
    # Wait, d_orig(u) is the total degree in original tree.
    # d_core(u) is the number of neighbors in the core.
    # The remaining neighbors can be used as leaves.
    # We need exactly 4 - d_core(u) leaves.
    # So we need d_orig(u) - d_core(u) >= 4 - d_core(u)  => d_orig(u) >= 4.
    # So the condition is simply: core vertices must have original degree >= 4.
    # And the core must be connected.
    # Then the total vertices = 3*C + 2.
    # But wait, we also need at least one degree-4 vertex, which is satisfied if C >= 1.
    # However, we must also ensure that we can actually form the alkane.
    # The leaves must be distinct vertices.
    # For a vertex u in the core, we need 4 - d_core(u) leaves.
    # The available neighbors are d_orig(u) - d_core(u).
    # We need 4 - d_core(u) <= d_orig(u) - d_core(u)  => 4 <= d_orig(u).
    # So as long as d_orig(u) >= 4, we can pick the required leaves.
    # But what if d_orig(u) > 4? We can only use 4 - d_core(u) leaves. The rest are unused.
    # So the strategy:
    # 1. Identify all vertices with original degree >= 4.
    # 2. Find the largest connected component (subgraph) within these vertices.
    # 3. Let C be the size of this component.
    # 4. The answer is 3*C + 2, provided C >= 1.
    # 5. If no such vertex exists, answer is -1.
    # But wait, is it possible that the largest connected component of degree>=4 vertices is not the optimal core?
    # Maybe a smaller connected component allows more leaves?
    # No, V = 3C + 2. So maximizing C maximizes V.
    # So we just need the largest connected component of vertices with degree >= 4.
    # Let's verify with Sample 1.
    # N=9. Edges: (1,2), (2,3), (3,4), (4,5), (2,6), (2,7), (3,8), (3,9).
    # Degrees:
    # 1: 1 (neighbor 2)
    # 2: 4 (neighbors 1,3,6,7) -> >=4
    # 3: 4 (neighbors 2,4,8,9) -> >=4
    # 4: 2 (neighbors 3,5)
    # 5: 1 (neighbor 4)
    # 6: 1 (neighbor 2)
    # 7: 1 (neighbor 2)
    # 8: 1 (neighbor 3)
    # 9: 1 (neighbor 3)
    # Vertices with degree >=4: {2, 3}.
    # Are 2 and 3 connected? Yes, edge (2,3).
    # So core = {2, 3}, C=2.
    # Answer = 3*2 + 2 = 8. Matches sample output.
    # Sample 2:
    # 7 vertices. Star-like?
    # Edges: (1,2), (1,3), (2,4), (2,5), (3,6), (3,7).
    # Degrees:
    # 1: 2 (2,3)
    # 2: 3 (1,4,5)
    # 3: 3 (1,6,7)
    # 4: 1
    # 5: 1
    # 6: 1
    # 7: 1
    # No vertex has degree >=4. So C=0. Answer -1. Matches.
    # Sample 3:
    # 15 vertices.
    # We need to compute degrees and find largest connected component of degree>=4.
    # Let's code this.

    # Compute degrees
    deg = [0] * (N + 1)
    for u in adj:
        for v in u:
            deg[v] += 1
    # Actually, adj is list of lists. Let's recompute degrees properly.
    deg = [0] * (N + 1)
    for u in range(1, N + 1):
        deg[u] = len(adj[u])
    
    # Find vertices with deg >= 4
    candidates = [i for i in range(1, N + 1) if deg[i] >= 4]
    
    if not candidates:
        print(-1)
        return
    
    # Build graph of candidates
    # We can use BFS/DFS to find connected components
    visited = [False] * (N + 1)
    max_c = 0
    
    for start in candidates:
        if visited[start]:
            continue
        # BFS
        stack = [start]
        visited[start] = True
        count = 0
        while stack:
            u = stack.pop()
            count += 1
            for v in adj[u]:
                if deg[v] >= 4 and not visited[v]:
                    visited[v] = True
                    stack.append(v)
        if count > max_c:
            max_c = count
    
    if max_c == 0:
        print(-1)
    else:
        print(3 * max_c + 2)

solve()
