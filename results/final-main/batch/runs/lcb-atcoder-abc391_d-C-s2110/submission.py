import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    it = iter(input_data)
    
    N = int(next(it))
    W = int(next(it))
    
    blocks = []
    for i in range(1, N + 1):
        x = int(next(it))
        y = int(next(it))
        blocks.append((x, y, i))
    
    Q = int(next(it))
    queries = []
    for j in range(Q):
        t = int(next(it))
        a = int(next(it))
        queries.append((t, a))
    
    # Group blocks by column
    col_blocks = defaultdict(list)
    for x, y, idx in blocks:
        col_blocks[x].append((y, idx))
    
    # Sort each column by height
    for x in col_blocks:
        col_blocks[x].sort()
    
    # Find the minimum column size (including empty columns)
    col_sizes = [len(col_blocks[x]) for x in range(1, W + 1)]
    min_count = min(col_sizes) if col_sizes else 0
    
    # If min_count == 0, all removal times are infinity
    if min_count == 0:
        removal_times = [float('inf')] * N
    else:
        # For each rank r from 1 to min_count, find the max initial height
        # across all columns for that rank
        rank_max_height = [0] * (min_count + 1)  # 1-indexed
        
        for x in range(1, W + 1):
            if x in col_blocks:
                for rank, (y, idx) in enumerate(col_blocks[x], 1):
                    if rank <= min_count:
                        rank_max_height[rank] = max(rank_max_height[rank], y)
        
        # Assign removal times
        removal_times = [float('inf')] * N
        for x in range(1, W + 1):
            if x in col_blocks:
                for rank, (y, idx) in enumerate(col_blocks[x], 1):
                    if rank <= min_count:
                        removal_times[idx - 1] = rank_max_height[rank]
                    else:
                        removal_times[idx - 1] = float('inf')
    
    # Process queries
    results = []
    for t, a in queries:
        if removal_times[a - 1] > t:
            results.append("Yes")
        else:
            results.append("No")
    
    print('\n'.join(results))

solve()
