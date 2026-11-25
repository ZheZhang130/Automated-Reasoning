import sys

# Increase recursion depth for deep trees in path compression
sys.setrecursionlimit(300000)

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

    # Disjoint Set Union (DSU) structure
    parent = list(range(N + 1))
    
    def find(i):
        # Path compression
        if parent[i] != i:
            parent[i] = find(parent[i])
        return parent[i]
    
    def union(i, j):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j
            return True
        return False
    
    deletions = 0
    
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        
        if union(u, v):
            # Edge connects two different components, keep it
            pass
        else:
            # Edge creates a cycle, delete it
            deletions += 1
    
    print(deletions)

if __name__ == "__main__":
    solve()
