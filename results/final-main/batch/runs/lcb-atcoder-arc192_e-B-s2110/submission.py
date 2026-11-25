import sys
from array import array

MOD = 998244353


def main():
    w, h, l, r, d, u = map(int, sys.stdin.buffer.read().split())
    size = w + h + 4
    fact = array('I', [1]) * (size + 1)
    invfact = array('I', [1]) * (size + 1)
    value = 1
    for i in range(2, size + 1):
        value = value * i % MOD
        fact[i] = value
    value = pow(value, MOD - 2, MOD)
    for i in range(size, 1, -1):
        invfact[i] = value
        value = value * i % MOD

    def prefix(a, b):
        # Sum of C(i+j+2,i+1)-1 over 0 <= i <= a, 0 <= j <= b.
        if a < 0 or b < 0:
            return 0
        return (fact[a+b+4] * invfact[a+2] * invfact[b+2]
                - a - b - 4 - (a+1)*(b+1)) % MOD

    def entering(n, m, k, lo, hi):
        if k == 0:
            return 0
        # First entry is a step from (k-1,t) to (k,t).
        before = invfact[k]
        after = invfact[n-k+1]
        result = 0
        for t in range(lo, hi + 1):
            p = fact[k+t+1] * invfact[t+1] * before % MOD - 1
            q = fact[n-k+m-t+2] * invfact[m-t+1] * after % MOD - 1
            result += p * q
        return result % MOD

    # In the full grid, classify invalid paths by their first point in the hole.
    starts_inside = (prefix(w-l, h-d) - prefix(w-r-1, h-d)
                     - prefix(w-l, h-u-1) + prefix(w-r-1, h-u-1))
    answer = (prefix(w, h) - starts_inside
              - entering(w, h, l, d, u) - entering(h, w, d, l, r))
    print(answer % MOD)


if __name__ == '__main__':
    main()
