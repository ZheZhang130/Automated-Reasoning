import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    A = [int(next(iterator)) for _ in range(N)]
    
    # difference array for gifts: diff[i] means add diff[i] to running count at year i
    # We use 0-based indexing for years 0 to N-1
    # diff array size N+2 to handle boundaries safely
    diff = [0] * (N + 2)
    
    current_gifts = 0
    B = [0] * N
    
    for i in range(N):
        # Add pending changes from difference array
        current_gifts += diff[i]
        
        # Number of stones alien i has after receiving gifts
        s_i = A[i] + current_gifts
        
        # Number of years alien i will give stones
        # They give in years i+1 to i+d_i (inclusive)
        # d_i = min(s_i, N - 1 - i)
        d_i = min(s_i, N - 1 - i)
        
        # Total stones after giving
        B[i] = s_i - d_i
        
        # Schedule the giving interval in the difference array
        # The interval covers years from i+1 to i+d_i (inclusive)
        # In 0-based indexing, these are years (i+1) to (i+d_i)
        # We add 1 at start of interval and subtract 1 after end of interval
        
        if d_i > 0:
            start_year = i + 1
            end_year = i + d_i
            
            diff[start_year] += 1
            if end_year + 1 < len(diff):
                diff[end_year + 1] -= 1
    
    print(*(B))

if __name__ == "__main__":
    solve()
