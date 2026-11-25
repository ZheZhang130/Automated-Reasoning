import sys
from collections import deque

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
    
    # Since N is small (<= 10), we can use BFS to find all simple paths from 1 to N
    # and compute the XOR sum for each path.
    
    # We'll use BFS to explore all simple paths.
    # State: (current_node, visited_mask, current_xor)
    # Since N <= 10, visited_mask can be up to 2^10 = 1024 states.
    
    from collections import deque
    
    # BFS to find all simple paths
    # We need to track visited nodes to ensure simple paths
    
    # Since we want all simple paths, we can use DFS with backtracking
    # or BFS with state (node, mask, xor_val)
    
    # Let's use BFS with state (node, mask, xor_val)
    # mask is a bitmask of visited nodes
    
    start_node = 1
    end_node = N
    
    # BFS queue: (node, mask, xor_val)
    queue = deque()
    queue.append((start_node, 1 << (start_node - 1), 0))
    
    # We want to find all paths to end_node
    # Since we need simple paths, we track visited nodes with mask
    
    # However, BFS might not be the best for finding all paths, but with N <= 10,
    # the number of simple paths is manageable.
    
    # Let's use DFS instead for simplicity
    
    min_xor = None
    
    def dfs(u, visited_mask, current_xor):
        nonlocal min_xor
        if u == end_node:
            if min_xor is None or current_xor < min_xor:
                min_xor = current_xor
            return
        
        for v, w in adj[u]:
            if not (visited_mask & (1 << (v - 1))):
                dfs(v, visited_mask | (1 << (v - 1)), current_xor ^ w)
    
    dfs(start_node, 1 << (start_node - 1), 0)
    
    print(min_xor)

if __name__ == "__main__":
    solve()
