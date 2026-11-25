import sys

MOD = 998244353


def main():
    tokens = iter(sys.stdin.buffer.read().split())
    n = int(next(tokens))
    q = int(next(tokens))

    inv = [0] * (n + 1)
    inv[1] = 1
    prefix = [0] * (n + 1)
    base = [0] * (n + 1)
    weights = [0] * (n + 1)
    total = 0
    factorial = 1

    for i in range(2, n + 1):
        inv[i] = MOD - (MOD // i) * inv[MOD % i] % MOD
        a = int(next(tokens)) % MOD
        weights[i] = a
        prefix[i] = (prefix[i - 1] + a * inv[i]) % MOD
        # Sum of expected distances from i to all vertices below i.
        row = ((i - 1) * a + 2 * total * inv[i - 1]) % MOD
        total = (total + row) % MOD
        base[i] = (row * inv[i] - prefix[i]) % MOD
        factorial = factorial * (i - 1) % MOD

    out = []
    for _ in range(q):
        u = int(next(tokens))
        v = int(next(tokens))
        # The running row average gains A_i/i at each step i > u.
        expected = weights[v] + prefix[v - 1] + base[u]
        out.append(str(expected * factorial % MOD))
    sys.stdout.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
