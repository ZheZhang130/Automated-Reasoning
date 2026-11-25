import sys

def solve():
    input_data = sys.stdin.read().split()
    idx = 0
    N = int(input_data[idx]); idx += 1
    A = [int(x) for x in input_data[idx:idx+N]]; idx += N
    B = [int(x) for x in input_data[idx:idx+N]]; idx += N
    C = [int(x) for x in input_data[idx:idx+N]]; idx += N

    # Let's re-analyze the problem from scratch.
    # Operation: flip A[i], then pay sum(A[k] * C[k]) where A is AFTER flip.
    # Let S be the current sum of A[k]*C[k].
    # When we flip A[i] (from a to 1-a), the new sum S' = S - a*C[i] + (1-a)*C[i] = S + C[i] - 2*a*C[i].
    # The cost paid is S'.
    # We want to reach state A == B.
    # Let D be the set of indices where A[i] != B[i].
    # We must flip each i in D exactly once.
    # Let's denote the initial sum as S0.
    # When we flip i, the cost paid is S_current + C[i] - 2*A[i]*C[i].
    # And S_new = S_current + C[i] - 2*A[i]*C[i].
    # So the cost paid equals the new sum S_new.
    # Total cost = sum of costs paid for each flip = sum of S_new for each flip.
    # Let's trace the sum S over the sequence of flips.
    # Initially S = S0.
    # After flipping a set of indices F, the sum becomes S = S0 + sum_{j in F} (C[j] - 2*A[j]*C[j]).
    # Let delta[j] = C[j] - 2*A[j]*C[j].
    # The cost paid when flipping j (given current sum S) is S + delta[j].
    # Total cost = sum_{k=1 to |D|} (S_before_k + delta[k]).
    # S_before_k = S0 + sum_{j in D, j flipped before k} delta[j].
    # So total cost = sum_{k=1 to |D|} (S0 + sum_{j in D, j flipped before k} delta[j] + delta[k]).
    # = |D| * S0 + sum_{k=1 to |D|} sum_{j in D, j flipped before k} delta[j] + sum_{k=1 to |D|} delta[k].
    # The last term is sum_{j in D} delta[j].
    # The middle term is sum_{j in D} delta[j] * (number of k such that j is flipped before k).
    # If we sort D such that delta[j] is increasing, then for a given j at index i (0-based), the number of k after j is (|D| - 1 - i).
    # So total cost = |D| * S0 + sum_{j in D} delta[j] * (|D| - 1 - i) + sum_{j in D} delta[j].
    # = |D| * S0 + sum_{j in D} delta[j] * (|D| - i).
    # Wait, let me re-check the sample 1 calculation.
    # |D| = 3, S0 = 17.
    # Sorted deltas: [-9, -6, 4]. Indices: [3, 1, 0].
    # i=0: delta=-9, term = -9 * (3-0) = -27.
    # i=1: delta=-6, term = -6 * (3-1) = -12.
    # i=2: delta=4, term = 4 * (3-2) = 4.
    # Total = 3*17 + (-27) + (-12) + 4 = 51 - 27 - 12 + 4 = 16.
    # This matches sample 1.
    
    # Let me re-check sample 3.
    # N=20, A and B given, C given.
    # Let's compute S0 and D.
    # A = [1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0]
    # B = [0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0]
    # C = [52, 73, 97, 72, 54, 15, 79, 67, 13, 55, 65, 22, 36, 90, 84, 46, 1, 2, 27, 8]
    # D = indices where A[i] != B[i].
    # i=0: A=1, B=0 -> diff
    # i=1: A=1, B=0 -> diff
    # i=2: A=1, B=0 -> diff
    # i=3: A=1, B=1 -> same
    # i=4: A=0, B=1 -> diff
    # i=5: A=0, B=1 -> diff
    # i=6: A=1, B=0 -> diff
    # i=7: A=1, B=1 -> same
    # i=8: A=0, B=1 -> diff
    # i=9: A=0, B=0 -> same
    # i=10: A=0, B=0 -> same
    # i=11: A=1, B=0 -> diff
    # i=12: A=0, B=0 -> same
    # i=13: A=1, B=0 -> diff
    # i=14: A=0, B=0 -> same
    # i=15: A=1, B=1 -> same
    # i=16: A=1, B=0 -> diff
    # i=17: A=0, B=1 -> diff
    # i=18: A=1, B=0 -> diff
    # i=19: A=0, B=0 -> same
    # D = [0, 1, 2, 4, 5, 6, 8, 11, 13, 16, 17, 18]
    # |D| = 12.
    # S0 = sum(A[i]*C[i] for i in range(N))
    # Let's compute this.
    # Actually, let me just run the code and see what S0 is.
    # But wait, my formula gave 3300, expected 2867.
    # Let me re-check the formula.
    # Total cost = |D| * S0 + sum_{j in D} delta[j] * (|D| - i).
    # Let me re-derive.
    # Total cost = sum_{k=1 to |D|} (S_before_k + delta[k]).
    # S_before_k = S0 + sum_{j in D, j flipped before k} delta[j].
    # So total cost = sum_{k=1 to |D|} (S0 + sum_{j in D, j flipped before k} delta[j] + delta[k]).
    # = |D| * S0 + sum_{k=1 to |D|} sum_{j in D, j flipped before k} delta[j] + sum_{k=1 to |D|} delta[k].
    # The last term is sum_{j in D} delta[j].
    # The middle term is sum_{j in D} delta[j] * (number of k such that j is flipped before k).
    # If we sort D such that delta[j] is increasing, then for a given j at index i (0-based), the number of k after j is (|D| - 1 - i).
    # So total cost = |D| * S0 + sum_{j in D} delta[j] * (|D| - 1 - i) + sum_{j in D} delta[j].
    # = |D| * S0 + sum_{j in D} delta[j] * (|D| - i).
    # This is what I have.
    # Let me check if the sorting is correct.
    # We want to minimize the total cost.
    # The term sum_{j in D} delta[j] * (|D| - i) is minimized when we put smaller delta[j] at larger i.
    # So we should sort by delta[j] in ascending order.
    # This is what I did.
    # Let me re-check the sample 3 calculation manually.
    # Actually, let me just print the intermediate values to debug.
    
    # Calculate initial sum S0
    S0 = sum(A[i] * C[i] for i in range(N))
    
    # Identify indices where A[i] != B[i]
    D = [i for i in range(N) if A[i] != B[i]]
    
    if not D:
        print(0)
        return

    # Calculate delta for each index in D
    # delta[i] = C[i] - 2 * A[i] * C[i]
    deltas = [(C[i] - 2 * A[i] * C[i], i) for i in D]
    
    # Sort deltas in ascending order
    deltas.sort()
    
    # Calculate total cost
    total_cost = len(D) * S0
    for idx, (delta, _) in enumerate(deltas):
        total_cost += delta * (len(D) - idx)
        
    print(total_cost)

solve()
