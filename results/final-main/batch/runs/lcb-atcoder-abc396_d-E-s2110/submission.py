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
    
    # Since N is small (<= 10), we can use BFS to find all simple paths from 1 to N
    # and compute the XOR sum for each path.
    # However, a simple BFS doesn't guarantee simple paths.
    # We can use DFS with backtracking to find all simple paths.
    
    min_xor = None
    
    def dfs(u, target, current_xor, visited):
        nonlocal min_xor
        if u == target:
            if min_xor is None or current_xor < min_xor:
                min_xor = current_xor
            return
        
        for v, w in adj[u]:
            if v not in visited:
                visited.add(v)
                dfs(v, target, current_xor ^ w, visited)
                visited.remove(v)
    
    # Start DFS from vertex 1
    visited = {1}
    dfs(1, N, 0, visited)
    
    print(min_xor)

if __name__ == "__main__":
    solve()
