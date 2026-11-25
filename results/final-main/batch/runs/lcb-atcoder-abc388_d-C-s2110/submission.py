import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    A = [int(next(iterator)) for _ in range(N)]
    
    # Difference array to track how many givers are active in each year
    # diff[i] will be added to the running count at the start of year i
    # We use size N+2 to handle boundaries safely
    diff = [0] * (N + 2)
    
    current_givers = 0
    result = [0] * N
    
    for i in range(N):
        # Add pending changes from difference array
        current_givers += diff[i]
        
        # Number of stones alien i has after receiving gifts from previous years
        s_i = A[i] + current_givers
        
        # Number of years this alien will give stones
        # They can give for min(s_i, N - 1 - i) years after year i
        # Note: N - 1 - i is the number of years remaining after year i (0-indexed)
        # But we need to be careful: the problem says "next d_i years"
        # In 0-indexed terms, if we are at year i, the remaining years are i+1 to N-1
        # So the count is N - 1 - i
        
        d_i = min(s_i, N - 1 - i)
        
        # Final stones for alien i
        result[i] = s_i - d_i
        
        # Schedule the giving interval
        # The alien gives for d_i years starting from year i+1
        # In difference array terms:
        # Add 1 at year i+1 (start of giving)
        # Subtract 1 at year i+1+d_i (end of giving, exclusive)
        
        if d_i > 0:
            diff[i + 1] += 1
            diff[i + 1 + d_i] -= 1
    
    print(*(result))

if __name__ == "__main__":
    solve()
