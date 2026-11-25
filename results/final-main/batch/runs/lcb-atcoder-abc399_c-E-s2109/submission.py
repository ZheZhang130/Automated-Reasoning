import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))
    
    if M == 0:
        print(0)
        return
    
    adj = defaultdict(list)
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        adj[u].append(v)
        adj[v].append(u)
    
    visited = [False] * (N + 1)
    components = 0
    
    for start_node in range(1, N + 1):
        if visited[start_node]:
            continue
        
        components += 1
        stack = [start_node]
        visited[start_node] = True
        
        while stack:
            node = stack.pop()
            for neighbor in adj[node]:
                if not visited[neighbor]:
                    visited[neighbor] = True
                    stack.append(neighbor)
    
    # A spanning forest has exactly N - components edges
    # We need to remove M - (N - components) edges
    print(M - (N - components))

if __name__ == "__main__":
    solve()
