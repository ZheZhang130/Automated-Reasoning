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
        indeg[i] += 1  # Edge i -> A[i]

    # Topological sort (remove indegree 0 nodes)
    queue = [i for i in range(1, N + 1) if indeg[i] == 0]
    topo_order = []
    while queue:
        u = queue.pop(0)
        topo_order.append(u)
        v = A[u]
        indeg[v] -= 1
        if indeg[v] == 0:
            queue.append(v)

    # Initialize D[u][t] = 1 for all u, t
    D = [[1] * (M + 1) for _ in range(N + 1)]

    # Process vertices in topological order
    for u in topo_order:
        v = A[u]
        # For each t from 1 to M, D[v][t] *= t (number of choices for x_u given x_v = t)
        for t in range(1, M + 1):
            D[v][t] = (D[v][t] * t) % MOD

    # Now, find cycles
    # Vertices not in topo_order are part of cycles
    in_topo = [False] * (N + 1)
    for u in topo_order:
        in_topo[u] = True

    visited = [False] * (N + 1)
    total_ans = 1

    for i in range(1, N + 1):
        if not in_topo[i] and not visited[i]:
            # Found a cycle
            cycle = []
            curr = i
            while not visited[curr]:
                visited[curr] = True
                cycle.append(curr)
                curr = A[curr]
            
            # Compute product of D[u][t] for all u in cycle for each t
            cycle_prod = [1] * (M + 1)
            for u in cycle:
                for t in range(1, M + 1):
                    cycle_prod[t] = (cycle_prod[t] * D[u][t]) % MOD
            
            # Sum over t
            cycle_sum = 0
            for t in range(1, M + 1):
                cycle_sum = (cycle_sum + cycle_prod[t]) % MOD
            
            total_ans = (total_ans * cycle_sum) % MOD

    print(total_ans)

if __name__ == "__main__":
    solve()
