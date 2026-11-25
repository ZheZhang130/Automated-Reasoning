import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n, p = data[:2]
    a = [data[2+i*n:2+(i+1)*n] for i in range(n)]

    if p == 2:
        # There is just one completion, the all-ones matrix.
        line = ' '.join([str(n % 2)] * n)
        print('\n'.join([line] * n))
        return

    # Pack each right-hand row into base-256**width digits.
    # No dot product can carry into the neighboring digit.
    width = max(1, ((n * (p-1)**2).bit_length() + 7) // 8)
    offsets = range(0, n * width, width)

    def multiply(x, y):
        packed = [
            int.from_bytes(b''.join(v.to_bytes(width, 'little') for v in row),
                           'little')
            for row in y
        ]
        result = []
        for row in x:
            value = sum(u * v for u, v in zip(row, packed) if u)
            raw = value.to_bytes(n * width, 'little')
            result.append([
                int.from_bytes(raw[k:k+width], 'little') % p for k in offsets
            ])
        return result

    result = None
    base = a
    exponent = p
    while exponent:
        if exponent & 1:
            result = base if result is None else multiply(result, base)
        exponent >>= 1
        if exponent:
            base = multiply(base, base)

    # In the walk expansion, summing each replacement variable over
    # nonzero residues gives -1 for multiplicity divisible by p-1
    # (including zero) and 0 otherwise. A surviving walk that uses a
    # replacement edge has p-1 copies of it and one fixed edge.
    # A loop can precede or follow that fixed edge. A nonloop can only
    # occur twice, for p=3, with the reverse edge between its copies.
    diag_zero = [a[i][i] == 0 for i in range(n)]
    sign = -1 if sum(row.count(0) for row in a) % 2 else 1
    out = []
    for i in range(n):
        row = []
        for j in range(n):
            total = result[i][j] + a[i][j] * (diag_zero[i] + diag_zero[j])
            if p == 3 and i != j and a[i][j] == 0:
                total += a[j][i]
            row.append(str(sign * total % p))
        out.append(' '.join(row))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
