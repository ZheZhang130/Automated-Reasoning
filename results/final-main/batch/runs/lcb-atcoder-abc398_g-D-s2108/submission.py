import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    try:
        N = int(next(iterator))
        M = int(next(iterator))
    except StopIteration:
        return

    adj = [[] for _ in range(N + 1)]
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        adj[u].append(v)
        adj[v].append(u)

    visited = [False] * (N + 1)
    comp_id = [-1] * (N + 1)
    comp_count = 0
    comp_nodes0 = []
    comp_nodes1 = []
    comp_edges = []

    for i in range(1, N + 1):
        if not visited[i]:
            comp_count += 1
            comp_nodes0.append(0)
            comp_nodes1.append(0)
            comp_edges.append(0)
            
            color = [-1] * (N + 1)
            color[i] = 0
            comp_id[i] = comp_count
            comp_nodes0[-1] += 1
            queue = [i]
            
            while queue:
                node = queue.pop(0)
                for neighbor in adj[node]:
                    if comp_id[neighbor] == -1:
                        comp_id[neighbor] = comp_count
                        color[neighbor] = 1 - color[node]
                        if color[neighbor] == 0:
                            comp_nodes0[-1] += 1
                        else:
                            comp_nodes1[-1] += 1
                        queue.append(neighbor)
            
            # Count edges in this component
            edge_count = 0
            for u in range(1, N + 1):
                if comp_id[u] == comp_count:
                    for v in adj[u]:
                        if comp_id[v] == comp_count:
                            edge_count += 1
            comp_edges[-1] = edge_count // 2

    total_moves = 0
    for cid in range(comp_count):
        a = comp_nodes0[cid]
        b = comp_nodes1[cid]
        total_moves += a * b - comp_edges[cid]

    if total_moves % 2 == 1:
        print("Aoki")
    else:
        print("Takahashi")

if __name__ == "__main__":
    solve()
