import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    tree = [x & -x for x in range(n + 1)]
    answer = [0] * n
    top = 1 << (n.bit_length() - 1)

    # In reverse insertion order, each rank refers to the remaining free slots.
    for value in range(n, 0, -1):
        rank = data[value]
        pos = 0
        step = top
        while step:
            nxt = pos + step
            if nxt <= n and tree[nxt] < rank:
                rank -= tree[nxt]
                pos = nxt
            step >>= 1

        answer[pos] = value
        pos += 1
        while pos <= n:
            tree[pos] -= 1
            pos += pos & -pos

    print(' '.join(map(str, answer)))


if __name__ == '__main__':
    main()
