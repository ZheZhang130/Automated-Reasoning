import sys
from collections import Counter

def solve():
    try:
        data = sys.stdin.read().split()
        if not data:
            return
        N = int(data[0])
        S = data[1]
    except:
        return

    MOD = 998244353

    # Precompute factorials
    fact = [1] * (N + 1)
    for i in range(2, N + 1):
        fact[i] = fact[i-1] * i % MOD
    
    def mod_inverse(a, m):
        return pow(a, m - 2, m)

    # Decompose into top-level primitive components only
    def get_top_level_components(s):
        components = []
        depth = 0
        start = 0
        for i, c in enumerate(s):
            if c == '(':
                depth += 1
            else:
                depth -= 1
            if depth == 0:
                components.append(s[start:i+1])
                start = i + 1
        return components

    components = get_top_level_components(S)
    
    # Count frequencies
    freq = Counter(components)
    
    # Calculate multinomial coefficient
    total = len(components)
    
    numerator = fact[total]
    denominator = 1
    for count in freq.values():
        denominator = denominator * fact[count] % MOD
    
    answer = numerator * mod_inverse(denominator, MOD) % MOD
    
    print(answer)

solve()
