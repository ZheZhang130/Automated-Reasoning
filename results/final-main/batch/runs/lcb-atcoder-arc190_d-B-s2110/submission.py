import sys
from operator import mul


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return
    n, p = data[:2]
    if p <= 2:
        # For p=2 every entry of every completed matrix is one.
        row = ' '.join([str(n % 2 if p == 2 else 0)] * n)
        sys.stdout.write((row + '\n') * n)
        return

    a = [data[2 + i*n:2 + (i+1)*n] for i in range(n)]
    zeros = sum(row.count(0) for row in a)

    # Pack each row of the right operand into an integer. Each lane
    # holds an entire dot product without carrying into the next lane.
    width = ( (n * (p-1)**2).bit_length() + 7 ) // 8
    offsets = range(0, width*n, width)

    def matmul(x, y):
        packed = [
            int.from_bytes(b''.join(v.to_bytes(width, 'little') for v in row),
                           'little')
            for row in y
        ]
        result = []
        for row in x:
            raw = sum(map(mul, row, packed)).to_bytes(n*width, 'little')
            result.append([
                int.from_bytes(raw[k:k+width], 'little') % p for k in offsets
            ])
        return result

    power = p
    base = a
    ans = None
    while power:
        if power & 1:
            ans = base if ans is None else matmul(ans, base)
        power >>= 1
        if power:
            base = matmul(base, base)

    # Dividing the sum by (p-1)^zeros, the contribution of a walk
    # vanishes unless each used zero edge has multiplicity divisible
    # by p-1. A walk of length p can use at most one such edge.
    zero_loop = [a[i][i] == 0 for i in range(n)]
    sign = -1 if zeros & 1 else 1
    lines = []
    for i in range(n):
        row = []
        for j in range(n):
            # A repeated loop can precede or follow the remaining edge.
            value = ans[i][j] + a[i][j] * (zero_loop[i] + zero_loop[j])
            # Only for p=3 can a non-loop be repeated, via a return edge.
            if p == 3 and i != j and a[i][j] == 0:
                value += a[j][i]
            row.append(str(sign * value % p))
        lines.append(' '.join(row))
    sys.stdout.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
