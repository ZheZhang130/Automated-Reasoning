import sys
from functools import reduce

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
    
    # Since N is small (<= 10), we can use DFS to explore all simple paths from 1 to N
    min_xor = None
    
    def dfs(u, current_xor, visited):
        nonlocal min_xor
        if u == N:
            if min_xor is None or current_xor < min_xor:
                min_xor = current_xor
            return
        
        for v, w in adj[u]:
            if v not in visited:
                visited.add(v)
                dfs(v, current_xor ^ w, visited)
                visited.remove(v)
    
    dfs(1, 0, {1})
    
    print(min_xor)

if __name__ == "__main__":
    solve()
