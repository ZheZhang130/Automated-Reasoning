import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))
    A = [0] * (N + 1)
    for i in range(1, N + 1):
        A[i] = int(next(iterator))

    MOD = 998244353

    # Compute indegrees
    indeg = [0] * (N + 1)
    for i in range(1, N + 1):
        indeg[A[i]] += 1

    # Topological sort (Kahn's algorithm) to remove tree nodes
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

    # Initialize DP tables: dp[u][t] = number of ways for subtree rooted at u (in reverse graph)
    # when u is assigned value t. Initially, each node has 1 way (itself).
    dp = [[1] * (M + 1) for _ in range(N + 1)]

    # Process in topological order (children processed before parents)
    for u in topo_order:
        v = A[u]
        # For each possible value t for v, the number of ways for u's subtree is dp[u][t]
        # But u can take any value from 1 to t, so we sum dp[u][s] for s from 1 to t
        for t in range(1, M + 1):
            sum_u = sum(dp[u][s] for s in range(1, t + 1)) % MOD
            dp[v][t] = (dp[v][t] * sum_u) % MOD

    # Identify cycles
    visited = [False] * (N + 1)
    cycles = []
    
    for i in range(1, N + 1):
        if not visited[i]:
            curr = i
            path = []
            while not visited[curr]:
                visited[curr] = True
                path.append(curr)
                curr = A[curr]
            
            # Now curr is the first node that was already visited.
            # Check if curr is in the current path (cycle)
            if curr in path:
                cycle_start_index = path.index(curr)
                cycle_nodes = path[cycle_start_index:]
                cycles.append(cycle_nodes)

    # Now compute the answer
    ans = 1
    for cycle in cycles:
        # For each cycle, compute sum_{t=1}^M product_{u in cycle} dp[u][t]
        cycle_sum = 0
        for t in range(1, M + 1):
            prod = 1
            for u in cycle:
                prod = (prod * dp[u][t]) % MOD
            cycle_sum = (cycle_sum + prod) % MOD
        ans = (ans * cycle_sum) % MOD

    print(ans)

solve()
