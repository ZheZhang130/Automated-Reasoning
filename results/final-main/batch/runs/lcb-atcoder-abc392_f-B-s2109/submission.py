import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    base = 1 << (n - 1).bit_length()
    answer = [0] * n

    # Initially all leaves are free. Padding leaves lie after the real
    # positions, so no requested rank can select one of them.
    free = [0]
    width = 1
    while width <= base:
        free.extend([base // width] * width)
        width <<= 1

    for value in range(n, 0, -1):
        rank = data[value]
        node = 1
        # Only counts of left children are needed to navigate the tree.
        while node < base:
            left = node << 1
            count = free[left]
            if rank <= count:
                free[left] = count - 1
                node = left
            else:
                rank -= count
                node = left + 1
        answer[node - base] = value

    sys.stdout.write(" ".join(map(str, answer)) + "\n")


if __name__ == "__main__":
    main()
