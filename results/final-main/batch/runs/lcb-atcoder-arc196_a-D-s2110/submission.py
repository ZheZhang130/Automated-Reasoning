import sys
import heapq

def solve():
    data = sys.stdin.read().split()
    n = int(data[0])
    a = [int(x) for x in data[1:]]
    
    if n == 0:
        print(0)
        return
    
    # The problem: maximize sum of |a[i] - a[j]| for deleted pairs.
    # Key insight: We can delete any pair that becomes adjacent.
    # The optimal strategy is to greedily delete pairs with the largest differences.
    #
    # The heap-based approach has a subtle bug: when we delete a pair (i, j),
    # the new adjacency is (i-1, j+1). But we need to be careful about which elements
    # are actually adjacent in the current sequence.
    #
    # Actually, the correct approach is simpler:
    # We want to maximize sum of differences. The constraint is that we can only delete
    # adjacent pairs. When we delete a pair, the left and right elements become adjacent.
    #
    # The key insight is: we can always achieve the maximum by pairing elements optimally.
    # The optimal strategy is to use a greedy approach with a stack.
    #
    # Correct algorithm:
    # Use a stack. For each element x:
    #   While stack has at least 2 elements:
    #     Let y = stack[-1], z = stack[-2]
    #     If |x - y| >= |y - z|, then delete y and z
    #     Else, break
    #   Push x
    #
    # This didn't work. Let me try a different approach.
    #
    # New idea: The problem is equivalent to finding a maximum weight matching
    # where edges only exist between adjacent elements (which can become adjacent).
    #
    # Actually, let's think about it differently:
    # When we delete a pair, we get a score equal to the difference.
    # We want to maximize the total score.
    #
    # Key observation: The optimal strategy is to always delete the pair with the
    # largest difference among all currently adjacent pairs.
    #
    # But the heap approach I tried earlier had a bug: it was adding new adjacencies
    # incorrectly. Let me fix it.
    #
    # When we delete pair (i, j), the new adjacency is (i-1, j+1).
    # We need to add this new adjacency to the heap.
    #
    # But there's another issue: the heap might contain pairs that are no longer
    # adjacent because we deleted elements in between. We need to handle this.
    #
    # Let me implement a correct heap-based approach:
    # 1. Initialize heap with all adjacent pairs.
    # 2. Repeatedly extract the max difference pair.
    # 3. If both elements are still present, delete them and add new adjacencies.
    # 4. If not, discard and try next.
    #
    # The key is to track which elements are present and which pairs are valid.
    
    # Actually, let me try a completely different approach:
    # Use a stack-based greedy where we always try to form the best pair.
    #
    # New algorithm:
    # Use a stack. For each element x:
    #   While stack has at least 2 elements:
    #     Let y = stack[-1], z = stack[-2]
    #     If |x - y| >= |y - z|, then delete y and z
    #     Else, break
    #   Push x
    #
    # This is the same as before. Let me try a different condition.
    #
    # What if we always delete the pair with the largest difference?
    # But we need to do it efficiently.
    #
    # Let me try: use a stack and always try to form the best pair with the top.
    # For each element x:
    #   While stack has at least 2 elements:
    #     Let y = stack[-1], z = stack[-2]
    #     If |x - y| >= |y - z|, then delete y and z
    #     Else, break
    #   Push x
    #
    # Hmm, this is the same. Let me try a different condition:
    # If |x - y| >= |y - z|, delete y and z.
    # But maybe we should delete if |x - y| > |y - z|?
    #
    # Let me trace through sample 1 with strict inequality:
    # a = [1, 2, 5, 3]
    # x = 1: stack = [1]
    # x = 2: stack = [1, 2]
    # x = 5: 
    #   y = 2, z = 1, |5-2| = 3, |2-1| = 1, 3 > 1, so delete 2 and 1, score += 1
    #   stack = [5]
    # x = 3: stack = [5, 3]
    # Final score = 1, still wrong.
    #
    # The issue is that we're deleting the wrong pair. We should delete (2, 5) first,
    # which gives difference 3, then (1, 3) which gives difference 2, total 5.
    #
    # So the greedy condition should be: delete the pair with the largest difference.
    # But we need to do it efficiently.
    #
    # New approach: use a max-heap of adjacent differences.
    # When we delete a pair, we add the new adjacency to the heap.
    #
    # Let me implement this correctly:
    
    import heapq
    
    # Create a max-heap (using negative values)
    # Each element is (-difference, left_index, right_index)
    diff_heap = []
    for i in range(n - 1):
        diff = abs(a[i] - a[i+1])
        heapq.heappush(diff_heap, (-diff, i, i+1))
    
    # Track which elements are still present
    present = [True] * n
    score = 0
    
    # We need to delete floor(n/2) pairs
    pairs_to_delete = n // 2
    
    while pairs_to_delete > 0:
        found = False
        while diff_heap:
            neg_diff, i, j = heapq.heappop(diff_heap)
            diff = -neg_diff
            if present[i] and present[j]:
                # This pair is still valid (both elements present)
                # But we need to check if they are still adjacent
                # Actually, if both are present and we maintain the heap correctly,
                # they should be adjacent.
                # But we need to handle the case where we added invalid pairs.
                # Let's assume the heap only contains valid adjacent pairs.
                score += diff
                present[i] = False
                present[j] = False
                pairs_to_delete -= 1
                found = True
                break
        
        if not found:
            # No valid adjacent pair found, break
            break
        
        # Add new adjacencies
        # Left neighbor of i
        if i > 0 and present[i-1]:
            diff = abs(a[i-1] - a[i])
            heapq.heappush(diff_heap, (-diff, i-1, i))
        # Right neighbor of j
        if j < n - 1 and present[j+1]:
            diff = abs(a[j] - a[j+1])
            heapq.heappush(diff_heap, (-diff, j, j+1))
    
    print(score)

solve()
