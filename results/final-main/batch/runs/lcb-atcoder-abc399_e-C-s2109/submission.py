import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    S = input_data[1]
    T = input_data[2]

    # Build the mapping from each character in S to the required character in T
    # If any character in S maps to more than one character in T, it's impossible
    mapping = {}
    for i in range(N):
        s_char = S[i]
        t_char = T[i]
        if s_char in mapping:
            if mapping[s_char] != t_char:
                print(-1)
                return
        else:
            mapping[s_char] = t_char

    # Build the graph of non-identity mappings
    # Each node is a character 'a'-'z'
    # We only care about characters that appear in S and need to be changed
    # The graph edges are: u -> v if mapping[u] == v and u != v
    # We need to count the minimum operations to resolve all cycles
    
    # First, identify which characters appear in T
    chars_in_T = set(T)
    
    # If T uses all 26 letters, any nontrivial change is impossible
    # But we need to check if S also uses all 26 letters
    # Actually, the condition is: if T uses all 26 letters, then S must also use all 26 letters
    # for the answer to be valid. If S doesn't use all 26 letters, we can't make S identical to T
    # if there are any non-identity mappings.
    
    # Let's build the graph
    # Nodes are characters 'a' through 'z'
    # Edges: for each char c in S, if mapping[c] != c, add edge c -> mapping[c]
    
    # We need to find cycles in this graph
    # A cycle requires an extra operation if it has no incoming edge from outside the cycle
    
    # Build adjacency list for the graph
    adj = {chr(ord('a') + i): [] for i in range(26)}
    in_degree = {chr(ord('a') + i): 0 for i in range(26)}
    
    for c in mapping:
        if mapping[c] != c:
            adj[c].append(mapping[c])
            in_degree[mapping[c]] += 1
    
    # Find cycles using DFS
    visited = {c: False for c in adj}
    in_stack = {c: False for c in adj}
    cycles = []
    
    def dfs(node, path):
        visited[node] = True
        in_stack[node] = True
        path.append(node)
        
        for neighbor in adj[node]:
            if not visited[neighbor]:
                dfs(neighbor, path)
            elif in_stack[neighbor]:
                # Found a cycle
                cycle_start_idx = path.index(neighbor)
                cycle = path[cycle_start_idx:]
                cycles.append(cycle)
        
        path.pop()
        in_stack[node] = False
    
    for c in adj:
        if not visited[c]:
            dfs(c, [])
    
    # Count cycles that have no incoming edge from outside the cycle
    # A cycle has no incoming edge from outside if all its nodes only have edges from within the cycle
    # We can check this by seeing if any node in the cycle has an in-degree from outside the cycle
    
    # Actually, the in_degree we computed includes edges from outside the cycle
    # So a cycle has no incoming edge from outside if for all nodes in the cycle,
    # their in_degree equals the number of edges from within the cycle
    
    # Let's compute the number of edges within each cycle
    cycle_extra_ops = 0
    for cycle in cycles:
        # Count edges within the cycle
        edges_within = 0
        for node in cycle:
            for neighbor in adj[node]:
                if neighbor in cycle:
                    edges_within += 1
        
        # The number of edges within the cycle should be equal to the length of the cycle
        # because each node in the cycle has exactly one outgoing edge to the next node in the cycle
        # So edges_within should equal len(cycle)
        
        # Now check if there are any incoming edges from outside the cycle
        # An incoming edge from outside means a node in the cycle has an in_degree > edges_within
        has_external_incoming = False
        for node in cycle:
            if in_degree[node] > edges_within:
                has_external_incoming = True
                break
        
        if not has_external_incoming:
            cycle_extra_ops += 1
    
    # The base answer is the number of non-identity mappings
    base_ops = sum(1 for c in mapping if mapping[c] != c)
    
    # If there are cycles with no external incoming edges, we need extra operations
    # But we also need to check if there's a temporary letter available
    # A temporary letter is available if T doesn't use all 26 letters
    
    if len(chars_in_T) == 26:
        # If T uses all 26 letters, we can't have any non-identity mappings
        # because that would require merging two letters, which is impossible
        if base_ops > 0:
            print(-1)
            return
        else:
            print(0)
            return
    else:
        # There's at least one letter not in T, so we can use it as a temporary
        answer = base_ops + cycle_extra_ops
        print(answer)

solve()
