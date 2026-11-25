import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]

    # All final positions start free. Each Fenwick node initially
    # counts every position in its interval.
    tree = [i & -i for i in range(n + 1)]
    highest_bit = 1 << (n.bit_length() - 1)
    answer = [0] * n

    for value in range(n, 0, -1):
        # The free positions, in order, hold the array just after
        # inserting value, so its position is the rank-th free slot.
        rank = data[value]
        pos = 0
        bit = highest_bit
        while bit:
            nxt = pos + bit
            if nxt <= n and tree[nxt] < rank:
                rank -= tree[nxt]
                pos = nxt
            bit >>= 1

        answer[pos] = value
        pos += 1
        while pos <= n:
            tree[pos] -= 1
            pos += pos & -pos

    sys.stdout.write(' '.join(map(str, answer)) + '\n')


if __name__ == '__main__':
    main()
