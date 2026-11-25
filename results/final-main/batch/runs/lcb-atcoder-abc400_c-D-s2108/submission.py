import sys
import math

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        N = int(line)
    except ValueError:
        return

    # We need to count X in [1, N] such that X = 2^a * b^2 for positive integers a, b.
    # This means X = 2^a * b^2, with a >= 1, b >= 1.
    # Let b = k. Then X = 2^a * k^2.
    # For a fixed k, we can have a = 1, 2, 3, ... as long as 2^a * k^2 <= N.
    # So for each k, the number of valid a's is floor(log2(N / k^2)) if N/k^2 >= 2, else 0.
    # But we must be careful: different (a, b) pairs might yield the same X? 
    # Actually, the representation is unique for a given X: 
    #   Let X = 2^a * b^2. Then b^2 must be the largest square divisor of X that is not divisible by 2? 
    #   Not exactly. Let's think differently.
    #
    # Alternative approach:
    #   X = 2^a * b^2. Let b = 2^x * y, where y is odd.
    #   Then X = 2^a * (2^x * y)^2 = 2^(a + 2x) * y^2.
    #   So X = 2^E * y^2, where E = a + 2x, and y is odd, y >= 1.
    #   Also, since a >= 1, we have E = a + 2x >= 1 + 2x.
    #   But note: for a fixed X, if we write X = 2^E * y^2 with y odd, then E is fixed.
    #   Then we need to check if there exists a >= 1 and x >= 0 such that E = a + 2x.
    #   Since a = E - 2x, and we require a >= 1, we have E - 2x >= 1 => 2x <= E - 1 => x <= (E-1)/2.
    #   Also x >= 0. So we need (E-1)/2 >= 0 => E >= 1.
    #   And for each such X, as long as E >= 1, we can choose x in [0, floor((E-1)/2)] and then a = E - 2x.
    #   But wait: the problem says "there exists a pair (a,b)". So if for a given X, there is at least one pair, then X is good.
    #   So X is good if and only if when we write X = 2^E * y^2 with y odd, we have E >= 1.
    #   But note: if E=0, then X = y^2 (with y odd). Then we would need 0 = a + 2x, but a>=1, so impossible.
    #   Therefore, X is good iff the exponent of 2 in the prime factorization of X is at least 1? 
    #   Not exactly: because b can have factors of 2. 
    #   Actually, let's re-express:
    #      X = 2^a * b^2.
    #      Let v2(X) be the exponent of 2 in X. Then v2(X) = a + 2*v2(b).
    #      Since a >= 1, we have v2(X) = a + 2*v2(b) >= 1 + 2*v2(b) >= 1.
    #      So v2(X) must be at least 1. But is that sufficient?
    #      Suppose v2(X) = E >= 1. Then we can write X = 2^E * y^2, where y is odd? 
    #      Actually, no: because b^2 might not be a perfect square of an odd number. 
    #      Let me clarify: 
    #          Let X = 2^E * m, where m is odd. Then for X to be of the form 2^a * b^2, 
    #          we must have that m is a perfect square. Why?
    #          Because if X = 2^a * b^2, then the odd part of X must be a perfect square.
    #          So: X is good if and only if:
    #             (1) The odd part of X is a perfect square, and
    #             (2) The exponent of 2 in X is at least 1.
    #
    #   Let X = 2^E * m, with m odd. Then X is good iff m is a perfect square and E >= 1.
    #   But note: if m is a perfect square, say m = k^2, then X = 2^E * k^2.
    #   We can write this as 2^a * b^2 by setting b = k * 2^t, then b^2 = k^2 * 2^(2t), so X = 2^(E-2t) * k^2 * 2^(2t) = 2^E * k^2.
    #   We need a = E - 2t >= 1. So we need E - 2t >= 1 for some t >= 0.
    #   This is possible if and only if E >= 1 (since we can take t=0, then a=E>=1).
    #   Therefore, the condition is simply: the odd part of X is a perfect square and the exponent of 2 is at least 1.
    #
    #   However, note: what if X is a perfect square? Then the odd part is a perfect square and the even part is a perfect square, so the whole is a perfect square.
    #   But we require a>=1, so X cannot be a perfect square of an odd number (because then E=0). 
    #   Actually, if X is a perfect square, then E must be even. But we require E>=1, so if E=0, it's not allowed. 
    #   So: X is good if and only if:
    #        (i) The odd part of X is a perfect square, and
    #        (ii) The exponent of 2 in X is at least 1.
    #
    #   But note: condition (i) is equivalent to: X / (2^E) is a perfect square, where E = v2(X).
    #   And condition (ii) is E>=1.
    #
    #   So we can iterate over possible values of the odd part that are perfect squares.
    #   Let m = k^2, where k is an odd positive integer. Then X = 2^E * k^2, with E>=1.
    #   We require X <= N, so 2^E * k^2 <= N.
    #   For a fixed k (odd), and fixed E (>=1), we have a good integer.
    #   But note: different (k, E) pairs yield distinct X? 
    #        Yes, because the odd part is k^2 and the exponent of 2 is E, so the representation is unique.
    #   Therefore, we can iterate over odd k such that k^2 <= N, and for each k, iterate over E>=1 such that 2^E * k^2 <= N.
    #   However, N is up to 10^18, so k can be up to 10^9. Iterating k from 1 to 10^9 is too slow.
    #
    #   Alternative: iterate over E (the exponent of 2) and then count the number of odd k such that k^2 <= N / 2^E.
    #   For a fixed E, we require k to be odd and k^2 <= N / 2^E, so k <= sqrt(N / 2^E).
    #   The number of odd positive integers k in [1, M] is ceil(M/2) if we consider k=1,3,5,... 
    #        Actually, the odd numbers are 1,3,5,..., up to the largest odd <= M.
    #        The count is (M+1)//2 if M is odd? Let me check:
    #          M=1: odd numbers: 1 -> count=1. (1+1)//2 = 1.
    #          M=2: odd numbers: 1 -> count=1. (2+1)//2 = 1.5 -> floor? Actually, we want the count of odd numbers in [1, M].
    #          The odd numbers are 1, 3, 5, ..., up to the largest odd <= M.
    #          The largest odd <= M is M if M is odd, or M-1 if M is even.
    #          The count is (largest_odd + 1) // 2.
    #          But note: (M+1)//2 in integer division gives:
    #             M=1 -> (1+1)//2 = 1
    #             M=2 -> (2+1)//2 = 1
    #             M=3 -> (3+1)//2 = 2
    #             M=4 -> (4+1)//2 = 2
    #          So yes, the count of odd numbers in [1, M] is (M+1)//2.
    #
    #   Therefore, for a fixed E, the number of odd k is (floor(sqrt(N / 2^E)) + 1) // 2.
    #   But note: we must have 2^E <= N, so E goes from 1 to floor(log2(N)).
    #   Since N <= 10^18, log2(N) <= 60, so E goes from 1 to about 60.
    #
    #   Algorithm:
    #      total = 0
    #      E = 1
    #      while (2^E) <= N:
    #          limit = N // (2**E)
    #          if limit == 0: break
    #          m = isqrt(limit)   # integer square root
    #          count = (m + 1) // 2
    #          total += count
    #          E += 1
    #      print(total)
    #
    #   However, note: we must be cautious with large numbers and floating point. 
    #   We can use integer square root. In Python, math.isqrt is available (Python 3.8+).
    #
    #   Let's test with sample 1: N=20.
    #      E=1: 2^1=2, limit=20//2=10, m=isqrt(10)=3, count=(3+1)//2=2. (k=1,3 -> X=2*1=2, 2*9=18)
    #      E=2: 2^2=4, limit=20//4=5, m=isqrt(5)=2, count=(2+1)//2=1. (k=1 -> X=4*1=4)
    #      E=3: 2^3=8, limit=20//8=2, m=isqrt(2)=1, count=(1+1)//2=1. (k=1 -> X=8*1=8)
    #      E=4: 2^4=16, limit=20//16=1, m=isqrt(1)=1, count=(1+1)//2=1. (k=1 -> X=16*1=16)
    #      E=5: 2^5=32>20, stop.
    #      Total = 2+1+1+1 = 5. Correct.
    #
    #   Sample 2: N=400.
    #      E=1: limit=200, m=14, count=7  (k=1,3,...,13 -> 7 odds)
    #      E=2: limit=100, m=10, count=5
    #      E=3: limit=50, m=7, count=4
    #      E=4: limit=25, m=5, count=3
    #      E=5: limit=12, m=3, count=2
    #      E=6: limit=6, m=2, count=1
    #      E=7: limit=3, m=1, count=1
    #      E=8: limit=1, m=1, count=1
    #      E=9: 2^9=512>400, stop.
    #      Total = 7+5+4+3+2+1+1+1 = 24. Correct.
    #
    #   So the algorithm is correct.

    import math

    total = 0
    E = 1
    while True:
        two_E = 1 << E
        if two_E > N:
            break
        limit = N // two_E
        if limit == 0:
            break
        m = math.isqrt(limit)
        count = (m + 1) // 2
        total += count
        E += 1

    print(total)

if __name__ == '__main__':
    solve()
