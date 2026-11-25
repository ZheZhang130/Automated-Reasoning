import sys


def main():
    n, *a = map(int, sys.stdin.buffer.read().split())
    size = 1 << n
    sums = [0] * size
    for mask in range(1, size):
        bit = mask & -mask
        sums[mask] = sums[mask ^ bit] + a[bit.bit_length() - 1]

    values = set()
    add = values.add

    def visit(mask, xor):
        # Finish with one block containing all the remaining bags.
        add(xor ^ sums[mask])

        # Put the lowest remaining bit in the next block. Every
        # nonempty submask of the other bits can be left for later.
        rest = mask & (mask - 1)
        left = rest
        while left:
            visit(left, xor ^ sums[mask ^ left])
            left = (left - 1) & rest

    visit(size - 1, 0)
    print(len(values))


if __name__ == "__main__":
    main()
