import sys
from collections import defaultdict

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    it = iter(data)
    N = int(next(it))
    M = int(next(it))
    
    adj = defaultdict(list)
    for _ in range(M):
        u = int(next(it))
        v = int(next(it))
        adj[u].append(v)
        adj[v].append(u)
    
    visited = [False] * (N + 1)
    edges_to_remove = 0
    
    for start in range(1, N + 1):
        if visited[start]:
            continue
        
        # DFS to count edges in this component
        stack = [start]
        visited[start] = True
        component_nodes = []
        
        while stack:
            node = stack.pop()
            component_nodes.append(node)
            for neighbor in adj[node]:
                if not visited[neighbor]:
                    visited[neighbor] = True
                    stack.append(neighbor)
        
        # Count edges within this component
        # Each edge is counted twice (once from each end)
        edge_count = 0
        for node in component_nodes:
            for neighbor in adj[node]:
                if neighbor > node:  # Count each edge once
                    edge_count += 1
        
        # For a forest, a component with k nodes must have k-1 edges
        # So we need to remove: edge_count - (len(component_nodes) - 1)
        edges_to_remove += edge_count - (len(component_nodes) - 1)
    
    print(edges_to_remove)

if __name__ == "__main__":
    solve()
