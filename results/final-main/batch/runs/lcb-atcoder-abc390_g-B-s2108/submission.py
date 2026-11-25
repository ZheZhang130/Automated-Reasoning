import sys

MOD = 998244353


def main():
    n = int(sys.stdin.buffer.readline())
    groups = []
    lo = 1
    power = 10
    while lo <= n:
        hi = min(n, power - 1)
        count = hi - lo + 1
        groups.append((power, count, (lo + hi) * count // 2 % MOD))
        lo = power
        power *= 10

    def product_except(skip):
        poly = [1]
        for i, (w, _, _) in enumerate(groups):
            if i != skip:
                poly.append(0)
                for j in range(len(poly) - 1, 0, -1):
                    poly[j] = (poly[j] + w * poly[j - 1]) % MOD
        return poly

    m = len(groups)
    # P = product (1+w*x)^count. With D = product (1+w*x),
    # D*P' = H*P, where H is computed by the product rule.
    d = product_except(-1)[1:]
    h = [0] * m
    for i, (w, count, _) in enumerate(groups):
        for j, coeff in enumerate(product_except(i)):
            h[j] = (h[j] + count * w * coeff) % MOD

    fact = [1] * n
    inv = [1] * n
    for k in range(1, n):
        fact[k] = fact[k - 1] * k % MOD
        if k > 1:
            inv[k] = -(MOD // k) * inv[MOD % k] % MOD

    # For each group, track coefficients of P/(1+w*x), since
    # the distinguished number cannot also occur in its own suffix.
    p = [1]
    q = [1] * m
    weights = [w for w, _, _ in groups]
    sums = [s for _, _, s in groups]
    answer = fact[-1] * sum(sums)
    for k in range(1, n):
        val = 0
        t = k - 1
        for j in range(min(m, k)):
            val += (h[j] - (t - j) * d[j]) * p[t - j]
        pk = val * inv[k] % MOD
        p.append(pk)
        contribution = 0
        for i in range(m):
            qi = (pk - weights[i] * q[i]) % MOD
            q[i] = qi
            contribution += sums[i] * qi
        # A specified suffix set of size k occurs in k!(n-1-k)! orders.
        answer = (answer + contribution * fact[k] * fact[n - 1 - k]) % MOD
    print(answer % MOD)


if __name__ == "__main__":
    main()
