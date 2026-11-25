import sys

# Increase recursion depth just in case, though N is small
sys.setrecursionlimit(2000)

def solve():
    # Read all input from stdin
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    
    try:
        N = int(next(iterator))
        M = int(next(iterator))
    except StopIteration:
        return

    # Adjacency list: adj[u] = list of (v, w)
    adj = [[] for _ in range(N + 1)]
    
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        w = int(next(iterator))
        adj[u].append((v, w))
        adj[v].append((u, w))
    
    # We need to find the minimum XOR path from 1 to N in a simple path.
    # Since N <= 10, we can use DFS with backtracking to explore all simple paths.
    
    min_xor = (1 << 60)  # Initialize with a value larger than any possible XOR (max w < 2^60)
    
    # DFS function
    # current_node: current vertex
    # current_xor: current XOR sum of edge weights on the path
    # visited: set of visited vertices on the current path
    def dfs(current_node, current_xor, visited):
        nonlocal min_xor
        
        # If we reached the target
        if current_node == N:
            if current_xor < min_xor:
                min_xor = current_xor
            return
        
        # Explore neighbors
        for neighbor, weight in adj[current_node]:
            if neighbor not in visited:
                # Mark neighbor as visited
                visited.add(neighbor)
                # Recurse
                dfs(neighbor, current_xor ^ weight, visited)
                # Backtrack: unmark neighbor
                visited.remove(neighbor)
    
    # Start DFS from vertex 1
    visited = {1}
    dfs(1, 0, visited)
    
    print(min_xor)

if __name__ == "__main__":
    solve()
