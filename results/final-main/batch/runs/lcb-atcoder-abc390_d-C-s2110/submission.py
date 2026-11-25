import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    N = int(next(iterator))
    A = [int(next(iterator)) for _ in range(N)]

    # Precompute sums for all masks
    # mask_sum[mask] = sum of A[i] for all i in mask
    mask_sum = [0] * (1 << N)
    for mask in range(1, 1 << N):
        # Find the lowest set bit
        lsb = mask & -mask
        # The index of the bit (0-based)
        idx = (lsb.bit_length() - 1)
        # The sum of the rest of the mask
        rest_mask = mask ^ lsb
        mask_sum[mask] = mask_sum[rest_mask] + A[idx]

    # DFS to enumerate partitions
    # We use a recursive approach where we always pick the smallest index
    # that is still in the current mask, and then try all subsets of the
    # remaining indices to form the next group.
    
    # To avoid deep recursion issues and for clarity, we can use an iterative
    # approach with a stack, but given N <= 12, recursion depth is at most 12.
    
    results = set()
    
    # We'll use a recursive function
    # current_mask: bitmask of indices that are still available to be partitioned
    # current_xor: current XOR sum of the groups formed so far
    
    # However, the standard way to enumerate partitions is:
    # Start with all indices available.
    # Pick the smallest index i that is in current_mask.
    # Then, form a group that includes i and any subset of the other available indices.
    # Recurse with the remaining indices.
    
    # We can implement this with a recursive function.
    
    def dfs(current_mask, current_xor):
        if current_mask == 0:
            results.add(current_xor)
            return
        
        # Find the smallest index in current_mask
        # We can use (current_mask & -current_mask) to get the lowest bit
        lsb = current_mask & -current_mask
        # The index of this bit (0-based)
        i = (lsb.bit_length() - 1)
        
        # The rest of the mask (excluding i)
        rest_mask = current_mask ^ lsb
        
        # Try all submasks of rest_mask
        # We iterate through all submasks of rest_mask
        submask = rest_mask
        while True:
            # The group is formed by (submask | lsb)
            group_mask = submask | lsb
            group_sum = mask_sum[group_mask]
            
            # Recurse with the remaining mask
            dfs(current_mask ^ group_mask, current_xor ^ group_sum)
            
            # Move to the next submask
            if submask == 0:
                break
            submask = (submask - 1) & rest_mask

    dfs((1 << N) - 1, 0)
    
    print(len(results))

if __name__ == "__main__":
    solve()
