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

    # Count frequencies of each digit in T
    count = Counter(T)
    last_digit = T[-1]

    # Build the optimal string G greedily
    G = list(S)
    for i in range(N):
        # Find the largest digit available in T
        best_digit = '0'
        for d in '987654321':
            if count[d] > 0:
                best_digit = d
                break
        
        if best_digit > S[i]:
            G[i] = best_digit
            count[best_digit] -= 1

    # Check if G contains the last_digit
    if last_digit in G:
        print("".join(G))
    else:
        # Change the last digit to last_digit
        G[-1] = last_digit
        print("".join(G))

if __name__ == "__main__":
    solve()
