import sys
from functools import lru_cache

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    A = [int(data[i+1]) for i in range(N)]
    
    # Precompute sums for all masks
    mask_sum = [0] * (1 << N)
    for mask in range(1, 1 << N):
        # Find lowest set bit
        lsb = mask & -mask
        # The index of lsb (0-based)
        idx = (lsb.bit_length() - 1)
        # Sum is sum of smaller mask + A[idx]
        smaller_mask = mask ^ lsb
        mask_sum[mask] = mask_sum[smaller_mask] + A[idx]
    
    # DFS to enumerate partitions
    # State: (remaining_mask, current_xor)
    # We always pick the lowest bit of remaining_mask as the "anchor" for the next group
    # Then we try all submasks of (remaining_mask ^ anchor_bit) as the other members of the group
    
    remaining = (1 << N) - 1
    results = set()
    
    def dfs(rem, cur_xor):
        if rem == 0:
            results.add(cur_xor)
            return
        
        # Get the lowest bit of rem
        anchor = rem & -rem
        other = rem ^ anchor
        
        # Try all submasks of 'other'
        sub = other
        while True:
            group_sum = mask_sum[anchor | sub]
            dfs(rem ^ (anchor | sub), cur_xor ^ group_sum)
            if sub == 0:
                break
            sub = (sub - 1) & other
    
    dfs(remaining, 0)
    print(len(results))

if __name__ == "__main__":
    solve()
