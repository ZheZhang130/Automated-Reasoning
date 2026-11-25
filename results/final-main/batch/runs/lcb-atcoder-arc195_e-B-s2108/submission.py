import sys

MOD = 998244353


def main():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    n = next(data)
    q = next(data)
    weights = [0, 0] + [next(data) for _ in range(n - 1)]

    inv = [0] * (n + 1)
    inv[1] = 1
    prefix = [0] * (n + 1)
    base = [0] * (n + 1)
    total = 0
    factorial = 1
    for i in range(2, n + 1):
        inv[i] = -(MOD // i) * inv[MOD % i] % MOD
        factorial = factorial * (i - 1) % MOD

        # Sum of expected distances from i to vertices below i.
        row = ((i - 1) * weights[i] + total * inv[i - 1]) % MOD
        total = (total + 2 * row) % MOD

        # For j > i, adding vertex j increases the row average
        # over vertices 1 through j by weights[j] / j.
        prefix[i] = (prefix[i - 1] + weights[i] * inv[i]) % MOD
        base[i] = (row * inv[i] - prefix[i]) % MOD

    out = []
    for _ in range(q):
        u = next(data)
        v = next(data)
        expected = weights[v] + base[u] + prefix[v - 1]
        out.append(str(expected * factorial % MOD))
    sys.stdout.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
