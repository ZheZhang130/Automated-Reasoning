import sys
from sys import stdin

def solve():
    input_data = stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    
    try:
        N = int(next(iterator))
        M = int(next(iterator))
    except StopIteration:
        return
    
    if M == 0:
        print(0)
        return
    
    # Use Union-Find to count edges that form cycles
    parent = list(range(N + 1))
    
    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]
        # Path compression
        while parent[x] != x:
            nxt = parent[x]
            parent[x] = root
            x = nxt
        return root
    
    def union(x, y):
        root_x = find(x)
        root_y = find(y)
        if root_x != root_y:
            parent[root_x] = root_y
            return False  # No cycle
        return True  # Cycle detected
    
    edges_to_remove = 0
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        if union(u, v):
            edges_to_remove += 1
    
    print(edges_to_remove)

if __name__ == "__main__":
    solve()
