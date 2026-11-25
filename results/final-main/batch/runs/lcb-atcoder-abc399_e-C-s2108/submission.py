import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    N = int(input_data[0])
    S = input_data[1]
    T = input_data[2]

    # Build mapping from each character in S to its required character in T
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

    # Build directed graph: each char -> its target
    # Only consider chars that are not already equal (s_char != t_char)
    graph = {}
    for s_char, t_char in mapping.items():
        if s_char != t_char:
            graph[s_char] = t_char

    # Count cycles in the graph
    # We need to find cycles in the functional graph (each node has at most 1 outgoing edge)
    visited = set()
    cycles_with_no_incoming = 0
    cycles_with_incoming = 0

    # First, compute in-degrees for nodes that are in the graph (only non-identity mappings)
    in_degree = defaultdict(int)
    for s_char in graph:
        target = graph[s_char]
        in_degree[target] += 1

    # Find cycles
    for start_node in list(graph.keys()):
        if start_node in visited:
            continue
        path = []
        curr = start_node
        while curr not in visited:
            if curr not in graph:
                break
            visited.add(curr)
            path.append(curr)
            curr = graph[curr]
        
        # Check if we completed a cycle
        if curr in path:
            cycle_start_idx = path.index(curr)
            cycle_nodes = path[cycle_start_idx:]
            # Check if any node in the cycle has an incoming edge from outside the cycle
            has_external_incoming = False
            for node in cycle_nodes:
                if in_degree[node] > 1:
                    has_external_incoming = True
                    break
            if has_external_incoming:
                cycles_with_incoming += 1
            else:
                cycles_with_no_incoming += 1
        else:
            # Not a cycle, just a path leading to a node not in graph or visited
            pass

    # Count non-identity mappings
    non_identity_count = len(graph)

    # If T uses all 26 letters, we can't do any changes if there are non-identity mappings
    # But actually, if S and T are different, and T uses all 26 letters, it's impossible
    # because we can't merge two letters into one if all 26 are used
    t_chars = set(T)
    if len(t_chars) == 26 and non_identity_count > 0:
        print(-1)
        return

    # Calculate answer
    ans = non_identity_count + cycles_with_no_incoming
    print(ans)

if __name__ == "__main__":
    solve()
