import sys

# Increase recursion depth for deep trees in find operation
sys.setrecursionlimit(300000)

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))
    
    # Disjoint Set Union (DSU) structure
    parent = list(range(N + 1))
    
    def find(x):
        # Path compression
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        root_x = find(x)
        root_y = find(y)
        if root_x != root_y:
            parent[root_x] = root_y
            return True
        return False
    
    edges_to_delete = 0
    
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        
        if not union(u, v):
            # Endpoints already connected, this edge creates a cycle
            edges_to_delete += 1
    
    print(edges_to_delete)

if __name__ == "__main__":
    solve()
