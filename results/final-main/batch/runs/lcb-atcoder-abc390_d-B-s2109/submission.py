import sys


def main():
    n, *stones = map(int, sys.stdin.buffer.read().split())
    size = 1 << n
    sums = [0] * size
    for mask in range(1, size):
        bit = mask & -mask
        sums[mask] = sums[mask ^ bit] + stones[bit.bit_length() - 1]

    results = set()
    add = results.add

    def visit(mask, value):
        # Take the entire remainder as one group.
        add(value ^ sums[mask])

        # Otherwise, keep the lowest bit in the next group and
        # choose a nonempty remainder from the other bits.
        free = mask & (mask - 1)
        rest = free
        while rest:
            visit(rest, value ^ sums[mask ^ rest])
            rest = (rest - 1) & free

    visit(size - 1, 0)
    print(len(results))


if __name__ == "__main__":
    main()
