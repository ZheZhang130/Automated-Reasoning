import sys
from collections import deque

def solve():
    data = sys.stdin.read().split()
    N = int(data[0])
    adj = []
    for i in range(N):
        row = data[1 + i]
        adj.append(row)
    
    # Build adjacency list
    graph = [[] for _ in range(N)]
    for i in range(N):
        for j in range(N):
            c = adj[i][j]
            if c != '-':
                graph[i].append((j, c))
    
    # Initialize the answer matrix with infinity
    INF = float('inf')
    ans = [[INF] * N for _ in range(N)]
    
    # For each starting node i, do BFS to find all (node, string) pairs
    # We use a dictionary: visited[(node, string)] = length
    # We prune if the string length exceeds 2*N.
    
    for i in range(N):
        # BFS from i
        # State: (node, string)
        visited = {}
        queue = deque()
        
        # Start with (i, "") - using integer i
        visited[(i, '')] = 0
        queue.append((i, ''))
        
        while queue:
            node, s = queue.popleft()
            length = len(s)
            
            # Try to extend
            for next_node, c in graph[node]:
                new_s = s + c
                new_length = length + 1
                
                # Prune if the string is too long
                if new_length > 2 * N:
                    continue
                
                state = (next_node, new_s)
                if state not in visited:
                    visited[state] = new_length
                    queue.append(state)
        
        # Now, for each j, check if there's a palindrome path from i to j
        for j in range(N):
            for state, length in visited.items():
                node, s = state
                if node == j:
                    # Check if s is a palindrome
                    if s == s[::-1]:
                        ans[i][j] = min(ans[i][j], length)
    
    # Also, for i == j, the empty string is a palindrome of length 0
    for i in range(N):
        ans[i][i] = 0
    
    # Print the answer
    for i in range(N):
        row = []
        for j in range(N):
            if ans[i][j] == INF:
                row.append("-1")
            else:
                row.append(str(ans[i][j]))
        print(" ".join(row))

if __name__ == "__main__":
    solve()
