import sys
from collections import Counter

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    M = int(input_data[1])
    S = input_data[2]
    T = input_data[3]
    
    # Count digits in T[0:M-1] (first M-1 operations)
    t_counts = Counter(T[:-1])
    last_digit = T[-1]
    
    # Build G: for each position, pick the largest available digit from T[0:M-1]
    # that is strictly greater than S[i]. If none, pick the largest available digit
    # (even if <= S[i]), but we must be careful: we can only use a digit if we have it.
    # Actually, the strategy is: at each position, try to use the largest available digit
    # from T[0:M-1]. If that digit > S[i], we use it. If that digit == S[i], we can also use it
    # (but it doesn't improve). If that digit < S[i], we should not use it unless we have no choice.
    # However, the optimal strategy is: at each position, use the largest available digit d.
    # If d > S[i], we use it. If d == S[i], we can use it or not. If d < S[i], we should not use it.
    # But wait: we might run out of large digits. So we should greedily use the largest available digit
    # at each position, regardless of whether it improves S[i] or not? No, that's not correct.
    # Correct strategy: at each position, use the largest available digit d. If d > S[i], use it.
    # If d == S[i], we can use it (no harm). If d < S[i], we should not use it. But we might run out of large digits.
    # So we should use the largest available digit d at each position, but only if d >= S[i].
    # If d < S[i], we keep S[i] and don't use any operation (save the operation for later).
    # But the problem is: we have a limited supply of each digit. So we need to decide which positions
    # to use which digits.
    # The optimal strategy is: at each position, use the largest available digit d. If d > S[i], use it.
    # If d == S[i], we can use it or not. If d < S[i], we should not use it. But we might run out of large digits.
    # So we should use the largest available digit d at each position, but only if d >= S[i].
    # If d < S[i], we keep S[i].
    # But this might not be optimal because we might want to save a large digit for a later position.
    # However, since we process left to right, and we want to maximize the string lexicographically,
    # we should always use the largest available digit at the current position if it's >= S[i].
    # Because using a smaller digit now would make the string smaller, and we can't improve it later.
    # So the greedy strategy is correct.
    
    # But wait: what if we have multiple large digits? For example, S[i] = '5', and we have '6' and '7' available.
    # We should use '7' because it's larger. But what if we have only one '7' and many '6's?
    # We should use '7' at the current position, because '7' > '6' > '5', so '7' is better.
    # So the greedy strategy is: at each position, use the largest available digit d. If d >= S[i], use it.
    # Otherwise, keep S[i].
    
    # But there's a catch: what if we have no operations left? Then we keep S[i].
    # So we need to track the remaining counts of each digit.
    
    # Let's implement this.
    
    # We'll build G by iterating through S and for each position, picking the largest available digit d
    # such that d >= S[i]. If no such digit exists, we keep S[i].
    # But wait: what if the largest available digit d is less than S[i]? Then we keep S[i].
    # But what if we have no operations left? Then we keep S[i].
    
    # So the algorithm is:
    # 1. Count digits in T[0:M-1].
    # 2. For each position i in S:
    #    a. Find the largest digit d in t_counts such that d >= S[i].
    #    b. If such d exists, use it: append d to G, decrement t_counts[d].
    #    c. Otherwise, keep S[i]: append S[i] to G.
    # 3. Check if G contains last_digit. If yes, return G.
    # 4. If not, change the last digit of G to last_digit.
    
    # But wait: step 2a might not be correct. What if the largest available digit d is less than S[i]?
    # Then we keep S[i]. But what if we have no operations left? Then we keep S[i].
    # So the algorithm is correct.
    
    # However, there's a problem: what if we have multiple digits that are >= S[i]?
    # We should use the largest one. So we need to find the largest digit d in t_counts such that d >= S[i].
    # Since there are only 9 digits, we can iterate from '9' down to S[i].
    
    # Let's implement this.
    
    G = []
    for i in range(N):
        original_digit = S[i]
        # Find the largest digit d in t_counts such that d >= original_digit
        best_digit = None
        for d in ['9', '8', '7', '6', '5', '4', '3', '2', '1']:
            if d >= original_digit and t_counts[d] > 0:
                best_digit = d
                break
        
        if best_digit is not None:
            G.append(best_digit)
            t_counts[best_digit] -= 1
        else:
            G.append(original_digit)
    
    # Check if G contains last_digit
    if last_digit in G:
        print(''.join(G))
    else:
        # Change the last digit to last_digit
        G[-1] = last_digit
        print(''.join(G))

solve()
