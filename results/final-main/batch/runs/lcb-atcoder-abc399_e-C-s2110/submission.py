import sys
from collections import defaultdict

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    S = data[1]
    T = data[2]

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

    # Count non-identity mappings (edges in the graph)
    edge_count = 0
    for c in mapping:
        if mapping[c] != c:
            edge_count += 1

    if edge_count == 0:
        print(0)
        return

    # Build reverse graph to check for external incoming edges to cycles
    rev_graph = defaultdict(list)
    for c in mapping:
        if mapping[c] != c:
            rev_graph[mapping[c]].append(c)

    # Find cycles in the functional graph
    # Nodes are characters that have mapping[c] != c
    nodes_with_edges = [c for c in mapping if mapping[c] != c]
    
    # Use state: 0 = unvisited, 1 = visiting, 2 = visited
    state = {c: 0 for c in nodes_with_edges}
    cycles = []
    
    for start_node in nodes_with_edges:
        if state[start_node] != 0:
            continue
        
        path = []
        curr = start_node
        while True:
            if state.get(curr, 0) == 1:
                # Found a cycle - curr is in path
                try:
                    cycle_start_idx = path.index(curr)
                except ValueError:
                    # curr not in path, shouldn't happen if logic is correct
                    break
                cycle = path[cycle_start_idx:]
                cycles.append(cycle)
                break
            if state.get(curr, 0) == 2:
                break
            state[curr] = 1
            path.append(curr)
            curr = mapping[curr]
            if curr not in nodes_with_edges:
                break
    
    # For each cycle, check if it has an incoming edge from outside
    cycles_with_no_external_incoming = 0
    
    for cycle in cycles:
        cycle_set = set(cycle)
        has_external_incoming = False
        for node in cycle:
            for incoming_node in rev_graph[node]:
                if incoming_node not in cycle_set:
                    has_external_incoming = True
                    break
            if has_external_incoming:
                break
        if not has_external_incoming:
            cycles_with_no_external_incoming += 1
    
    # If T uses all 26 letters and we have non-identity mappings, it's impossible
    letters_in_T = set(T)
    if len(letters_in_T) == 26:
        print(-1)
        return
    
    # Answer is edge_count + cycles_with_no_external_incoming
    print(edge_count + cycles_with_no_external_incoming)

solve()
