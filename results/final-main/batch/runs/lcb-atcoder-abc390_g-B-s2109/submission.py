import sys

MOD = 998244353


def solve(n):
    weights = []
    counts = []
    sums = []
    lo = 1
    while lo <= n:
        w = lo * 10
        hi = min(n, w - 1)
        count = hi - lo + 1
        weights.append(w)
        counts.append(count)
        sums.append((lo + hi) * count // 2 % MOD)
        lo = w

    d = len(weights)
    # D = product (1 + w*x).  G = product (1 + w*x)^(count-1).
    # Construct B and H with D*G' = B*G and the desired polynomial G*H.
    denominator = [1]
    for w in weights:
        denominator.append(0)
        for j in range(len(denominator) - 1, 0, -1):
            denominator[j] = (denominator[j] + w * denominator[j - 1]) % MOD

    b = [0] * d
    h = [0] * d
    for w, count, value_sum in zip(weights, counts, sums):
        quotient = 1
        scale = (count - 1) * w
        for j in range(d):
            b[j] = (b[j] + scale * quotient) % MOD
            h[j] = (h[j] + value_sum * quotient) % MOD
            quotient = (denominator[j + 1] - w * quotient) % MOD

    limit = n - d
    inv = [0] * (limit + 1)
    g = [0] * (limit + 1)
    g[0] = 1
    if limit:
        inv[1] = 1
    for k in range(1, limit + 1):
        if k > 1:
            inv[k] = MOD - (MOD // k) * inv[MOD % k] % MOD
        total = 0
        for j in range(min(d, k)):
            total += (b[j] - (k - 1 - j) * denominator[j + 1]) * g[k - 1 - j]
        g[k] = total * inv[k] % MOD

    fact = [1] * n
    for k in range(1, n):
        fact[k] = fact[k - 1] * k % MOD
    # A suffix set of size k admits k! suffix orders and (n-1-k)! prefix orders.
    factors = [fact[k] * fact[n - 1 - k] % MOD for k in range(n)]
    answer = 0
    for shift, value in enumerate(h):
        subtotal = sum(a * f for a, f in zip(g, factors[shift:shift + limit + 1]))
        answer = (answer + value * (subtotal % MOD)) % MOD
    return answer


if __name__ == '__main__':
    print(solve(int(sys.stdin.buffer.readline())))
