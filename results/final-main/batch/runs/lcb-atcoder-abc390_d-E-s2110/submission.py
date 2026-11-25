import sys
from functools import lru_cache

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    A = list(map(int, input_data[1:N+1]))
    
    # We need to find all possible XOR sums of the final bag contents.
    # Operation: merge two bags (A, B) -> (0, A+B)
    # This means we can partition the original stones into groups, 
    # where each group's stones are summed into one bag.
    # The XOR sum is the XOR of the sums of these groups.
    # Since we can merge any two bags, we can achieve any partition of the original bags.
    # For a partition, the XOR sum is the XOR of the sum of each group.
    # Note: The sum of a group is the sum of A_i for i in that group.
    # The XOR sum of the partition is XOR_{groups} (sum(group)).
    
    # However, note that the problem allows merging any two bags. 
    # This means we can form any partition of the set of bags.
    # But wait: the operation is "move all stones from bag A into bag B".
    # This implies that one bag becomes empty. So we are effectively merging sets of bags.
    # The final state is a partition of the original bags into non-empty sets,
    # and each set's stones are summed into one bag (the others in the set are empty).
    # The XOR sum is the XOR of the sums of these sets.
    
    # Let S be the total sum of all A_i.
    # For any partition, let the sums of the groups be s1, s2, ..., sk.
    # Then s1 + s2 + ... + sk = S.
    # We want to count the number of distinct values of s1 ^ s2 ^ ... ^ sk.
    
    # However, note: the problem does not require the partition to be into non-empty sets?
    # Actually, every bag must be in exactly one group (either kept or merged into another).
    # So yes, it is a partition of the set of indices {1, ..., N}.
    
    # But N is up to 12, so we can iterate over all partitions? 
    # The number of partitions of a set of size N is the Bell number B_N.
    # B_12 = 4213597, which is too large to iterate.
    
    # Alternate approach:
    # Notice that the XOR sum of the final bags is:
    #   XOR_{groups} (sum(group))
    # But note: (sum(group)) mod 2 = (XOR_{i in group} A_i) mod 2? Not exactly.
    # However, we can use dynamic programming or recursion with memoization.
    
    # But note: the constraints on A_i are up to 10^17, so we cannot use the values as states.
    # However, the number of groups is at most N, and the partition is over N items.
    
    # Insight: 
    # The XOR sum of the final configuration is:
    #   X = XOR_{groups} (sum(group))
    # But note: sum(group) = sum_{i in group} A_i.
    # So X = XOR_{groups} (sum_{i in group} A_i)
    # However, this is not linear. 
    # But observe: 
    #   X = (sum_{i in group1} A_i) ^ (sum_{i in group2} A_i) ^ ... 
    # This is not the same as sum_{i} A_i.
    
    # Alternate Insight:
    # Consider the bits. For each bit position, the contribution of a number A_i to the XOR sum
    # depends on how many groups it is in? Actually, no: each A_i is in exactly one group.
    # But the value of the group sum is the sum of A_i in that group.
    # The XOR of the group sums is not simply related to the bits of individual A_i.
    
    # However, note that the problem is equivalent to: 
    #   We can assign each A_i to a group. The groups are unlabeled, but the XOR sum is over the groups.
    #   But the groups are formed by merging, so the order of groups doesn't matter for the XOR sum? 
    #   Actually, the XOR sum is commutative, so the order of groups doesn't matter.
    #   But the grouping matters: which A_i are together.
    
    # We can use recursion: 
    #   Let dp(mask) = set of possible XOR sums for the subset of bags represented by mask.
    #   But we need to partition the entire set. 
    #   However, the state would be the mask of bags that have been assigned to groups? 
    #   Actually, we can build the partition by adding one group at a time.
    #   But the groups are unordered, so we can enforce an order (e.g., the smallest index in the group).
    
    # Steps:
    #   We want to partition the set {0, ..., N-1} into non-empty subsets.
    #   For each partition, compute the XOR of the sums of the subsets.
    #   We want the number of distinct XOR values.
    
    # We can use recursion with memoization on the mask of remaining bags.
    #   Let f(mask) = set of possible XOR sums for the partition of the subset 'mask' (where mask is the set of bags that are still to be partitioned).
    #   But note: we are building the partition from the bottom up? 
    #   Actually, we can do:
    #       f(mask) = { XOR( sum(group) for group in partition of mask) }
    #   How to compute f(mask)?
    #       We can iterate over all non-empty submasks 'sub' of 'mask' that contain the smallest bit in 'mask' (to avoid duplicates).
    #       Then: f(mask) = { x ^ s for x in f(mask \ sub) for s in [sum(A[i] for i in sub)] }
    #       But note: the base case is f(0) = {0}.
    #   However, the state is the mask, and we only consider submasks that include the lowest bit of mask.
    #   This is a standard way to count partitions (using the lowest bit to avoid overcounting).
    
    # Steps for DP:
    #   Let mask go from 0 to (1<<N)-1.
    #   For each mask, let i = the lowest bit set in mask.
    #   Then iterate over all submasks 'sub' of mask such that i is in sub and sub is non-empty.
    #   Then the rest is mask ^ sub.
    #   But note: we must have processed mask ^ sub before mask? 
    #   Actually, we can iterate mask from 0 to (1<<N)-1, and for each mask, we consider the lowest bit i.
    #   Then we iterate over all submasks 'sub' of mask that contain i.
    #   Then the rest is mask ^ sub, which is a smaller mask (since we remove at least i).
    #   So we can do:
    #       dp[mask] = set()
    #       i = lowest bit of mask
    #       for sub in submasks of mask that contain i:
    #           s = sum(A[j] for j in sub)
    #           rest_xor = dp[mask ^ sub]   # but wait, we need to have computed dp[mask^sub] already?
    #           Actually, mask^sub is a proper subset of mask, so if we iterate mask in increasing order, it's fine.
    #           However, note: mask^sub might be 0, which we set to {0}.
    #       Then dp[mask] = { x ^ s for x in dp[mask^sub] for each sub }
    #   But wait: the partition of mask is: one group is 'sub', and the rest is partitioned arbitrarily.
    #   However, the XOR sum of the entire partition is: (XOR sum of the groups in the rest) ^ (sum of sub)
    #   So yes, we do: x ^ s, where x is from dp[mask^sub].
    
    # However, note: the base case: dp[0] = {0}.
    # But mask=0: no bags, so XOR sum is 0.
    
    # But the problem: the entire set must be partitioned. So we want dp[(1<<N)-1].
    
    # Steps:
    #   Precompute the sum for each submask? There are 2^N submasks, and N<=12, so 2^12 = 4096, which is small.
    #   We can precompute the sum for each mask: 
    #       mask_sum[mask] = sum(A[i] for i in mask)
    #   Then:
    #       dp = [set() for _ in range(1<<N)]
    #       dp[0] = {0}
    #       for mask in range(1, 1<<N):
    #           i = (mask & -mask).bit_length() - 1   # but note: bit_length() of 1 is 1, so we want the index.
    #           Actually, we can do: 
    #               i = 0
    #               temp = mask
    #               while not (temp & 1):
    #                   temp >>= 1
    #                   i += 1
    #           But a simpler way: 
    #               i = (mask & -mask).bit_length() - 1 doesn't work because (mask & -mask) is a power of two, 
    #               and bit_length() of 1 is 1, so index 0. But we want the index of the bit.
    #           Alternatively, we can precompute the lowest bit index for each mask? 
    #           Or: 
    #               i = 0
    #               if mask & 1: i = 0
    #               else: 
    #                   # find the first bit
    #                   pass
    #           Actually, we can do:
    #               i = (mask & -mask).bit_length() - 1
    #               But note: (mask & -mask) is the lowest set bit as a power of two. 
    #               For example, if mask=6 (binary 110), then mask & -mask = 2 (binary 10), and 2.bit_length()=2, so i=1. Correct.
    #               However, in Python, (mask & -mask).bit_length() - 1 gives the index (0-indexed) of the lowest set bit.
    #           So:
    #               low_bit = mask & -mask
    #               i = low_bit.bit_length() - 1
    #           Then iterate over all submasks 'sub' of mask that contain i.
    #           How to iterate? 
    #               We can iterate over all submasks of mask, and then check if i is in sub.
    #               But note: we can iterate by: 
    #                   sub = mask
    #                   while True:
    #                       # process sub
    #                       if (sub >> i) & 1:
    #                           ...
    #                       if sub == 0: break
    #                       sub = (sub - 1) & mask
    #               But this iterates in decreasing order, and we need to check if i is in sub.
    #           Alternatively, we can iterate over all submasks of mask, and then check if the i-th bit is set.
    #           But note: the number of submasks is 2^(popcount(mask)), which is at most 2^12, so it's acceptable.
    #           However, we can optimize: 
    #               We only consider submasks that contain i. 
    #               So: sub = (mask without the bits above i) | (any subset of the bits above i) | {i}
    #               Actually, we can let:
    #                   rest = mask ^ (1<<i)
    #                   for sub_rest in submasks of rest:
    #                       sub = sub_rest | (1<<i)
    #               Then iterate over sub_rest from 0 to rest, but we need to iterate in a way that we get all submasks.
    #               We can do: 
    #                   sub_rest = rest
    #                   while True:
    #                       sub = sub_rest | (1<<i)
    #                       ...
    #                       if sub_rest == 0: break
    #                       sub_rest = (sub_rest - 1) & rest
    #           This is efficient.
    
    # Implementation:
    #   Precompute mask_sum for all masks? Actually, we can compute on the fly or precompute.
    #   Since N is small, we can precompute an array `mask_sum` of size 1<<N.
    
    # Steps:
    #   Read N and A.
    #   Precompute mask_sum for all masks from 0 to (1<<N)-1.
    #   Initialize dp[0] = {0}, and dp[mask] = set() for mask>0.
    #   Iterate mask from 1 to (1<<N)-1:
    #       i = (mask & -mask).bit_length() - 1
    #       rest = mask ^ (1<<i)
    #       # iterate over all submasks of rest
    #       sub_rest = rest
    #       while True:
    #           sub = sub_rest | (1<<i)
    #           s = mask_sum[sub]
    #           rest_mask = mask ^ sub
    #           # rest_mask is mask without sub, which is a proper subset (since sub contains i, and rest_mask does not contain i)
    #           # and rest_mask < mask, so dp[rest_mask] is already computed.
    #           for x in dp[rest_mask]:
    #               dp[mask].add(x ^ s)
    #           if sub_rest == 0:
    #               break
    #           sub_rest = (sub_rest - 1) & rest
    #   Then the answer is len(dp[(1<<N)-1])
    
    # However, note: the base case dp[0] = {0} is correct.
    # But when mask=0, we don't enter the loop.
    
    # Let's code accordingly.
    
    # Precompute mask_sum
    mask_sum = [0] * (1 << N)
    for mask in range(1 << N):
        s = 0
        for i in range(N):
            if mask & (1 << i):
                s += A[i]
        mask_sum[mask] = s
    
    # dp[mask] = set of possible XOR sums for the partition of the subset 'mask'
    dp = [set() for _ in range(1 << N)]
    dp[0] = {0}
    
    # Iterate mask from 1 to (1<<N)-1
    for mask in range(1, 1 << N):
        # Find the lowest set bit
        low_bit = mask & -mask
        i = low_bit.bit_length() - 1
        rest = mask ^ low_bit
        
        # Iterate over all submasks of rest
        sub_rest = rest
        while True:
            sub = sub_rest | low_bit
            rest_mask = mask ^ sub
            s = mask_sum[sub]
            for x in dp[rest_mask]:
                dp[mask].add(x ^ s)
            
            if sub_rest == 0:
                break
            sub_rest = (sub_rest - 1) & rest
    
    print(len(dp[(1 << N) - 1]))

if __name__ == '__main__':
    solve()
