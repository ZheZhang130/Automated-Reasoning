import sys
from collections import Counter

def solve():
    input_data = sys.stdin.read().split()
    N = int(input_data[0])
    M = int(input_data[1])
    S = input_data[2]
    T = input_data[3]

    # Key insight:
    # We have M operations, each replaces one character in S with a character from T.
    # The operations are performed in order k=1,2,...,M.
    # The last operation (k=M) writes T[M-1] to some position i.
    # This overwrites whatever was at position i.
    #
    # To maximize the result:
    # 1. We should use the largest digits from T to improve S from left to right.
    # 2. The last operation must write T[-1] to some position.
    # 3. To minimize the impact of the last operation, we should write T[-1] to the
    #    rightmost position (N-1), because it's the least significant.
    #
    # However, there's a subtlety: we need to use ALL M operations.
    # The first M-1 operations can be used to improve S.
    # The last operation writes T[-1] to the rightmost position.
    #
    # Algorithm:
    # 1. Count the frequency of each digit in T (excluding the last element).
    # 2. Sort the available digits in descending order.
    # 3. For each position in S from left to right:
    #    - If the current digit is less than the largest available digit,
    #      replace it with that largest digit.
    # 4. After the greedy pass, set S[N-1] = T[-1].
    #
    # But wait, we need to be careful: we can only use each digit from T as many times as it appears.
    # So we should use a Counter for T (excluding the last element).
    #
    # Actually, let's think again:
    # We have M operations. The last one writes T[-1] to some position.
    # The first M-1 operations can be used to improve S.
    # We should use the largest digits from T (excluding the last one) to improve S.
    #
    # Algorithm:
    # 1. Count the frequency of each digit in T (excluding the last element).
    # 2. Sort the available digits in descending order.
    # 3. For each position in S from left to right:
    #    - If the current digit is less than the largest available digit,
    #      replace it with that largest digit.
    # 4. After the greedy pass, set S[N-1] = T[-1].
    #
    # But wait, we need to handle the case where M=1 separately.
    # If M=1, we just write T[0] to the rightmost position.
    #
    # Let's implement this:
    if M == 1:
        # Only one operation, write T[0] to the rightmost position
        print(S[:-1] + T[0])
        return
    
    # Count frequency of each digit in T (excluding the last element)
    t_counts = Counter(T[:-1])
    
    # Sort the available digits in descending order
    sorted_T = sorted(t_counts.elements(), reverse=True)
    
    S_list = list(S)
    t_idx = 0
    
    for i in range(N):
        if t_idx < len(sorted_T):
            best_digit = sorted_T[t_idx]
            if best_digit > S_list[i]:
                S_list[i] = best_digit
                t_idx += 1
            # else: keep current digit, move to next position
        else:
            break
    
    # After the greedy pass, set S[N-1] = T[-1]
    S_list[N-1] = T[-1]
    
    result = ''.join(S_list)
    print(result)

solve()
