import sys
from math import factorial


def solve(n, mod):
    h = n // 2
    edges = n * (n - 1) // 2
    # The root misses the other h-1 even-distance vertices.
    degree = edges - (h - 1) - (n - 1)

    # A state is (even vertices used, odd vertices used, last size,
    # last parity).  Construct the DAG in increasing order of vertices used.
    start = (1, 0, 1, 0)
    levels = [{} for _ in range(n + 1)]
    levels[1][start] = 0
    incoming = [[]]
    order = []
    finals = []
    stride = h + 1
    for total in range(1, n + 1):
        for (e, o, a, parity), idx in levels[total].items():
            if total == n:
                finals.append(idx)
                continue
            if idx:
                order.append(idx)
            remaining = h - (e if parity else o)
            for b in range(1, remaining + 1):
                ne, no = (e + b, o) if parity else (e, o + b)
                if total + b != n and (no if parity else ne) == h:
                    continue
                state = (ne, no, b, 1 - parity)
                level = levels[total + b]
                dest = level.get(state)
                if dest is None:
                    dest = len(incoming)
                    level[state] = dest
                    incoming.append([])
                incoming[dest].append((idx, a * stride + b))

    schedule = [(idx, incoming[idx]) for idx in order + finals]
    invfac = [pow(factorial(i), -1, mod) for i in range(h + 1)]
    label_factor = factorial(n - 1) % mod
    values = [0] * len(incoming)
    values[0] = 1
    weight = [0] * (stride * stride)
    samples = []
    for x in range(degree + 1):
        y = x + 1
        layer = [1] * stride
        for b in range(1, stride):
            layer[b] = pow(y, b * (b - 1) // 2, mod) * invfac[b] % mod
        t = 0
        for a in range(1, stride):
            # t = ((1+x)^a - 1)/x as a polynomial, even at x=0.
            t = (t * y + 1) % mod
            power = 1
            base = a * stride
            for b in range(1, stride):
                power = power * t % mod
                weight[base + b] = power * layer[b] % mod
        for idx, terms in schedule:
            val = 0
            for parent, w in terms:
                val += values[parent] * weight[w]
            values[idx] = val % mod
        samples.append(sum(values[i] for i in finals) * label_factor % mod)

    # Newton interpolation on the consecutive points 0,1,...,degree.
    newton = [samples[0]]
    invfact = 1
    for k in range(1, degree + 1):
        invfact = invfact * pow(k, -1, mod) % mod
        for i in range(degree + 1 - k):
            samples[i] = (samples[i + 1] - samples[i]) % mod
        newton.append(samples[0] * invfact % mod)

    coeff = [newton[-1]]
    for k in range(degree - 1, -1, -1):
        coeff.append(coeff[-1])
        for i in range(len(coeff) - 2, 0, -1):
            coeff[i] = (coeff[i - 1] - k * coeff[i]) % mod
        coeff[0] = (newton[k] - k * coeff[0]) % mod
    return coeff + [0] * (h - 1)


if __name__ == "__main__":
    n, p = map(int, sys.stdin.buffer.read().split())
    print(*solve(n, p))
