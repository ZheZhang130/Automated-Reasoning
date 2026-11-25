import sys
from collections import deque

# Increase recursion depth just in case, though we use iterative approach
sys.setrecursionlimit(300000)

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    try:
        N = int(next(iterator))
    except StopIteration:
        return

    if N == 1:
        print(-1)
        return

    adj = [[] for _ in range(N + 1)]
    for _ in range(N - 1):
        u = int(next(iterator))
        v = int(next(iterator))
        adj[u].append(v)
        adj[v].append(u)

    # Root the tree at vertex 1
    parent = [0] * (N + 1)
    order = []
    stack = [1]
    visited = [False] * (N + 1)
    visited[1] = True
    
    # BFS to establish parent-child relationships and processing order
    while stack:
        u = stack.pop()
        order.append(u)
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                stack.append(v)
    
    # Process in reverse order (bottom-up)
    # dp[u] = max number of degree-4 vertices in the subtree of u (when u is connected to its parent)
    # If u is a leaf in the alkane, it contributes 0 to the count of degree-4 vertices.
    # If u is a degree-4 vertex, it contributes 1 plus the sum of the best 3 children branches.
    
    dp = [0] * (N + 1)
    max_degree4_vertices = 0
    
    # We need to know the number of children for each node in the rooted tree
    # Since we built the tree with BFS, we can count children during the BFS or after
    # Actually, we can just use the adjacency list and parent array to determine children
    
    # Let's recompute children counts
    children_count = [0] * (N + 1)
    for u in range(1, N + 1):
        for v in adj[u]:
            if v != parent[u]:
                children_count[u] += 1
    
    # Process in reverse order
    for u in reversed(order):
        # Get the dp values of children
        child_dp = []
        for v in adj[u]:
            if v != parent[u]:
                child_dp.append(dp[v])
        
        # Sort in descending order to get the largest values
        child_dp.sort(reverse=True)
        
        # Option 1: u is a leaf in the alkane (doesn't count as degree-4)
        # This is always possible if there's at least one child branch we can use
        # But actually, if u is a leaf, it doesn't contribute to degree-4 count
        # So dp[u] = 0 in this case
        
        # Option 2: u is a degree-4 vertex
        # It needs 4 edges: either 4 children (if root) or 3 children + parent (if not root)
        # If root: need at least 4 children
        # If not root: need at least 3 children
        
        if len(child_dp) >= 4:
            # Can be degree-4 with 4 children
            val = 1 + sum(child_dp[:4])
            dp[u] = max(dp[u], val)
            max_degree4_vertices = max(max_degree4_vertices, val)
        
        if parent[u] != 0 and len(child_dp) >= 3:
            # Can be degree-4 with 3 children + parent
            val = 1 + sum(child_dp[:3])
            dp[u] = max(dp[u], val)
            max_degree4_vertices = max(max_degree4_vertices, val)
        
        # Also consider if u is a leaf (dp[u] = 0)
        # But 0 is always <= any positive value, so we don't need to explicitly set it
        
    if max_degree4_vertices == 0:
        print(-1)
    else:
        # Number of vertices = 3 * I + 2 where I is number of degree-4 vertices
        print(3 * max_degree4_vertices + 2)

if __name__ == "__main__":
    solve()
