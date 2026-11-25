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
    
    # Count frequencies of each digit in T (excluding the last one)
    count = Counter(T[:-1])
    last_digit = T[-1]
    
    # Build the optimal string G greedily using free operations
    # We want to place the largest available digit at positions where it improves the original
    G = []
    for i in range(N):
        original = S[i]
        # Find the largest digit available in count
        best_digit = None
        for d in range(9, 0, -1):
            if count[d] > 0:
                best_digit = str(d)
                break
        
        if best_digit is not None:
            # If best_digit > original, use it
            if best_digit > original:
                G.append(best_digit)
                count[best_digit] -= 1
            else:
                # best_digit <= original, so we keep original
                G.append(original)
        else:
            # No digits left in count, keep original
            G.append(original)
    
    G_str = ''.join(G)
    
    # Now place last_digit at the last position
    result = G_str[:-1] + last_digit
    print(result)

if __name__ == "__main__":
    solve()
