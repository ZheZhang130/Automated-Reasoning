import sys
from collections import defaultdict

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    S = data[1]
    T = data[2]

    # For each position i, S[i] must map to T[i]
    # If S[i] == S[j], then T[i] must equal T[j] (otherwise impossible -> -1)
    # We need to find minimum operations to make all S[i] == T[i]
    # This is equivalent to: for each char c in 'a'..'z', if it appears in S,
    # we must change it to some other char. Each change counts as 1 op.
    # But we can chain changes: a->b->c counts as 2 ops.
    # Actually, the problem is: we want to transform S to T.
    # For each character x in S, if x appears at positions where T has different chars,
    # we must change x. The minimum ops is the number of characters in S that need to be changed.
    # But we can change one char to another, and that affects all occurrences.
    # So for each char c in 'a'..'z', if c appears in S, we check:
    #   Let positions of c in S be P_c.
    #   For all i in P_c, T[i] must be the same char, say d.
    #   If not, return -1.
    #   If c == d, no change needed for this char.
    #   If c != d, we need to change c to d. This is 1 op for this char.
    # Total ops = number of characters in S that need to be changed.
    # But wait: can we do better by chaining? e.g., a->b->c?
    # No, because each op changes ALL occurrences. So if we have a->b and b->c,
    # doing a->b then b->c would change the original a's to b's, then those b's (including original b's) to c's.
    # So we cannot independently control different occurrences of the same char.
    # Therefore, for each char c in S, if it needs to become d (and c != d), we must do one op: c->d.
    # But note: if we change c to d, and d is already present in S (at some positions),
    # then those positions (which originally had d) will remain d (since we only change c, not d).
    # So the operation c->d is safe.
    # The number of operations is the number of chars c such that c != target(c).
    
    # Step 1: Check consistency
    # For each char c, collect all T[i] where S[i] == c. They must all be equal.
    char_targets = defaultdict(set)
    for i in range(N):
        char_targets[S[i]].add(T[i])
    
    for c, targets in char_targets.items():
        if len(targets) > 1:
            print(-1)
            return

    # Step 2: Count how many chars need to be changed
    # For each char c, if c != target, then we need to change c to target.
    # But note: if we change c to target, and target is already present in S (at some positions),
    # then those positions (which originally had target) will remain target (since we only change c, not target).
    # So the operation c->target is safe.
    # The number of operations is the number of chars c such that c != target(c).
    
    ops = 0
    for c in char_targets:
        target = list(char_targets[c])[0]
        if c != target:
            ops += 1
    
    print(ops)

solve()
