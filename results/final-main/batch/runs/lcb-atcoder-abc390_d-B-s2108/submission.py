import sys
from functools import lru_cache


def main():
    n, *stones = map(int, sys.stdin.buffer.read().split())
    size = 1 << n
    sums = [0] * size
    for mask in range(1, size):
        first = mask & -mask
        sums[mask] = sums[mask ^ first] + stones[first.bit_length() - 1]

    # In each partition, choose the group containing the first remaining bag.
    # Cache the possible XORs of small remainders, which recur across branches.
    @lru_cache(None)
    def small(mask):
        if not mask:
            return (0,)
        first = mask & -mask
        rest = mask ^ first
        tail = rest
        values = set()
        while True:
            group_sum = sums[mask ^ tail]
            for value in small(tail):
                values.add(group_sum ^ value)
            if not tail:
                return tuple(values)
            tail = (tail - 1) & rest

    results = set()
    add = results.add

    def enumerate_xors(mask, prefix):
        if mask.bit_count() <= 5:
            for value in small(mask):
                add(prefix ^ value)
            return
        rest = mask & (mask - 1)
        tail = rest
        while True:
            enumerate_xors(tail, prefix ^ sums[mask ^ tail])
            if not tail:
                return
            tail = (tail - 1) & rest

    enumerate_xors(size - 1, 0)
    print(len(results))


if __name__ == "__main__":
    main()
