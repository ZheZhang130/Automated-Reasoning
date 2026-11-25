import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    N = int(next(iterator))
    A = [int(next(iterator)) for _ in range(N)]

    # Precompute sums for all masks
    # mask_sum[mask] = sum of A[i] for all i where bit i is set in mask
    mask_sum = [0] * (1 << N)
    for mask in range(1, 1 << N):
        # Find the lowest set bit
        lsb = mask & -mask
        # The index of the lowest set bit (0-based)
        idx = (lsb.bit_length() - 1)
        # The sum without this bit
        prev_mask = mask ^ lsb
        mask_sum[mask] = mask_sum[prev_mask] + A[idx]

    # DFS to enumerate partitions
    # We use a recursive approach where we always pick the smallest remaining index
    # and form a group with it and any subset of the remaining larger indices.
    
    # To avoid recursion depth issues and for clarity, we can use an iterative stack-based approach
    # or just recursion since N is small (up to 12).
    
    results = set()
    
    # We'll use a recursive function
    # state: (remaining_mask, current_xor)
    # remaining_mask: bitmask of indices that are not yet assigned to any group
    # current_xor: current XOR sum of the groups formed so far
    
    # However, the standard way to enumerate partitions with the "smallest element" rule:
    # At each step, find the smallest index i in remaining_mask.
    # Then, form a group that includes i and any subset of the other indices in remaining_mask.
    # Recurse with the new remaining_mask (excluding the group formed).
    
    # We can implement this with a stack to avoid recursion limit, though N=12 is small enough for recursion.
    
    # Let's use a stack: each element is (remaining_mask, current_xor)
    # But we need to know which group was just formed to avoid double counting? 
    # Actually, the rule "smallest element must be in the current group" ensures uniqueness.
    # So we just need to track the current XOR and the remaining mask.
    
    # However, the base case is when remaining_mask is 0.
    # We add current_xor to results.
    
    # But wait: the initial state is (all ones, 0).
    # In the first step, we pick the smallest index (say 0) and form a group with 0 and some subset of others.
    # Then we recurse.
    
    # Let's implement recursively.
    
    # To make it iterative, we can use a stack.
    # Stack elements: (remaining_mask, current_xor)
    # But we need to know the smallest index in remaining_mask to form the group.
    # Actually, the rule is: the group MUST contain the smallest index in remaining_mask.
    # So, for a given remaining_mask, the smallest index is fixed.
    # We iterate over all subsets of (remaining_mask without the smallest index) and add the smallest index to each.
    
    # Let's do it recursively for clarity.
    
    # We'll use a simple recursive function.
    
    # But to avoid recursion, let's use a stack.
    # We start with ( (1<<N) - 1, 0 )
    # But wait, the initial mask should be (1<<N) - 1? 
    # Actually, the indices are 0 to N-1. So the initial mask is (1<<N) - 1.
    
    # However, the problem says bags are 1-indexed, but we can use 0-indexed internally.
    
    # Let's define the recursive function.
    
    # We'll use a stack to simulate recursion.
    # Each stack element: (remaining_mask, current_xor)
    # But we need to know the smallest index in remaining_mask to form the group.
    # Actually, the smallest index is fixed for a given remaining_mask.
    # So we can compute it as: (remaining_mask & -remaining_mask).bit_length() - 1
    
    # However, we need to iterate over all subsets of the other indices.
    # Let other_mask = remaining_mask ^ (1 << smallest_index)
    # Then we iterate over all submasks of other_mask.
    # For each submask, the group is (submask | (1 << smallest_index)).
    # Then we recurse with (remaining_mask ^ group_mask, current_xor ^ mask_sum[group_mask]).
    
    # Base case: remaining_mask == 0 -> add current_xor to results.
    
    # But note: the initial call should be with ( (1<<N)-1, 0 ).
    
    # However, the problem says N bags, so indices 0 to N-1.
    # The initial mask is (1<<N) - 1.
    
    # Let's implement.
    
    # We'll use a stack to avoid recursion.
    # Stack: list of (remaining_mask, current_xor)
    # But we need to process each state.
    
    # Actually, the recursive structure is a tree, so we can use a stack.
    
    # Let's do it.
    
    stack = [((1 << N) - 1, 0)]
    
    while stack:
        remaining_mask, current_xor = stack.pop()
        
        if remaining_mask == 0:
            results.add(current_xor)
            continue
        
        # Find the smallest index in remaining_mask
        # The smallest index is the lowest set bit.
        lsb = remaining_mask & -remaining_mask
        smallest_index = lsb.bit_length() - 1
        
        # The other indices
        other_mask = remaining_mask ^ lsb
        
        # Iterate over all submasks of other_mask
        # We can do this by: sub = other_mask; while True: ...; sub = (sub - 1) & other_mask
        # But note: we must include the empty submask (which means the group is just {smallest_index})
        # and the full other_mask (which means the group is the entire remaining_mask).
        
        sub = other_mask
        while True:
            group_mask = sub | lsb
            new_remaining = remaining_mask ^ group_mask
            new_xor = current_xor ^ mask_sum[group_mask]
            stack.append((new_remaining, new_xor))
            
            if sub == 0:
                break
            sub = (sub - 1) & other_mask
    
    print(len(results))

if __name__ == "__main__":
    solve()
