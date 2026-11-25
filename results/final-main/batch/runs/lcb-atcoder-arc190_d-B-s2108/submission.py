import sys
from operator import mul


def matmul(a, b, p):
    columns = list(zip(*b))
    return [[sum(map(mul, row, col)) % p for col in columns] for row in a]


def matpow(a, e, p):
    result = None
    while e:
        if e & 1:
            result = a if result is None else matmul(result, a, p)
        e >>= 1
        if e:
            a = matmul(a, a, p)
    return result


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n, p = data[:2]
    if p <= 2:
        # For p=2 there is exactly one completion, the all-ones matrix.
        print('\n'.join([' '.join([str(n % p)] * n)] * n))
        return

    a = [data[k:k+n] for k in range(2, len(data), n)]
    ans = matpow(a, p, p)
    zero_loops = [int(a[i][i] == 0) for i in range(n)]
    sign = -1 if data[2:].count(0) % 2 else 1

    # Divide the sum by the number of completions temporarily. Each
    # replaced entry then has moment 1 for exponents divisible by p-1
    # and moment 0 otherwise. A surviving walk using any replaced entry
    # must use that edge exactly p-1 times and have just one fixed edge.
    # This gives loops at either end, or (only at p=3) an alternating walk.
    for i, row in enumerate(ans):
        for j, value in enumerate(row):
            value += (zero_loops[i] + zero_loops[j]) * a[i][j]
            if p == 3 and i != j and a[i][j] == 0:
                value += a[j][i]
            row[j] = sign * value % p

    sys.stdout.write('\n'.join(' '.join(map(str, row)) for row in ans) + '\n')


if __name__ == '__main__':
    main()
