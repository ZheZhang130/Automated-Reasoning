import sys

def solve():
    data = sys.stdin.read().split()
    N = int(data[0])
    M = int(data[1])
    S = data[2]
    T = data[3]
    
    # Sort T in descending order
    T_sorted = sorted(T, reverse=True)
    
    # We have M operations. We can change M positions.
    # We want to maximize the resulting string.
    # 
    # Key insight: We should use the largest digits from T in the most significant positions.
    # But we must use ALL M digits from T.
    # 
    # Strategy:
    # 1. Sort T in descending order.
    # 2. For positions 0 to M-2, try to place the largest available token in the leftmost position
    #    where it's greater than the current digit.
    # 3. For the last token (T[M-1]), place it in the rightmost position that it can improve,
    #    or if it can't improve, in the rightmost position overall.
    
    # Let's implement this:
    S_list = list(S)
    t_ptr = 0
    
    # Use the first M-1 digits from T_sorted to improve S from left to right
    for i in range(min(N, M - 1)):
        if t_ptr < M - 1 and T_sorted[t_ptr] > S_list[i]:
            S_list[i] = T_sorted[t_ptr]
            t_ptr += 1
    
    # Now place the last digit T_sorted[M-1] (if M > 0)
    if M > 0:
        last_digit = T_sorted[M - 1]
        # Find the rightmost position where we can place the last digit
        # We want to place it in the rightmost position where it's greater than the current digit
        # or if it can't improve, in the rightmost position overall.
        
        # Actually, we should place it in the rightmost position where it's greater than the current digit.
        # If it can't improve any position, we place it in the rightmost position overall.
        
        # But we also need to consider that we might have skipped some positions in the first loop.
        # Let's find the rightmost position where last_digit > S_list[i]
        last_pos = -1
        for i in range(N - 1, -1, -1):
            if last_digit > S_list[i]:
                last_pos = i
                break
        
        if last_pos == -1:
            # Can't improve any position, place in the rightmost position overall
            last_pos = N - 1
        
        S_list[last_pos] = last_digit
    
    print(''.join(S_list))

if __name__ == "__main__":
    solve()
