import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))
    
    adj = [[] for _ in range(N + 1)]
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        w = int(next(iterator))
        adj[u].append((v, w))
        adj[v].append((u, w))
    
    # BFS to find all simple paths from 1 to N
    # Since N is small (<= 10), we can use DFS with backtracking
    
    min_xor = None
    
    def dfs(current, target, visited, current_xor):
        nonlocal min_xor
        
        if current == target:
            if min_xor is None or current_xor < min_xor:
                min_xor = current_xor
            return
        
        # Pruning: if we already found a path, and current_xor >= min_xor, 
        # we might still find a smaller one, but we can't prune based on XOR alone
        # because XOR is not monotonic. However, we can prune if we've visited all neighbors.
        
        for neighbor, weight in adj[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                dfs(neighbor, target, visited, current_xor ^ weight)
                visited.remove(neighbor)
    
    visited = {1}
    dfs(1, N, visited, 0)
    
    print(min_xor)

if __name__ == "__main__":
    solve()
