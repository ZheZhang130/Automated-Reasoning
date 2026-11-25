import sys

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

    # The key insight: we can reverse any valid substring.
    # This allows us to swap adjacent primitive components.
    # So we can achieve any permutation of the primitive components.
    #
    # But wait, the sample output for (())() is 2, which matches the number of permutations.
    # However, my calculation gave 720, which is 6! = 720.
    # The issue is that I'm treating each primitive component as distinct, but they might be the same.
    #
    # For (())(), the primitive components are "(())" and "()".
    # They are different, so the number of permutations is 2! = 2.
    #
    # But my code calculated 720, which suggests I'm not handling the frequencies correctly.
    #
    # Let me re-check the logic.
    # The multinomial coefficient is N! / (n1! * n2! * ... * nk!)
    # where ni is the count of the i-th distinct primitive component.
    #
    # For (())(), we have:
    # - "(())" appears 1 time
    # - "()" appears 1 time
    # So the answer is 2! / (1! * 1!) = 2.
    #
    # But my code gave 720, which is 6! / (1! * 1!) = 720.
    # The issue is that N is the total length, not the number of primitive components.
    #
    # The multinomial coefficient should be:
    # (number of primitive components)! / (prod(count of each distinct component)!)
    #
    # Let me fix this.

    def get_primitive_components(s):
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

    components = get_primitive_components(S)
    num_components = len(components)
    
    from collections import Counter
    freq = Counter(components)
    
    # Precompute factorials
    fact = [1] * (num_components + 1)
    for i in range(2, num_components + 1):
        fact[i] = fact[i-1] * i % MOD
    
    numerator = fact[num_components]
    denominator = 1
    for count in freq.values():
        denominator = denominator * fact[count] % MOD
    
    # Modular inverse
    def mod_inverse(a, m):
        return pow(a, m - 2, m)
    
    answer = numerator * mod_inverse(denominator, MOD) % MOD
    
    print(answer)

solve()
