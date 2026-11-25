import sys

MOD = 998244353


def main():
    n, m = map(int, sys.stdin.buffer.readline().split())
    s = sys.stdin.buffer.readline().strip()

    masks = {}
    for i, c in enumerate(s):
        masks[c] = masks.get(c, 0) | (1 << i)

    size = 1 << n
    absent = 26 - len(masks)
    transitions = []
    # Bit i records whether the LCS increases from prefix i to i+1.
    for state in range(size):
        shifted = (state << 1) | 1
        row = []
        for mask in masks.values():
            x = state | mask
            row.append(x & ~(x - shifted))
        transitions.append(row)

    dp = [0] * size
    dp[0] = 1
    for _ in range(m):
        new = [v * absent for v in dp]
        for state, ways in enumerate(dp):
            if ways:
                for target in transitions[state]:
                    new[target] += ways
        dp = [v % MOD for v in new]

    ans = [0] * (n + 1)
    for state, ways in enumerate(dp):
        ans[state.bit_count()] += ways
    print(*(v % MOD for v in ans))


if __name__ == "__main__":
    main()
