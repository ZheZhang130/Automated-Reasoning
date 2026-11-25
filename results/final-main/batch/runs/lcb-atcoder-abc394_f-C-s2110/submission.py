import sys
from collections import deque

# Increase recursion depth just in case, though we use iterative approach
sys.setrecursionlimit(300000)

def solve():
    # Read all input from stdin
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    try:
        N = int(next(iterator))
    except StopIteration:
        return

    if N == 1:
        # Single vertex, no degree 4 possible
        print(-1)
        return

    # Build adjacency list
    adj = [[] for _ in range(N + 1)]
    for _ in range(N - 1):
        u = int(next(iterator))
        v = int(next(iterator))
        adj[u].append(v)
        adj[v].append(u)

    # Root the tree at vertex 1
    # We need to compute parent pointers and a processing order (post-order)
    parent = [0] * (N + 1)
    order = []
    stack = [1]
    visited = [False] * (N + 1)
    visited[1] = True
    
    # BFS to establish parent-child relationships and order
    queue = deque([1])
    while queue:
        u = queue.popleft()
        order.append(u)
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                queue.append(v)
    
    # Now process in reverse order (bottom-up)
    # dp[u] = max degree-4 vertices in the subtree of u, given that the edge (parent[u], u) is used
    # If u is a leaf in the alkane, it contributes 0 to the count of degree-4 vertices
    # If u is a degree-4 vertex, it contributes 1 plus sum of 3 largest children's dp values
    
    dp = [0] * (N + 1)
    max_degree4 = 0
    
    # Process in reverse order (children before parents)
    for u in reversed(order):
        # Collect dp values from children
        children_dp = []
        for v in adj[u]:
            if v != parent[u]:
                children_dp.append(dp[v])
        
        # Sort children_dp in descending order to get largest values
        children_dp.sort(reverse=True)
        
        # Option 1: u is a leaf in the alkane (edge to parent is used)
        # This is always feasible if parent[u] exists (i.e., u is not root)
        # But actually, we can also consider u as a leaf even if it's root, 
        # but root has no parent edge, so it can only be degree-4 or leaf with no parent.
        # However, for the alkane definition, we need at least one degree-4 vertex.
        # So we'll handle that separately.
        
        # Option 2: u is a degree-4 vertex
        # It needs either:
        #   a) 4 children (all used as degree-4 or leaves) -> needs 4 children
        #   b) 3 children + 1 parent edge -> needs at least 3 children and parent exists
        
        # For option 2a: u is degree-4 with 4 children
        if len(children_dp) >= 4:
            # Sum of 4 largest children
            val = 1 + sum(children_dp[:4])
            dp[u] = max(dp[u], val)
            max_degree4 = max(max_degree4, val)
        
        # For option 2b: u is degree-4 with 3 children + parent
        if len(children_dp) >= 3 and parent[u] != 0:
            val = 1 + sum(children_dp[:3])
            dp[u] = max(dp[u], val)
            max_degree4 = max(max_degree4, val)
        
        # Option 1: u is a leaf
        # This doesn't contribute to degree-4 count, but we need to track it for parent's calculation
        # Actually, dp[u] represents the max degree-4 vertices in subtree when parent edge is used
        # If u is a leaf, it contributes 0 to the count, which is already the default
        
        # Special case: if u is root (parent[u] == 0), it can only be degree-4 with 4 children
        # We already handled that in option 2a
        
    # Check if we found any valid alkane
    if max_degree4 == 0:
        print(-1)
    else:
        # Number of vertices = 3 * I + 2 where I is number of degree-4 vertices
        print(3 * max_degree4 + 2)

if __name__ == "__main__":
    solve()
