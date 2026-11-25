import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    down, up, common = [], [], []
    for i in range(1, n + 1):
        a, b, w = data[i], data[n + i], data[2 * n + i]
        if a:
            if b:
                common.append(w)
            else:
                down.append(w)
        elif b:
            up.append(w)

    down.sort(reverse=True)
    up.sort(reverse=True)
    common.sort(reverse=True)

    # For a fixed set of flips, perform all decreases first (largest
    # first), then all increases (smallest first). In descending order,
    # the weights have coefficients 0,1,... for down and 1,2,... for up.
    weighted = sum(i * w for i, w in enumerate(down))
    weighted += sum(i * w for i, w in enumerate(up, 1))
    remaining = sum(common)
    moves = len(down) + len(up)
    best = weighted + moves * remaining

    # If k common bits are turned off temporarily, they can be the k
    # heaviest: exchanging a lighter chosen bit for a heavier unchosen
    # one reduces the state weight throughout that off interval.
    p = q = 0
    tail_down, tail_up = sum(down), sum(up)
    for k, w in enumerate(common):
        while p < len(down) and down[p] >= w:
            tail_down -= down[p]
            p += 1
        while q < len(up) and up[q] >= w:
            tail_up -= up[q]
            q += 1

        # Insert w in each ranked list; every fixed weight behind it
        # has its coefficient increased by one.
        weighted += (p + q + 2 * k + 1) * w + tail_down + tail_up
        remaining -= w
        moves += 2
        best = min(best, weighted + moves * remaining)

    print(best)


if __name__ == "__main__":
    main()
