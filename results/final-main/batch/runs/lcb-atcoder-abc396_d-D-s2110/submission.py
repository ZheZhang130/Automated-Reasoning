import sys
from collections import deque

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

    adj = [[] for _ in range(N + 1)]
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        w = int(next(iterator))
        adj[u].append((v, w))
        adj[v].append((u, w))

    # Since N is small (<= 10), we can use BFS/DFS to explore all simple paths
    # We'll use DFS to find all simple paths from 1 to N and compute XOR for each
    
    min_xor = None
    
    # Use iterative DFS to avoid recursion limit issues and manage visited state
    # Stack will contain (current_node, current_xor, visited_mask)
    # Since N <= 10, we can use an integer mask for visited vertices
    
    start_node = 1
    end_node = N
    
    # We need to track visited vertices to ensure simple paths
    # Use a stack for DFS: (u, current_xor, visited_mask)
    stack = [(start_node, 0, 1 << (start_node - 1))]
    
    while stack:
        u, current_xor, visited_mask = stack.pop()
        
        if u == end_node:
            if min_xor is None or current_xor < min_xor:
                min_xor = current_xor
            continue
        
        for v, w in adj[u]:
            # Check if v is already visited in current path
            if not (visited_mask & (1 << (v - 1))):
                new_mask = visited_mask | (1 << (v - 1))
                new_xor = current_xor ^ w
                stack.append((v, new_xor, new_mask))
    
    print(min_xor)

if __name__ == "__main__":
    solve()
