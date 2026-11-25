import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))
    
    # Build adjacency list
    adj = [[] for _ in range(N + 1)]
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        adj[u].append(v)
        adj[v].append(u)
    
    # Count connected components and compute bipartition for each
    visited = [False] * (N + 1)
    total_moves = 0
    
    for i in range(1, N + 1):
        if not visited[i]:
            # BFS to find bipartition and collect component nodes
            color = [-1] * (N + 1)
            color[i] = 0
            queue = [i]
            component_nodes = [i]
            visited[i] = True
            idx = 0
            while idx < len(queue):
                u = queue[idx]
                idx += 1
                for v in adj[u]:
                    if not visited[v]:
                        visited[v] = True
                        color[v] = 1 - color[u]
                        queue.append(v)
                        component_nodes.append(v)
            
            count0 = sum(1 for u in component_nodes if color[u] == 0)
            count1 = sum(1 for u in component_nodes if color[u] == 1)
            
            # Count edges in this component by summing degrees and dividing by 2
            edge_count = 0
            for u in component_nodes:
                edge_count += len(adj[u])
            edge_count //= 2
            
            max_edges = count0 * count1
            total_moves += (max_edges - edge_count)
    
    if total_moves % 2 == 1:
        print("Aoki")
    else:
        print("Takahashi")

if __name__ == "__main__":
    solve()
