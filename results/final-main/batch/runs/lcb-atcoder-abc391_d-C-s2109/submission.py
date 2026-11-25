import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    
    N = int(next(iterator))
    W = int(next(iterator))
    
    # Store blocks by column
    col_blocks = defaultdict(list)
    for i in range(1, N + 1):
        x = int(next(iterator))
        y = int(next(iterator))
        col_blocks[x].append((y, i))
    
    # For each column, sort by height and assign ranks
    # We need to track the max height for each rank across all columns
    # Only ranks 1..m (where m is min column size) can be removed
    
    # First, determine the minimum column size (number of blocks in each column)
    col_sizes = [len(col_blocks[c]) for c in range(1, W + 1)]
    min_col_size = min(col_sizes) if col_sizes else 0
    
    # For each rank r from 1 to min_col_size, find the max initial height
    # For ranks > min_col_size, they can never be removed (removal time = infinity)
    
    max_height_for_rank = {}
    for r in range(1, min_col_size + 1):
        max_h = 0
        for c in range(1, W + 1):
            blocks = col_blocks[c]
            if len(blocks) >= r:
                # blocks are sorted by height, so blocks[r-1] is the r-th block
                max_h = max(max_h, blocks[r-1][0])
        max_height_for_rank[r] = max_h
    
    # For each block, determine its removal time
    # A block at column x, rank r (1-indexed) has removal time = max_height_for_rank[r]
    # If r > min_col_size, removal time is infinity
    
    block_removal_time = {}
    for c in range(1, W + 1):
        blocks = col_blocks[c]
        for rank, (y, idx) in enumerate(blocks, start=1):
            if rank <= min_col_size:
                removal_time = max_height_for_rank[rank]
            else:
                removal_time = float('inf')
            block_removal_time[idx] = removal_time
    
    Q = int(next(iterator))
    results = []
    for _ in range(Q):
        t = int(next(iterator))
        a = int(next(iterator))
        removal_time = block_removal_time[a]
        # Block exists at time T+0.5 if removal_time > T
        if removal_time > t:
            results.append("Yes")
        else:
            results.append("No")
    
    print('\n'.join(results))

if __name__ == "__main__":
    solve()
