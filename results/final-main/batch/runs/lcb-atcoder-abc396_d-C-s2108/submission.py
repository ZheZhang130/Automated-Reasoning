import sys

# Increase recursion depth just in case, though N is small
sys.setrecursionlimit(2000)

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
    
    min_xor = (1 << 60)
    
    def dfs(u, current_xor, visited):
        nonlocal min_xor
        if u == N:
            if current_xor < min_xor:
                min_xor = current_xor
            return
        
        for v, w in adj[u]:
            if v not in visited:
                new_visited = visited | {v}
                dfs(v, current_xor ^ w, new_visited)
    
    dfs(1, 0, {1})
    
    print(min_xor)

if __name__ == "__main__":
    solve()
