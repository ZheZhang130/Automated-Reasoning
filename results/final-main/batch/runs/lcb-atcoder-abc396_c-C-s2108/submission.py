import sys
from typing import List

def solve() -> None:
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    it = iter(input_data)
    N = int(next(it))
    M = int(next(it))
    
    B = []
    for _ in range(N):
        B.append(int(next(it)))
    
    W = []
    for _ in range(M):
        W.append(int(next(it)))
    
    # Sort both arrays in descending order
    B.sort(reverse=True)
    W.sort(reverse=True)
    
    # Prefix sums for B and W
    # We'll compute them on the fly to save memory, but given constraints, precomputing is fine too.
    # Let's just iterate.
    
    # We need to choose k black balls and j white balls such that k >= j.
    # For a fixed k, we want to maximize sum(B[0..k-1]) + max(sum(W[0..j-1])) for 0 <= j <= min(k, M).
    # Since W is sorted descending, the prefix sums are not necessarily increasing if values are negative.
    # However, we want the maximum prefix sum for any valid j.
    # So for each k, we consider j from 0 to min(k, M).
    # As k increases, the range of j increases by at most 1.
    
    # Let's maintain the maximum prefix sum of W seen so far for valid j.
    # But note: the maximum prefix sum might not be at the current j, it could be at a previous j.
    # So we maintain a running maximum of the prefix sums of W.
    
    # However, the constraint is j <= k. So when we are at k, we can include W[0]...W[k-1] (if k<=M).
    # But we can also choose to stop earlier. So we need the max prefix sum of W for indices 0 to min(k, M).
    
    # Let's precompute the prefix sums of W and then for each k, take the max of prefix sums up to min(k, M).
    # But note: the prefix sum array for W might have negative values, so the max might be at an earlier index.
    
    # Actually, we can do this without precomputing all prefix sums if we are careful, but precomputing is O(M) which is fine.
    
    # Let's compute prefix sums for W.
    # W_prefix[i] = sum(W[0]...W[i-1]) for i from 0 to M.
    # W_prefix[0] = 0.
    
    W_prefix = [0] * (M + 1)
    current = 0
    for i in range(M):
        current += W[i]
        W_prefix[i+1] = current
    
    # Now, for each k from 0 to N:
    #   We can choose j from 0 to min(k, M).
    #   The best white sum for this k is max(W_prefix[0], W_prefix[1], ..., W_prefix[min(k, M)]).
    #   But note: as k increases, the set of allowed j increases. So we can maintain a running max for W_prefix.
    
    # However, the running max for W_prefix up to min(k, M) is not simply the previous running max plus the new element,
    # because the new element might be negative. But we are taking the max over the range [0, min(k, M)].
    # So we can maintain a variable `max_white` which is the max of W_prefix[0]...W_prefix[min(k, M)].
    # When k increases, if k <= M, then we consider W_prefix[k] (which is the new element) and update max_white.
    # If k > M, then min(k, M) = M, so we don't add any new element to the range, so max_white remains the same.
    
    # But note: the range for j is [0, min(k, M)]. So when k increases from k to k+1:
    #   If k+1 <= M, then the new j we can consider is j = k+1 (which corresponds to W_prefix[k+1]).
    #   So we update max_white = max(max_white, W_prefix[k+1]).
    #   If k+1 > M, then we don't add any new j, so max_white remains the same.
    
    # However, we must start k from 0.
    # k=0: j can only be 0. max_white = W_prefix[0] = 0.
    # k=1: j can be 0 or 1. max_white = max(W_prefix[0], W_prefix[1]).
    # ...
    
    # So we can iterate k from 0 to N.
    # But note: the problem says "choose zero or more balls", so k=0 is allowed (choose 0 black and 0 white).
    # However, the condition is: number of black balls >= number of white balls.
    # So if we choose 0 black balls, we must choose 0 white balls.
    
    # Let's compute the prefix sums for B as well? Actually, we can just accumulate as we go.
    
    # Initialize:
    #   current_black_sum = 0
    #   max_white = 0 (for k=0, j=0)
    #   best_total = 0 (for k=0, j=0)
    
    # But note: we must consider k from 0 to N.
    # However, the problem says "choose zero or more", so k=0 is allowed.
    
    # But wait: the sample outputs include cases where the answer is 0 (choosing no balls).
    # So we initialize best_total = 0.
    
    # However, note: if we choose k black balls, we must choose j white balls with j <= k and j <= M.
    # And we want to maximize the sum.
    
    # Let's iterate k from 0 to N.
    # But note: for k=0, we have j=0 only.
    # Then for k=1, j can be 0 or 1.
    # ...
    
    # We can do:
    #   current_black_sum = 0
    #   max_white = 0
    #   best_total = 0
    #   for k in range(1, N+1):
    #       current_black_sum += B[k-1]   # because B is 0-indexed, so the k-th black ball is at index k-1
    #       if k <= M:
    #           max_white = max(max_white, W_prefix[k])
    #       best_total = max(best_total, current_black_sum + max_white)
    #
    # But wait: what about k=0? We already have best_total=0 for k=0.
    # However, the loop above starts at k=1. So we need to consider k=0 separately? 
    # Actually, for k=0, current_black_sum=0, max_white=0, so total=0, which is already in best_total.
    # But note: the loop for k from 1 to N does not consider k=0. So we should initialize best_total=0 and then run the loop.
    # However, the loop for k=1 to N will update best_total with k=1,2,...,N.
    # But what if the maximum is at k=0? Then best_total=0 is correct.
    # However, note: for k>=1, we might have a negative current_black_sum, but if max_white is positive enough, it might be better than 0.
    # But we also have the option of k=0, which gives 0.
    # So we should initialize best_total=0 and then run the loop for k from 1 to N.
    # But wait: the loop for k=1 to N does not consider the possibility of having k=0 and j=0? 
    # Actually, we start with best_total=0, which corresponds to k=0, j=0.
    # Then for k=1, we consider j=0 and j=1.
    # So it's correct.
    
    # However, there is a catch: the max_white for a given k is the maximum of W_prefix[0]...W_prefix[min(k, M)].
    # But in the loop, when we are at k, we update max_white by including W_prefix[k] (if k<=M).
    # But note: max_white should be the maximum over j in [0, min(k, M)].
    # So when we move from k-1 to k, if k<=M, then we add W_prefix[k] to the set of candidates, and we take the max.
    # If k>M, then the set of candidates doesn't change (still [0, M]), so max_white remains the same.
    # So the update is correct.
    
    # But note: the prefix sum array W_prefix is 0-indexed: W_prefix[i] is the sum of the first i white balls.
    # So for k=1, we consider j=0 and j=1. W_prefix[0]=0, W_prefix[1]=W[0].
    # So max_white = max(0, W_prefix[1]).
    # Then for k=2, we consider j=0,1,2. So we update max_white = max(max_white, W_prefix[2]).
    # This is correct.
    
    # However, we must be cautious: the problem says "choose zero or more", so k=0 is allowed.
    # Our initialization best_total=0 covers k=0.
    
    # But note: the loop for k from 1 to N: 
    #   We add B[k-1] to current_black_sum.
    #   Then if k<=M, we update max_white with W_prefix[k].
    #   Then we update best_total.
    
    # However, what if k > M? Then we don't update max_white, but we still update best_total with current_black_sum + max_white.
    # This is correct because for k>M, the maximum white sum we can get is the same as for k=M (since we can't choose more than M white balls).
    # And max_white is already the maximum over j in [0, M] from the previous steps.
    
    # So the algorithm is:
    #   Sort B descending, W descending.
    #   Compute W_prefix[0..M].
    #   current_black_sum = 0
    #   max_white = 0
    #   best_total = 0
    #   for k in range(1, N+1):
    #       current_black_sum += B[k-1]
    #       if k <= M:
    #           max_white = max(max_white, W_prefix[k])
    #       best_total = max(best_total, current_black_sum + max_white)
    #   print(best_total)
    
    # But wait: what if the best solution is with k=0? Then best_total=0 is correct.
    # However, note: the problem says "choose zero or more", so k=0 is allowed and gives 0.
    # But what if all B_i and W_j are negative? Then the best is 0 (choosing nothing).
    # Our algorithm: 
    #   k=0: best_total=0.
    #   k=1: current_black_sum = B[0] (negative), max_white = max(0, W_prefix[1]) (which might be negative or positive).
    #         But if W_prefix[1] is negative, then max_white remains 0 (from k=0).
    #         Then total = B[0] + 0, which is negative, so best_total remains 0.
    #   So it works.
    
    # However, note: max_white is initialized to 0, which corresponds to j=0 (choosing 0 white balls).
    # And for k=0, we have j=0 only, so max_white=0.
    # For k>=1, we can have j from 0 to min(k, M).
    # So the algorithm is correct.
    
    # But note: the constraints say N, M up to 200,000, so O(N+M) is acceptable.
    
    # Let's code accordingly.
    
    current_black_sum = 0
    max_white = 0
    best_total = 0
    
    # We iterate k from 1 to N (inclusive)
    for k in range(1, N+1):
        current_black_sum += B[k-1]
        if k <= M:
            # W_prefix[k] is the sum of the first k white balls (which are the largest k)
            if W_prefix[k] > max_white:
                max_white = W_prefix[k]
        # Update best_total
        total = current_black_sum + max_white
        if total > best_total:
            best_total = total
            
    print(best_total)

if __name__ == '__main__':
    solve()
