import sys

def solve():
    try:
        input_data = sys.stdin.read().split()
        if not input_data:
            return
        N = int(input_data[0])
        S = input_data[1]
    except Exception:
        return

    MOD = 998244353

    # Convert S to a list of integers: 1 for '(', -1 for ')'
    # This helps in analyzing the structure
    A = [1 if c == '(' else -1 for c in S]

    # We need to count the number of distinct strings reachable.
    # Key observation: The operation allows us to reverse a valid parenthesis substring,
    # which effectively swaps '(' with ')' and reverses the order.
    # This operation preserves the "depth profile" of the string in a specific way.
    #
    # Let's consider the positions of '(' and ')'.
    # Actually, a simpler invariant might be the sequence of depths at even positions?
    # Or perhaps we can think about the structure of the string.
    #
    # Let's try a different approach.
    # Consider the string as a sequence of "blocks".
    # A valid parenthesis sequence can be decomposed into a unique structure.
    #
    # Let's look at the sample cases again.
    # Sample 1: (())() -> 2 reachable strings: (())() and ()(())
    # Sample 2: () -> 1 reachable string: ()
    # Sample 3 (from description): (()())() -> 2 reachable strings: (()())() and ()(()())
    #
    # Notice that in Sample 1, the string (())() can be seen as (()) followed by ().
    # The operation on the whole string (())() -> ()(()) swaps the two parts.
    #
    # Hypothesis: The reachable strings are determined by the number of "primitive" components.
    # A primitive component is a valid parenthesis sequence that cannot be split into two non-empty valid sequences.
    # For example, (()) is primitive, () is primitive.
    # (())() is composed of (()) and ().
    # (()())() is composed of (()()) and ().
    #
    # Let's decompose S into primitive components.
    # For S = (())(), the primitives are (()) and ().
    # For S = (()())(), the primitives are (()()) and ().
    #
    # If we have k primitive components, say P1, P2, ..., Pk.
    # We can reverse any valid substring.
    # Reversing a valid substring that spans multiple primitives might merge them or split them?
    # Actually, the operation is: choose a valid substring, reverse it (swap ( and ) and reverse order).
    #
    # Let's consider the effect on the primitive decomposition.
    # If we have a valid substring that is a concatenation of some primitives, say P_i ... P_j,
    # reversing it would transform P_i ... P_j into something else.
    #
    # Wait, let's re-read the operation carefully.
    # "Choose a contiguous substring of S that is a valid parenthesis sequence, and reverse it."
    # "reversing here is different from the usual definition of reversing."
    # "replace S_i with ) if S_{l+r-i} is (, and with ( if S_{l+r-i} is )".
    # This means: reverse the string, then swap ( and ).
    #
    # Example: S = (())(), substring from 1 to 6 is (())().
    # Reverse: )(()((
    # Swap: ()(())
    # So (())() becomes ()(())
    #
    # What if we have (()())()?
    # Primitives: (()()), ()
    # If we reverse the whole string (()())():
    # Reverse: )(()())(
    # Swap: ()(()())
    # So (()())() becomes ()(()())
    #
    # It seems we can permute the primitive components?
    # But not arbitrarily.
    #
    # Let's think about the "depth" of the string.
    # For a valid parenthesis sequence, the depth at each position is well-defined.
    # The operation preserves the multiset of depths? No.
    #
    # Let's consider the positions of the "primitive" boundaries.
    # A primitive component ends when the depth returns to 0.
    # Let the depths be d[0], d[1], ..., d[N-1]. d[0]=0, d[N]=0.
    # The operation on a valid substring from l to r (1-indexed, so indices l-1 to r-1 in 0-indexed)
    # transforms the substring.
    #
    # Key Insight:
    # The operation allows us to reverse the order of the primitive components?
    # Not exactly.
    #
    # Let's consider the sequence of primitive components.
    # For (())(), primitives are A=(()) and B=().
    # We can go from AB to BA.
    # Can we go from AB to ABA? No, because we need valid substrings.
    #
    # Actually, let's consider the "skeleton" of the string.
    # The operation on a valid substring P (which is a concatenation of some primitives)
    # transforms P into P' where P' is also a valid parenthesis sequence.
    #
    # Let's try to find an invariant.
    # Consider the positions where the depth is 0. These are the boundaries between primitives.
    # Let the indices where depth is 0 be 0 = i_0 < i_1 < ... < i_k = N.
    # Then the primitives are S[i_0:i_1], S[i_1:i_2], ..., S[i_{k-1}:i_k].
    #
    # When we apply the operation on a valid substring from l to r,
    # the new string S' will have depth profile related to S.
    # Specifically, if we reverse and swap, the depth profile is transformed.
    #
    # Let's consider the sequence of primitive components as a multiset.
    # In Sample 1: (()) and (). We can swap them to get ()(())
    # In Sample 3: (()()) and (). We can swap them to get ()(()())
    #
    # What if we have (()())(()())?
    # Primitives: A=(()()), B=(()())
    # Can we swap them? Yes, by reversing the whole string.
    # Can we do anything else?
    #
    # What if we have (())(())?
    # Primitives: A=(()), B=(())
    # Reverse whole: (())(()) -> (())(()) (same)
    # So only 1 string?
    #
    # Wait, let's check if we can do partial reversals.
    # For (())(()), can we reverse just the first (())?
    # Substring 1-4: (()) is valid.
    # Reverse: ))((
    # Swap: (( ))
    # So (())(()) becomes (())(()) again.
    #
    # So it seems we can only swap primitive components if they are distinct?
    # Or maybe we can always swap any two adjacent primitives?
    #
    # Let's consider the structure more carefully.
    # The operation on a valid substring P transforms P into P'.
    # If P is a concatenation of primitives P1, P2, ..., Pm,
    # then P' is also a valid parenthesis sequence.
    # Is P' a concatenation of the same primitives in reverse order?
    #
    # Let's test with P = (())(). Primitives: (()), ().
    # P' = ()(())
    # Primitives of P': (), (())
    # So the order is reversed.
    #
    # What if P = (()())()? Primitives: (()()), ().
    # P' = ()(()())
    # Primitives of P': (), (()())
    # Order reversed.
    #
    # What if P = (())(())? Primitives: (()), (())
    # P' = (())(())
    # Primitives: (()), (())
    # Order reversed, but since they are identical, it looks the same.
    #
    # So it seems the operation allows us to reverse the order of any contiguous block of primitives.
    # This means we can achieve any permutation of the primitive components?
    #
    # Wait, can we reverse a block of primitives that is not the whole string?
    # Yes, if the block itself is a valid parenthesis sequence.
    # A concatenation of primitives is always a valid parenthesis sequence.
    # So we can reverse any contiguous block of primitives.
    #
    # This means we can achieve any permutation of the primitive components.
    # So the number of distinct strings is the number of distinct permutations of the primitive components.
    #
    # Let's verify with Sample 1: (())(), primitives: (()), ().
    # Distinct permutations: 2! / (1! * 1!) = 2. Correct.
    #
    # Sample 2: (), primitives: ().
    # Distinct permutations: 1! / (1!) = 1. Correct.
    #
    # Sample 3: (()())(), primitives: (()()), ().
    # Distinct permutations: 2! / (1! * 1!) = 2. Correct.
    #
    # What about (()())(()())?
    # Primitives: (()()), (()())
    # Distinct permutations: 2! / (2!) = 1.
    #
    # What about (())(())?
    # Primitives: (()), (())
    # Distinct permutations: 2! / (2!) = 1.
    #
    # What about (()())(()())(())?
    # Primitives: (()()), (()()), (())
    # Distinct permutations: 3! / (2! * 1!) = 3.
    #
    # So the algorithm is:
    # 1. Decompose S into primitive components.
    # 2. Count the frequency of each primitive component.
    # 3. The answer is N! / (product of (count_i!)) for each distinct primitive component, modulo 998244353.
    #
    # Wait, but the primitive components are strings. We need to count their frequencies.
    # But the primitive components can be identical.
    #
    # How to decompose into primitives?
    # We can use a stack to find the depth.
    # The depth returns to 0 at the end of each primitive.
    #
    # Let's implement this.

    # Find primitive components
    # We can use a counter for depth.
    # When depth becomes 0, we have found a primitive component.
    
    depth = 0
    primitives = []
    current = ""
    
    for c in S:
        current += c
        if c == '(':
            depth += 1
        else:
            depth -= 1
        
        if depth == 0:
            primitives.append(current)
            current = ""
    
    # Now count frequencies of each primitive
    from collections import Counter
    counts = Counter(primitives)
    
    # Calculate the number of distinct permutations
    # N is the total length, but we need the number of primitives, say K.
    K = len(primitives)
    
    # The number of distinct permutations is K! / (product of count! for each count)
    
    # We need factorials
    fact = [1] * (K + 1)
    for i in range(2, K + 1):
        fact[i] = fact[i-1] * i % MOD
    
    ans = fact[K]
    for count in counts.values():
        ans = ans * fact[count] % MOD
        ans = ans * pow(fact[count], MOD - 2, MOD) % MOD
    
    # Wait, the formula is K! / (count1! * count2! * ...)
    # So we multiply by modular inverse of each count!
    
    # Let's recalculate
    ans = fact[K]
    for count in counts.values():
        inv = pow(fact[count], MOD - 2, MOD)
        ans = ans * inv % MOD
    
    print(ans)

solve()
