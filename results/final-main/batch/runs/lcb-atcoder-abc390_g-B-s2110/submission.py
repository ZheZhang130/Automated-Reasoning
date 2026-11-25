import sys

MOD = 998244353


def solve(n):
    weights = []
    counts = []
    sums = []
    lo, w = 1, 10
    while lo <= n:
        hi = min(n, w - 1)
        c = hi - lo + 1
        weights.append(w)
        counts.append(c)
        sums.append((lo + hi) * c // 2 % MOD)
        lo, w = w, w * 10

    # For P(x) = product (1 + w*x)^c, build D and E with D*P' = E*P.
    d = len(weights)
    D = [1]
    for w in weights:
        D.append(0)
        for j in range(len(D) - 1, 0, -1):
            D[j] = (D[j] + w * D[j - 1]) % MOD
    E = [0] * d
    for w, c in zip(weights, counts):
        q = 0
        for j in range(d):
            q = (D[j] - w * q) % MOD
            E[j] = (E[j] + c * w * q) % MOD

    inv = [0] * n
    if n > 1:
        inv[1] = 1
    fact_weight = 1
    for k in range(2, n):
        inv[k] = MOD - (MOD // k) * inv[MOD % k] % MOD
        fact_weight = fact_weight * k % MOD

    # P modulo x^n suffices: a suffix has at most n-1 elements.
    p = [1] + [0] * (n - 1)
    slopes = D[1:]
    intercepts = [(E[j] + j * slopes[j]) % MOD for j in range(d)]
    for k in range(n - 1):
        acc = 0
        for j in range(min(k + 1, d)):
            acc += (intercepts[j] - k * slopes[j]) * p[k - j]
        p[k + 1] = acc * inv[k + 1] % MOD

    # Exclude the element being shifted by dividing out its own factor.
    # Each size-k suffix set occurs in k! * (n-1-k)! permutations.
    excluded = [0] * d
    ans = 0
    for k, pk in enumerate(p):
        total = 0
        for j in range(d):
            q = (pk - weights[j] * excluded[j]) % MOD
            excluded[j] = q
            total += sums[j] * q
        ans = (ans + fact_weight * total) % MOD
        if k < n - 1:
            fact_weight = fact_weight * (k + 1) * inv[n - 1 - k] % MOD
    return ans


if __name__ == '__main__':
    print(solve(int(sys.stdin.buffer.readline())))
