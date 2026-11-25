import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    try:
        N = int(next(iterator))
        A = [int(next(iterator)) for _ in range(N)]
    except StopIteration:
        return

    # diff[i] will store the change in the number of givers for year i
    # We use a difference array to efficiently add intervals
    # diff[i] += 1 means starting an interval at year i
    # diff[j] -= 1 means ending an interval before year j
    diff = [0] * (N + 2)
    
    current_givers = 0
    B = [0] * N
    
    for i in range(N):
        # Year is i (0-indexed in our loop, but problem uses 1-indexed years)
        # At the start of year i, we add the accumulated diff to current_givers
        current_givers += diff[i]
        
        # Number of stones alien i receives as gifts
        gifts_received = current_givers
        
        # Total stones alien i has after receiving gifts
        total_stones = A[i] + gifts_received
        
        # Number of years alien i will give stones
        # They give in years i+1, i+2, ..., i + d_i (inclusive)
        # d_i = min(total_stones, N - 1 - i) because there are N - 1 - i years after year i
        # Note: In 0-indexed terms, years are 0 to N-1.
        # Alien i becomes adult at year i. They give in years i+1, i+2, ...
        # The number of years they can give is min(total_stones, N - 1 - i)
        
        d_i = min(total_stones, N - 1 - i)
        
        # Final stones for alien i
        B[i] = total_stones - d_i
        
        # Update difference array for the interval of giving
        # The interval starts at year i + 1 (inclusive) and ends at year i + d_i (inclusive)
        # In difference array terms:
        # Add 1 at start of interval: year i + 1
        # Subtract 1 at end of interval + 1: year i + d_i + 1
        
        start_year = i + 1
        end_year = i + d_i
        
        if start_year < N:
            diff[start_year] += 1
        if end_year + 1 < N + 2:
            diff[end_year + 1] -= 1
            
    print(*(B))

if __name__ == "__main__":
    solve()
