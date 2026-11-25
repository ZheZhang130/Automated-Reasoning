import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    down_a, down_b, common = [], [], []
    total_a = total_b = 0
    for i in range(1, n + 1):
        a, b, c = data[i], data[n + i], data[2 * n + i]
        if a:
            total_a += c
        if b:
            total_b += c
        if a and b:
            common.append(c)
        elif a:
            down_a.append(c)
        elif b:
            down_b.append(c)

    down_a.sort(reverse=True)
    down_b.sort(reverse=True)
    common.sort(reverse=True)

    # Remove bits from A in descending weight order. The insertion
    # phase is the reversal of descending removals from B.
    cost = 0
    remaining = total_a
    for c in down_a:
        remaining -= c
        cost += remaining
    remaining = total_b
    for c in down_b:
        cost += remaining
        remaining -= c

    best = cost
    ia = ib = 0
    prefix_a = prefix_b = chosen_weight = 0
    na, nb = len(down_a), len(down_b)
    for c in common:
        while ia < na and down_a[ia] >= c:
            prefix_a += down_a[ia]
            ia += 1
        while ib < nb and down_b[ib] >= c:
            prefix_b += down_b[ib]
            ib += 1

        # The new removal lowers every later cost by c, and adds its
        # own cost (after the flip on A, before the flip on reversed B).
        cost += total_a - prefix_a - chosen_weight - c * (na - ia + 1)
        cost += total_b - prefix_b - chosen_weight - c * (nb - ib)
        chosen_weight += c
        if cost < best:
            best = cost

    print(best)


if __name__ == "__main__":
    main()
