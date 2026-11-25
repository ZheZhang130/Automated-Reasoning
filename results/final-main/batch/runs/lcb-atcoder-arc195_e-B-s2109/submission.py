import sys

MOD = 998244353


def main():
    it = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(it)
    q = next(it)
    weights = [0, 0] + [next(it) for _ in range(n - 1)]

    inv = [0] * (n + 2)
    inv[1] = 1
    for k in range(2, n + 2):
        inv[k] = MOD - (MOD // k) * inv[MOD % k] % MOD

    both_later = [0] * (n + 1)
    one_later = [0] * (n + 1)
    at_u = [0] * (n + 1)
    factorial = 1
    for k in range(2, n + 1):
        a = weights[k]
        # Descendants of k form one color in a Polya urn with
        # initial counts 1 (inside) and k-1 (outside).
        # Later draws are exchangeable, so their separation probability
        # is 2*(k-1)/(k*(k+1)) = 4/(k+1) - 2/k.
        both_later[k] = (both_later[k - 1] + a * (4 * inv[k + 1] - 2 * inv[k])) % MOD
        one_later[k] = (one_later[k - 1] + a * inv[k]) % MOD
        at_u[k] = a * (k - 1) * inv[k] % MOD
        factorial = factorial * (k - 1) % MOD

    out = []
    for _ in range(q):
        u = next(it)
        v = next(it)
        # An edge contributes exactly when its subtree separates u and v.
        distance = (both_later[u - 1] + at_u[u]
                    + one_later[v - 1] - one_later[u] + weights[v])
        out.append(str(distance * factorial % MOD))
    sys.stdout.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
