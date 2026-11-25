import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    
    N = int(next(iterator))
    W = int(next(iterator))
    
    # Store blocks: (x, y) for each block index 1..N
    blocks = []
    for i in range(N):
        x = int(next(iterator))
        y = int(next(iterator))
        blocks.append((x, y))
    
    Q = int(next(iterator))
    queries = []
    for i in range(Q):
        t = int(next(iterator))
        a = int(next(iterator))
        queries.append((t, a))
    
    # Group blocks by column
    col_blocks = defaultdict(list)
    for i, (x, y) in enumerate(blocks):
        col_blocks[x].append((y, i))  # store (height, original_index)
    
    # For each column, sort by height and assign ranks
    # We need to find the maximum rank that exists in every column
    # Actually, we need to know for each rank r, what is the max height among all columns that have a block at rank r
    
    # First, determine the number of ranks that can be removed (min length of non-empty columns)
    # But actually, a rank is removed only if it exists in ALL columns.
    # If a column has fewer blocks than another, the higher ranks in the longer column never get removed.
    
    # Let's compute for each rank r (1-indexed), the max height among all columns that have a block at rank r.
    # If a column has no block at rank r, then rank r is never removed.
    
    # We'll use a list to store max_height for each rank. Initialize with -1.
    # We need to know the maximum rank that exists in every column.
    
    # First, find the minimum number of blocks in any non-empty column
    min_col_len = float('inf')
    for x in col_blocks:
        if col_blocks[x]:
            min_col_len = min(min_col_len, len(col_blocks[x]))
    
    # If min_col_len is inf (no blocks), then no ranks can be removed
    if min_col_len == float('inf'):
        max_heights = [-1] * (N + 1)
    else:
        # For each rank from 1 to min_col_len, compute max height
        max_heights = [-1] * (min_col_len + 1)
        
        for x in col_blocks:
            sorted_blocks = sorted(col_blocks[x], key=lambda p: p[0])
            for rank, (y, idx) in enumerate(sorted_blocks, start=1):
                if rank <= min_col_len:
                    if max_heights[rank] == -1 or y > max_heights[rank]:
                        max_heights[rank] = y
        
        # For ranks beyond min_col_len, they are never removed (infinity)
        # We'll handle this later when answering queries
    
    # Now, for each block, determine its removal time
    # A block at (x, y) with rank r in its column is removed at time max_heights[r] if r <= min_col_len
    # Otherwise, it's never removed (infinity)
    
    removal_time = [float('inf')] * N  # 0-indexed, so block i corresponds to index i-1 in queries
    
    for x in col_blocks:
        sorted_blocks = sorted(col_blocks[x], key=lambda p: p[0])
        for rank, (y, idx) in enumerate(sorted_blocks, start=1):
            if rank <= min_col_len:
                removal_time[idx] = max_heights[rank]
            else:
                removal_time[idx] = float('inf')
    
    # Answer queries
    results = []
    for t, a in queries:
        # Block a (1-indexed) exists at time t+0.5 if removal_time[a-1] > t
        if removal_time[a-1] > t:
            results.append("Yes")
        else:
            results.append("No")
    
    print('\n'.join(results))

if __name__ == "__main__":
    solve()
