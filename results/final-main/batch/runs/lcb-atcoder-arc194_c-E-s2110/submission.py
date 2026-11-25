import sys

def solve():
    data = sys.stdin.read().split()
    it = iter(data)
    N = int(next(it))
    A = [int(next(it)) for _ in range(N)]
    B = [int(next(it)) for _ in range(N)]
    C = [int(next(it)) for _ in range(N)]

    # For each position, we need to decide whether to flip it or not.
    # Let x_i = 1 if we flip position i, 0 otherwise.
    # After flips, A[i] becomes A[i] ^ x_i.
    # We want A[i] ^ x_i = B[i], so x_i = A[i] ^ B[i].
    # 
    # But we can flip multiple times. Let's think of it as:
    # We start with A, and we want to reach B.
    # Each flip operation: choose i, flip A[i], pay sum of current A (after flip).
    #
    # Key insight: The order of flips matters.
    # If we flip a position twice, it's equivalent to not flipping it at all, but we pay extra.
    # So we should flip each position at most once.
    #
    # But wait, the sample explanation shows flipping positions in a specific order.
    # Let's re-read the problem:
    # "First, choose an integer i... and flip the value of A_i"
    # "Then, pay sum_{k=1}^N A_k C_k yen as the cost of this operation."
    #
    # So each operation: flip one position, then pay the sum of all current A values (weighted by C).
    #
    # Let's think of this differently:
    # We want to transform A to B.
    # Let S be the set of indices where A[i] = 1.
    # Let T be the set of indices where B[i] = 1.
    # We need to transform S to T.
    #
    # When we flip index i:
    #   If i in S: new S = S \ {i}, cost = sum(C[j] for j in S \ {i})
    #   If i not in S: new S = S U {i}, cost = sum(C[j] for j in S U {i})
    #
    # Let's denote:
    #   total = sum(C[j] for j in S)
    #   cost(i) = total - C[i] if i in S else total + C[i]
    #
    # We want to find a sequence of flips to go from S to T with minimum total cost.
    #
    # Let U = S \ T (positions that are 1 in A but should be 0 in B)
    # Let V = T \ S (positions that are 0 in A but should be 1 in B)
    # Let W = S ∩ T (positions that are 1 in both)
    # Let Z = (S ∪ T)^c (positions that are 0 in both)
    #
    # We need to flip all positions in U (from 1 to 0).
    # We need to flip all positions in V (from 0 to 1).
    # We don't need to flip positions in W or Z.
    #
    # But the order matters!
    # When we flip a position in U (1->0), the cost is total - C[i].
    # When we flip a position in V (0->1), the cost is total + C[i].
    #
    # To minimize total cost, we want to:
    # 1. Flip positions in U when total is as small as possible.
    # 2. Flip positions in V when total is as small as possible.
    #
    # Strategy:
    # - First, flip all positions in V (0->1) in ascending order of C[i].
    #   This increases total, but we want to do it when total is small.
    # - Then, flip all positions in U (1->0) in descending order of C[i].
    #   This decreases total, and we want to do it when total is large (to minimize the reduction).
    #
    # Wait, that's not right. Let me reconsider.
    #
    # Actually, the cost of flipping i is:
    #   If i in S: cost = total - C[i]
    #   If i not in S: cost = total + C[i]
    #
    # So flipping a position in S (1->0) reduces the total by C[i] and costs (total - C[i]).
    # Flipping a position not in S (0->1) increases the total by C[i] and costs (total + C[i]).
    #
    # Let's think of the total cost as:
    #   sum over all flips of (current total after flip)
    #
    # If we flip a position in S (1->0):
    #   new_total = total - C[i]
    #   cost = new_total = total - C[i]
    #
    # If we flip a position not in S (0->1):
    #   new_total = total + C[i]
    #   cost = new_total = total + C[i]
    #
    # So the cost of flipping i is:
    #   total + (C[i] if i not in S else -C[i])
    #
    # Let's denote:
    #   base_total = sum(C[j] for j in S)
    #   For a flip of i in S: cost = base_total - C[i]
    #   For a flip of i not in S: cost = base_total + C[i]
    #
    # But base_total changes as we flip!
    #
    # Let's think of it as:
    #   Total cost = sum over all flips of (current total after flip)
    #              = sum over all flips of (initial_total + sum of C[j] for j flipped so far that are now 1)
    #
    # Actually, let's think of it differently.
    # Let x_i = 1 if we flip position i, 0 otherwise.
    # After all flips, A[i] = A[i] ^ x_i = B[i].
    # So x_i = A[i] ^ B[i].
    #
    # But we can flip in any order.
    # Let's say we flip positions in some order p_1, p_2, ..., p_k.
    # The cost of flipping p_j is: sum(C[i] for i where A[i] = 1 after j-1 flips).
    #
    # Let's denote:
    #   S_0 = {i | A[i] = 1} (initial set of 1s)
    #   S_j = S_{j-1} \ {p_j} if p_j in S_{j-1} else S_{j-1} U {p_j}
    #   cost_j = sum(C[i] for i in S_j)
    #   Total cost = sum_{j=1}^k cost_j
    #
    # We want to minimize this.
    #
    # Key observation:
    #   Total cost = sum_{j=1}^k sum_{i in S_j} C[i]
    #              = sum_{i} C[i] * (number of times i is in S_j for j=1..k)
    #
    # For a position i:
    #   If i in S_0 and i not in T (need to flip 1->0):
    #     i is in S_0, then not in S_1 (after first flip of i), then not in any subsequent S_j.
    #     So i is in S_0, S_1, ..., S_{j-1} where j is the step when we flip i.
    #     Number of times i is in S_j = j (if we flip i at step j).
    #   If i not in S_0 and i in T (need to flip 0->1):
    #     i is not in S_0, ..., S_{j-1}, then in S_j (after flipping i at step j).
    #     So i is in S_j, S_{j+1}, ..., S_k.
    #     Number of times i is in S_j = k - j + 1.
    #   If i in S_0 and i in T (don't need to flip):
    #     i is in S_0, ..., S_k.
    #     Number of times i is in S_j = k + 1.
    #   If i not in S_0 and i not in T (don't need to flip):
    #     i is not in S_0, ..., S_k.
    #     Number of times i is in S_j = 0.
    #
    # Wait, this is getting complicated. Let me think of a simpler approach.
    #
    # Actually, let's just simulate the optimal order:
    # 1. First, flip all positions that need 0->1 (V) in ascending order of C[i].
    # 2. Then, flip all positions that need 1->0 (U) in descending order of C[i].
    #
    # But we also need to consider positions that are already correct (W and Z).
    # For positions in W (A[i]=1, B[i]=1), we don't need to flip them.
    # For positions in Z (A[i]=0, B[i]=0), we don't need to flip them.
    #
    # But wait, the sample explanation shows flipping positions that are not mismatches?
    # No, in sample 1, all flipped positions are mismatches.
    #
    # Let me re-read the sample explanation:
    # "First, flip A_4. Now, A = (0, 1, 1, 0)."
    # A_4 is index 3 (0-indexed), which is a mismatch (A[3]=1, B[3]=0).
    # "Next, flip A_2. Now, A = (0, 0, 1, 0)."
    # A_2 is index 1, which is a mismatch (A[1]=1, B[1]=0).
    # "Finally, flip A_1. Now, A = (1, 0, 1, 0), which matches B."
    # A_1 is index 0, which is a mismatch (A[0]=0, B[0]=1).
    #
    # So all flipped positions are mismatches.
    #
    # The order is: flip 1->0 at i=3 (C=9), then 1->0 at i=1 (C=6), then 0->1 at i=0 (C=4).
    # This is: 1->0 in descending order of C[i], then 0->1 in ascending order of C[i].
    #
    # But my current code does: 1->0 in descending order, then 0->1 in ascending order.
    # Let me check the cost calculation again.
    #
    # Initial: A = [0,1,1,1], C = [4,6,2,9]
    # current_sum = 6+2+9 = 17 (sum of C[i] for i where A[i]=1)
    #
    # flip_10 = [(9, 3), (6, 1)] (sorted descending)
    # flip_01 = [(4, 0)] (sorted ascending)
    #
    # Do 1->0 flips first:
    #   Flip i=3: current_sum = 17 - 9 = 8, total_cost = 8
    #   Flip i=1: current_sum = 8 - 6 = 2, total_cost = 8 + 2 = 10
    # Do 0->1 flips next:
    #   Flip i=0: current_sum = 2 + 4 = 6, total_cost = 10 + 6 = 16
    #
    # This matches the sample output!
    #
    # So why is case 03 failing?
    # Let me check case 03 manually.
    #
    # Actually, I think the issue is that we need to consider the initial sum correctly.
    # Let me re-implement with a cleaner approach.

    # Calculate initial sum of C[i] for positions where A[i] = 1
    current_sum = sum(C[i] for i in range(N) if A[i] == 1)
    
    # Separate into lists
    flip_10 = [(C[i], i) for i in range(N) if A[i] == 1 and B[i] == 0]
    flip_01 = [(C[i], i) for i in range(N) if A[i] == 0 and B[i] == 1]
    
    # Sort flip_10 descending by cost
    flip_10.sort(key=lambda x: x[0], reverse=True)
    # Sort flip_01 ascending by cost
    flip_01.sort(key=lambda x: x[0])
    
    total_cost = 0
    
    # Do 1->0 flips first
    for cost, i in flip_10:
        current_sum -= cost
        total_cost += current_sum
    
    # Do 0->1 flips next
    for cost, i in flip_01:
        current_sum += cost
        total_cost += current_sum
    
    print(total_cost)

if __name__ == "__main__":
    solve()
