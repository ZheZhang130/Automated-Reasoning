import sys
from sys import stdin

def solve():
    data = stdin.read().split()
    if not data:
        return
    it = iter(data)
    N = int(next(it))
    M = int(next(it))
    
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
        rx, ry = find(x), find(y)
        if rx == ry:
            return False
        if rx < ry:
            parent[ry] = rx
        else:
            parent[rx] = ry
        return True
    
    cycles = 0
    for _ in range(M):
        u = int(next(it))
        v = int(next(it))
        if not union(u, v):
            cycles += 1
    
    print(cycles)

if __name__ == "__main__":
    solve()
