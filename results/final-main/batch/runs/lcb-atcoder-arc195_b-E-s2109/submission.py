import sys
from collections import Counter

def solve():
    input_data = sys.stdin.read().split()
    idx = 0
    N = int(input_data[idx]); idx += 1
    A = list(map(int, input_data[idx:idx+N])); idx += N
    B = list(map(int, input_data[idx:idx+N])); idx += N

    # Count fixed values in A and B
    fixed_A = [x for x in A if x != -1]
    fixed_B = [x for x in B if x != -1]

    # Count how many -1s we have in each
    cnt_A = fixed_A.count(-1)
    cnt_B = fixed_B.count(-1)

    # We can fill -1s with any non-negative integer.
    # We can also rearrange A.
    # Goal: A_i + B_i = S for all i, with A_i, B_i >= 0.

    # Strategy:
    # For positions where both A and B are fixed, we must have A_i + B_i = S.
    # So S must be at least max(A_i + B_i) over all fixed pairs.
    # Also, for any position where one is fixed and the other is -1, 
    # we can choose the -1 value to satisfy the sum S, as long as S - fixed >= 0.
    # For positions where both are -1, we can choose any non-negative values that sum to S.

    # So:
    # 1. Compute min possible S: must be at least max(A_i + B_i) for all i where both are fixed.
    #    If there are no fixed pairs, min_S = 0.
    # 2. For each position:
    #    - If both fixed: check A_i + B_i == S. If not, impossible.
    #    - If one fixed (say A_i fixed, B_i = -1): we need S - A_i >= 0.
    #    - If both -1: we can always fill with (0, S) as long as S >= 0.
    #
    # But we can choose S freely? Actually, we can choose the filled values arbitrarily.
    # However, the fixed pairs constrain S.
    # So S must be at least max(A_i + B_i) for all fixed pairs.
    # Also, for positions with one fixed, say A_i fixed, we need S >= A_i.
    # Similarly, if B_i fixed, S >= B_i.
    # So S must be at least max( all fixed A_i, all fixed B_i, all fixed A_i+B_i ).
    # But note: if we have a fixed pair (a, b), then S = a+b, so S is fixed for that pair.
    # If there are multiple fixed pairs, they must all have the same sum.
    #
    # Therefore:
    # Step 1: Check all fixed pairs: they must all have the same sum S.
    # Step 2: For positions with one fixed value, say A_i = a, then we need S >= a.
    #          Similarly, if B_i = b, then S >= b.
    # Step 3: For positions with both -1, we can set A_i=0, B_i=S (or any split) as long as S>=0.
    #
    # So the algorithm:
    # 1. Collect all fixed pairs and check they have the same sum S.
    #    If no fixed pairs, S can be any non-negative integer. We'll choose S = max(max(fixed_A), max(fixed_B), 0).
    #    But actually, we can choose S as large as needed? However, we want to minimize constraints.
    #    Actually, we can choose S to be the maximum of:
    #        - all fixed A_i
    #        - all fixed B_i
    #        - all fixed A_i+B_i (if any)
    #    Why? Because for a fixed pair (a,b), we must have S = a+b. So if there are multiple fixed pairs, they must agree.
    #    If there is at least one fixed pair, then S is fixed to that sum.
    #    If there are no fixed pairs, then we can choose S arbitrarily. To minimize constraints, we can choose S = max(max(fixed_A), max(fixed_B), 0).
    #    But note: if there are fixed values that are not in pairs, we still need S >= those values.
    #
    # Revised plan:
    # Let S_min = 0.
    # For every fixed A_i, S_min = max(S_min, A_i).
    # For every fixed B_i, S_min = max(S_min, B_i).
    # For every fixed pair (A_i, B_i), we require A_i + B_i == S_min. 
    #    But if we have multiple fixed pairs, they must all have the same sum.
    #    So: if there are fixed pairs, they must all have the same sum, say S_fixed.
    #    Then we set S = S_fixed.
    #    If there are no fixed pairs, then S can be chosen as S_min (which is max of all fixed values, or 0).
    #
    # However, what if we have fixed pairs and also fixed single values?
    # Example: A = [1, -1], B = [2, -1]. Fixed pair: (1,2) -> sum=3. Fixed single: none? 
    # But wait, the fixed values are part of the pairs. 
    # Actually, the fixed values are given. The -1s are to be filled.
    # So the fixed pairs are the positions where both A_i and B_i are not -1.
    # The positions where one is -1 are not fixed pairs.
    #
    # So:
    # Step 1: Identify all positions i where A_i != -1 and B_i != -1. These are fixed pairs.
    # Step 2: If there are fixed pairs, they must all have the same sum S. If not, return "No".
    # Step 3: Let S = that common sum (if fixed pairs exist). If no fixed pairs, then S can be chosen as max(max(fixed_A), max(fixed_B), 0).
    # Step 4: For every position i:
    #    - If A_i != -1 and B_i != -1: check A_i + B_i == S. (Already checked in step 2, but do again for safety)
    #    - If A_i != -1 and B_i == -1: we need S - A_i >= 0. If not, return "No".
    #    - If A_i == -1 and B_i != -1: we need S - B_i >= 0. If not, return "No".
    #    - If A_i == -1 and B_i == -1: we can fill with (0, S) as long as S >= 0. Since S is non-negative by construction, this is always possible.
    #
    # Step 5: Also, we must ensure that S is non-negative. Since all fixed values are non-negative (because we only consider non -1, and input says non-negative for filled, and fixed values are given as non-negative? 
    #    Constraints: -1 <= A_i, B_i <= 10^9. But when we fill -1, we fill with non-negative. The fixed values (non -1) are given as non-negative? 
    #    The problem says: "replace A_i with any non-negative integer". So the fixed values (non -1) are already non-negative? 
    #    The constraints say -1 <= A_i <= 10^9, so non -1 values are >=0. So S will be non-negative.
    #
    # Implementation:
    # Read N, A, B.
    # fixed_pairs = []
    # fixed_A_vals = []
    # fixed_B_vals = []
    # For i in range(N):
    #   if A[i] != -1 and B[i] != -1:
    #       fixed_pairs.append(A[i] + B[i])
    #   if A[i] != -1:
    #       fixed_A_vals.append(A[i])
    #   if B[i] != -1:
    #       fixed_B_vals.append(B[i])
    #
    # If fixed_pairs is not empty:
    #   S = fixed_pairs[0]
    #   if any(p != S for p in fixed_pairs): return "No"
    # Else:
    #   S = max(fixed_A_vals + fixed_B_vals, default=0)
    #
    # Now check all positions:
    # For i in range(N):
    #   if A[i] != -1 and B[i] != -1:
    #       if A[i] + B[i] != S: return "No"
    #   elif A[i] != -1:
    #       if S - A[i] < 0: return "No"
    #   elif B[i] != -1:
    #       if S - B[i] < 0: return "No"
    #   else:
    #       # both -1, we can fill with (0, S) which is valid since S>=0.
    #
    # If all checks pass, return "Yes".

    fixed_pairs = []
    fixed_A_vals = []
    fixed_B_vals = []
    for i in range(N):
        if A[i] != -1 and B[i] != -1:
            fixed_pairs.append(A[i] + B[i])
        if A[i] != -1:
            fixed_A_vals.append(A[i])
        if B[i] != -1:
            fixed_B_vals.append(B[i])

    if fixed_pairs:
        S = fixed_pairs[0]
        for p in fixed_pairs:
            if p != S:
                print("No")
                return
    else:
        all_fixed = fixed_A_vals + fixed_B_vals
        if all_fixed:
            S = max(all_fixed)
        else:
            S = 0

    # Now verify all positions
    for i in range(N):
        if A[i] != -1 and B[i] != -1:
            if A[i] + B[i] != S:
                print("No")
                return
        elif A[i] != -1:
            if S - A[i] < 0:
                print("No")
                return
        elif B[i] != -1:
            if S - B[i] < 0:
                print("No")
                return
        else:
            # both -1: we can fill with (0, S) -> 0+S = S, and both non-negative since S>=0.
            pass

    print("Yes")

if __name__ == "__main__":
    solve()
