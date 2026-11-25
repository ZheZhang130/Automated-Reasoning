import sys
from bisect import bisect_left
from itertools import accumulate


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    remove, add, common = [], [], []
    for i in range(1, n + 1):
        a, b, w = data[i], data[n + i], data[2 * n + i]
        if a:
            (common if b else remove).append(w)
        elif b:
            add.append(w)

    remove.sort()
    add.sort()
    common.sort(reverse=True)
    fixed = sum(common)
    length = len(remove) + len(add)

    # Within each phase, a pair of flipped bits contributes its smaller weight.
    cost = fixed * length
    cost += sum(w * (len(remove) - 1 - i) for i, w in enumerate(remove))
    cost += sum(w * (len(add) - i) for i, w in enumerate(add))
    best = cost

    # For a given number of temporarily cleared bits, take the heaviest ones.
    # Prefix sums count the new pair contributions with the mandatory flips.
    mandatory = sorted(remove + add)
    prefix = list(accumulate(mandatory, initial=0))
    for x in common:
        k = bisect_left(mandatory, x)
        # Existing temporary clears all weigh at least x. Together with
        # mandatory weights >= x, they contribute (length - k) * x.
        # Combine this with the change in fixed cost and the new addition.
        cost += 2 * fixed + prefix[k] - (k + 1) * x
        fixed -= x
        length += 2
        if cost < best:
            best = cost

    print(best)


if __name__ == "__main__":
    main()
