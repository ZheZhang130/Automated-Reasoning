import sys
from collections import Counter

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    S = input_data[1]
    
    MOD = 998244353
    
    # Decompose into primitive components
    # A primitive component is a valid parenthesis sequence that cannot be split
    # into two non-empty valid parenthesis sequences.
    balance = 0
    start = 0
    components = []
    for i, c in enumerate(S):
        if c == '(':
            balance += 1
        else:
            balance -= 1
        if balance == 0:
            components.append(S[start:i+1])
            start = i + 1
    
    # Count frequencies
    comp_counts = Counter(components)
    
    # The answer is the number of distinct permutations of these components.
    num_components = len(components)
    
    # Precompute factorials
    fact = [1] * (num_components + 1)
    for i in range(2, num_components + 1):
        fact[i] = (fact[i-1] * i) % MOD
    
    # Compute multinomial coefficient
    numerator = fact[num_components]
    denominator = 1
    for count in comp_counts.values():
        denominator = (denominator * fact[count]) % MOD
    
    answer = (numerator * pow(denominator, MOD-2, MOD)) % MOD
    print(answer)

if __name__ == "__main__":
    solve()
