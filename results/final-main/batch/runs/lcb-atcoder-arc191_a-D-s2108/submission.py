import sys
from collections import Counter

def solve():
    input_data = sys.stdin.read().split()
    N = int(input_data[0])
    M = int(input_data[1])
    S = input_data[2]
    T = input_data[3]

    # Count frequency of each digit in T
    t_counts = Counter(T)
    
    # Convert S to a list for mutability
    S_list = list(S)
    
    # For each position from left to right, try to replace with a larger digit from T
    for i in range(N):
        # Find the largest digit d in T such that d > S[i] and count[d] > 0
        best_digit = None
        for d in range(9, 0, -1):
            if d > int(S_list[i]) and t_counts[str(d)] > 0:
                best_digit = d
                break
        
        if best_digit is not None:
            S_list[i] = str(best_digit)
            t_counts[str(best_digit)] -= 1
    
    # Now, use remaining operations to overwrite with the largest available digit
    # Find the largest digit in T that still has count > 0
    if t_counts:
        max_digit = max(int(d) for d in t_counts if t_counts[d] > 0)
        max_digit_str = str(max_digit)
        
        # Use remaining operations to overwrite positions with this digit
        for i in range(N):
            if int(S_list[i]) < max_digit:
                S_list[i] = max_digit_str
                t_counts[max_digit_str] -= 1
                if t_counts[max_digit_str] == 0:
                    break
    
    # If we still have operations left, we need to use them
    # Find the largest digit in T (even if count is 0)
    if t_counts:
        max_digit = max(int(d) for d in t_counts)
        max_digit_str = str(max_digit)
        
        # Use remaining operations to overwrite positions with this digit
        for i in range(N):
            if int(S_list[i]) < max_digit:
                S_list[i] = max_digit_str
    
    print(''.join(S_list))

solve()
