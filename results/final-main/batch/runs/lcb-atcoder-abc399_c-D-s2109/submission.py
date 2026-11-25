import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))
    
    parent = list(range(N + 1))
    
    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]
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
            return False
        return True
    
    cycles = 0
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        if union(u, v):
            cycles += 1
    
    print(cycles)

if __name__ == "__main__":
    solve()
