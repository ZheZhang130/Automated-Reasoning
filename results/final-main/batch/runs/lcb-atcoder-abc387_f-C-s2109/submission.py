import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))
    A = [0] + [int(next(iterator)) for _ in range(N)]  # 1-indexed
    
    MOD = 998244353
    
    # Compute indegrees
    indeg = [0] * (N + 1)
    for i in range(1, N + 1):
        indeg[i] += 1
    
    # Topological sort to remove tree nodes
    queue = [i for i in range(1, N + 1) if indeg[i] == 0]
    topo_order = []
    
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        topo_order.append(u)
        v = A[u]
        indeg[v] -= 1
        if indeg[v] == 0:
            queue.append(v)
    
    # D[u][t] will store the number of ways for the subtree rooted at u (in the functional graph sense, 
    # where edges go u -> A[u], so u is a child of A[u]) given that u has value t.
    # Initially, for a leaf (no children in the tree sense), D[u][t] = 1.
    # When we remove u, we update D[A[u]][t] by multiplying with sum_{s=1}^t D[u][s].
    
    # Initialize D
    D = [[1] * (M + 1) for _ in range(N + 1)]
    
    # Process in topo_order (leaves first)
    for u in topo_order:
        v = A[u]
        # Compute prefix sums of D[u]
        prefix_sum = 0
        for t in range(1, M + 1):
            prefix_sum = (prefix_sum + D[u][t]) % MOD
            D[v][t] = (D[v][t] * prefix_sum) % MOD
            
    # Now, the remaining nodes are those in cycles.
    # We need to find cycles and compute the answer.
    visited = [False] * (N + 1)
    ans = 1
    
    for i in range(1, N + 1):
        if not visited[i] and indeg[i] > 0:
            # Found a cycle
            cycle_nodes = []
            curr = i
            while not visited[curr]:
                visited[curr] = True
                cycle_nodes.append(curr)
                curr = A[curr]
            
            # Compute product for this cycle
            cycle_prod = [0] * (M + 1)
            for t in range(1, M + 1):
                prod = 1
                for u in cycle_nodes:
                    prod = (prod * D[u][t]) % MOD
                cycle_prod[t] = prod
            
            cycle_sum = sum(cycle_prod[1:]) % MOD
            ans = (ans * cycle_sum) % MOD
            
    print(ans)

if __name__ == '__main__':
    solve()
