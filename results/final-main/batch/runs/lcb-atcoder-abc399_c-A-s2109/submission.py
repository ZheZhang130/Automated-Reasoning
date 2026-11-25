import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))
    
    if M == 0:
        print(0)
        return
    
    # Use Union-Find to count edges that create cycles
    parent = list(range(N + 1))
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
            return True
        return False
    
    edges_to_remove = 0
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        if not union(u, v):
            # This edge creates a cycle
            edges_to_remove += 1
    
    print(edges_to_remove)

if __name__ == "__main__":
    solve()
