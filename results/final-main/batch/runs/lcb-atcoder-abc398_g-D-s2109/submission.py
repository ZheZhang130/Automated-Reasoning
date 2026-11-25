import sys

def solve():
    input_data = sys.stdin.read
    data = input_data().split()
    it = iter(data)
    
    try:
        N = int(next(it))
        M = int(next(it))
    except StopIteration:
        return

    # Build adjacency list
    adj = [[] for _ in range(N + 1)]
    for _ in range(M):
        u = int(next(it))
        v = int(next(it))
        adj[u].append(v)
        adj[v].append(u)

    # Check bipartiteness (no odd cycle)
    color = [-1] * (N + 1)
    for i in range(1, N + 1):
        if color[i] == -1:
            color[i] = 0
            stack = [i]
            while stack:
                u = stack.pop()
                for v in adj[u]:
                    if color[v] == -1:
                        color[v] = 1 - color[u]
                        stack.append(v)
                    elif color[v] == color[u]:
                        # Should not happen per constraints
                        pass

    # Count components and their sizes
    comp_id = [-1] * (N + 1)
    comp_size = []
    comp_edges = []
    comp_idx = 0
    for i in range(1, N + 1):
        if comp_id[i] == -1:
            comp_id[i] = comp_idx
            comp_size.append(0)
            comp_edges.append(0)
            stack = [i]
            while stack:
                u = stack.pop()
                comp_size[comp_idx] += 1
                for v in adj[u]:
                    if comp_id[v] == -1:
                        comp_id[v] = comp_idx
                        stack.append(v)
            # Now count edges for this component
            for u in range(1, N + 1):
                if comp_id[u] == comp_idx:
                    for v in adj[u]:
                        if comp_id[v] == comp_idx:
                            comp_edges[comp_idx] += 1
            comp_edges[comp_idx] //= 2
            comp_idx += 1

    total_moves = 0
    for i in range(len(comp_size)):
        max_edges = (comp_size[i] * comp_size[i]) // 4
        total_moves += (max_edges - comp_edges[i])

    if total_moves % 2 == 1:
        print("Aoki")
    else:
        print("Takahashi")

solve()
