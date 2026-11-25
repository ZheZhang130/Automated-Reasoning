import sys

MOD = 998244353


def main():
    n, m = map(int, sys.stdin.buffer.readline().split())
    s = sys.stdin.buffer.readline().strip()

    masks = {}
    for i, c in enumerate(s):
        masks[c] = masks.get(c, 0) | (1 << i)

    size = 1 << n
    transitions = []
    for state in range(size):
        shifted = (state << 1) | 1
        row = []
        for mask in masks.values():
            # A set bit marks an increase between adjacent LCS prefix lengths.
            x = state | mask
            row.append(x & ~(x - shifted))
        transitions.append(row)

    absent = 26 - len(masks)
    dp = [0] * size
    dp[0] = 1
    for _ in range(m):
        # Letters absent from S leave every LCS prefix length unchanged.
        nxt = [absent * count for count in dp]
        for count, row in zip(dp, transitions):
            if count:
                for dest in row:
                    nxt[dest] += count
        dp = [count % MOD for count in nxt]

    ans = [0] * (n + 1)
    for state, count in enumerate(dp):
        ans[state.bit_count()] += count
    print(*(count % MOD for count in ans))


if __name__ == "__main__":
    main()
