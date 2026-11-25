import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    S = input_data[1]
    T = input_data[2]

    # Check consistency: for each position i, S[i] and T[i] must be compatible.
    # If S[i] == T[i], then we must never change S[i] to something else.
    # If S[i] != T[i], then we must change S[i] to T[i] at some point.
    # Also, if we have two positions i and j with S[i] == S[j], then T[i] must equal T[j].
    # This is because once we change S[i] to T[i], all occurrences of that character become T[i].
    # So if S[i] == S[j], then after transformation, both must be the same, so T[i] == T[j].

    # First, check the necessary condition: for all i, j where S[i] == S[j], we must have T[i] == T[j].
    # We can group indices by S[i] and check T[i] for each group.
    char_to_indices = defaultdict(list)
    for i in range(N):
        char_to_indices[S[i]].append(i)

    # Check consistency
    for char, indices in char_to_indices.items():
        if len(indices) > 1:
            if len(set(T[i] for i in indices)) != 1:
                print(-1)
                return

    # Now, we need to find the minimum number of operations.
    # Each operation is: choose x, y and replace all x with y.
    # We want to transform S to T.
    # Let's think about the mapping from characters in S to characters in T.
    # For each character c in S, we need to map it to some character d in T.
    # But note: we can only do global replacements. So if we have multiple positions with the same character in S,
    # they must all go to the same character in T (which we already checked).
    #
    # However, the operations are sequential. We can chain replacements.
    # For example, if we want to change 'a' to 'b', and then 'b' to 'c', we do two operations.
    # But note: if we have both 'a' and 'b' in S, and we want to change 'a' to 'b', we do that first,
    # but then the original 'b's become 'b' (unchanged) and the 'a's become 'b'. Then if we want to change 'b' to 'c',
    # both the original 'b's and the converted 'a's become 'c'.
    #
    # So the key is: we need to define a mapping from each character in S to a character in T.
    # But the mapping must be consistent: if we have a character c in S, it must map to a single character d in T.
    # And we also have the constraint that if S[i] == T[i], then we cannot change that character.
    #
    # Let's define a directed graph where an edge from u to v means we replace u with v.
    # But note: we can only replace one character at a time. And the replacement is global.
    # Also, we cannot have cycles because that would require infinite operations or be impossible.
    #
    # Actually, the problem is: we want to reach T from S.
    # For each character c in S, we need to decide what it becomes in T.
    # Let f(c) be the character that c becomes in T.
    # Then we must have: for every position i, f(S[i]) == T[i].
    # And f must be a function (each c maps to exactly one d).
    #
    # But note: we can only do replacements. So if we have a character c that we want to change to d,
    # we do one operation: replace c with d.
    # However, if we have multiple characters that need to be changed, we can do them in any order.
    # But caution: if we change c to d, and then later change d to e, then the original c's become e.
    # So the final mapping is: c -> ... -> e.
    #
    # Therefore, the minimum number of operations is the number of characters c in S such that f(c) != c.
    # But wait: is that true? Let's see:
    # Example: S = "ab", T = "ba". 
    # We need: f('a') = 'b', f('b') = 'a'.
    # If we do: replace 'a' with 'b', then S becomes "bb". Then replace 'b' with 'a', then S becomes "aa". That's not "ba".
    # So we cannot simply do independent replacements because the order matters and the replacements are global.
    #
    # Actually, the issue is: if we have a cycle in the desired mapping, we cannot achieve it.
    # For example, if we want 'a'->'b' and 'b'->'a', then:
    # Start: "ab"
    # Option 1: replace 'a' with 'b' -> "bb", then replace 'b' with 'a' -> "aa" (not "ba")
    # Option 2: replace 'b' with 'a' -> "aa", then replace 'a' with 'b' -> "bb" (not "ba")
    # So it's impossible. Hence, if the desired mapping has a cycle, we output -1.
    #
    # But wait: what if we have more characters? 
    # Actually, the problem is: we can only replace one character at a time, and the replacement is global.
    # So the transformation is: we have a set of characters, and we want to map each character in S to a character in T.
    # The mapping must be a function (each character in S maps to exactly one character in T).
    # And the mapping must be acyclic? Not exactly: we can have chains, but cycles are impossible.
    #
    # However, note: we are allowed to do any number of operations. So we can have chains: a->b->c.
    # But we cannot have a cycle: a->b->a.
    #
    # So the algorithm:
    # 1. Check consistency: for each character c in S, all positions i where S[i]==c must have T[i]==d for some fixed d.
    #    If not, return -1.
    # 2. Define a mapping: for each character c in S, let d be the character such that for all i with S[i]==c, T[i]==d.
    #    If c == d, then we don't need to change c.
    #    If c != d, then we need to change c to d.
    # 3. Now, we have a directed graph where an edge from c to d exists if we need to change c to d.
    #    But note: we can only have one outgoing edge per character (which we have by step 1).
    #    However, we can have multiple incoming edges.
    # 4. The problem: if there is a cycle in this graph, then it's impossible -> return -1.
    #    Why? Because if we have a cycle, say a->b->c->a, then we would need to change a to b, then b to c, then c to a.
    #    But after changing a to b, the original b's are still b, and then we change b to c, so both become c, and then c to a, so all become a.
    #    But we wanted a to become a? No, we wanted a to become a? Actually, in the cycle, we want a->b, b->c, c->a.
    #    But at the end, we want the character that was originally a to be a? No, we want it to be a? 
    #    Actually, the target T has specific characters at each position. 
    #    For the positions that were originally a, we want them to be a? But in the cycle, we set f(a)=b, so we want them to be b.
    #    But after step3, they are a. So that's not b.
    #    Hence, cycles are impossible.
    #
    # 5. So we need to check for cycles in the mapping graph.
    #    The graph has nodes = 'a' to 'z'.
    #    For each character c in S, if c != d (where d is the target character for c), then add edge c->d.
    #    Then check for cycles.
    #
    # 6. If no cycle, then the minimum number of operations is the number of edges in the graph? 
    #    But note: we can do the operations in any order, and each edge corresponds to one operation.
    #    However, we must avoid cycles. And if there are no cycles, then the number of operations is the number of edges.
    #    But wait: what if we have a chain a->b->c? Then we need two operations: first a->b, then b->c.
    #    So yes, the number of operations is the number of edges.
    #
    # However, there is a catch: what if we have multiple edges that are independent? 
    # For example, a->b and c->d. Then we can do them in any order, and the total operations is 2.
    # So yes, the answer is the number of edges (i.e., the number of characters c such that f(c) != c).
    #
    # But wait: what if the mapping is not defined for some character? 
    # We only care about characters that appear in S.
    #
    # So algorithm refined:
    #   - Build the mapping: for each char c in S, map to d (the corresponding char in T).
    #   - Build a graph: for each c in the mapping, if c != d, add edge c->d.
    #   - Check for cycles in this graph.
    #   - If cycle, return -1.
    #   - Otherwise, return the number of edges.
    #
    # However, note: the graph might have multiple edges? No, because each c has at most one d.
    #
    # Steps:
    #   1. Build the mapping for each character that appears in S.
    #   2. Build a directed graph: for each c that appears in S and c != d, add edge c->d.
    #   3. Check for cycles using DFS.
    #   4. If cycle, return -1.
    #   5. Else, return the number of edges.
    #
    # But wait: what if we have a character that is not in S? We don't care about it.
    #
    # Example: S="ab", T="ba"
    #   mapping: a->b, b->a.
    #   graph: a->b, b->a -> cycle -> return -1.
    #
    # Example: S="ab", T="bb"
    #   mapping: a->b, b->b.
    #   graph: a->b (only one edge). No cycle. Answer = 1.
    #
    # Example: S="ab", T="ac"
    #   mapping: a->a, b->c.
    #   graph: b->c. No cycle. Answer = 1.
    #
    # Example: S="ab", T="ab"
    #   mapping: a->a, b->b. No edges. Answer = 0.
    #
    # Example: S="ab", T="cd"
    #   mapping: a->c, b->d.
    #   graph: a->c, b->d. No cycle. Answer = 2.
    #
    # But wait: what if we have a chain? 
    #   S="a", T="b" -> a->b: 1 op.
    #   S="a", T="c" -> a->c: 1 op? But we can do a->b then b->c? But that would be 2 ops.
    #   However, we can do a->c directly in one op. So the minimum is 1.
    #   So the graph edge is a->c, and we count 1 op.
    #
    # Therefore, the answer is the number of edges in the graph (which is the number of c such that c != d).
    #
    # But note: the graph might have a cycle only if we have a->b and b->a, etc.
    #
    # Implementation:
    #   - Create a mapping dict: for each char c in S, map to d (the corresponding char in T).
    #   - Build a graph: for each c in the mapping, if c != d, add edge c->d.
    #   - Check for cycles: use DFS with states (0: unvisited, 1: visiting, 2: visited).
    #   - Count the number of edges.
    #
    # However, note: the graph might have multiple edges? No, because each c has at most one d.
    #
    # Let's code accordingly.

    mapping = {}
    for i in range(N):
        c = S[i]
        d = T[i]
        if c in mapping:
            if mapping[c] != d:
                # Inconsistent: same character in S maps to different characters in T.
                print(-1)
                return
        else:
            mapping[c] = d

    # Build graph: nodes are 'a' to 'z', but we only care about characters that appear in S.
    # We'll create a graph for all 26 letters, but only add edges for characters that are in mapping and c != d.
    graph = {chr(ord('a') + i): [] for i in range(26)}
    for c, d in mapping.items():
        if c != d:
            graph[c].append(d)

    # Check for cycles using DFS
    state = {node: 0 for node in graph}  # 0: unvisited, 1: visiting, 2: visited
    has_cycle = False

    def dfs(node):
        nonlocal has_cycle
        state[node] = 1
        for neighbor in graph[node]:
            if state[neighbor] == 1:
                has_cycle = True
                return
            if state[neighbor] == 0:
                dfs(neighbor)
                if has_cycle:
                    return
        state[node] = 2

    for node in graph:
        if state[node] == 0:
            dfs(node)
            if has_cycle:
                break

    if has_cycle:
        print(-1)
    else:
        # Count the number of edges (i.e., the number of c such that c != d)
        count = 0
        for c, d in mapping.items():
            if c != d:
                count += 1
        print(count)

solve()
