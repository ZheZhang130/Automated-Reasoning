import sys
from sys import stdin

def solve():
    lines = stdin.read().splitlines()
    if not lines:
        return
    
    first_line = lines[0].strip()
    if not first_line:
        return
    
    parts = first_line.split()
    N = int(parts[0])
    M = int(parts[1])
    
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
    for i in range(1, M + 1):
        line = lines[i].strip()
        u, v = map(int, line.split())
        if union(u, v):
            edges_to_remove += 1
    
    print(edges_to_remove)

if __name__ == "__main__":
    solve()
