import sys

MOD = 998244353


def main():
    n, m = map(int, sys.stdin.buffer.readline().split())
    s = sys.stdin.buffer.readline().strip()

    matches = [0] * 26
    for i, ch in enumerate(s):
        matches[ch - ord('a')] |= 1 << i
    masks = [mask for mask in matches if mask]
    absent = 26 - len(masks)

    # A state marks the positions where the LCS row increases.
    # Subtracting the shifted state selects the first possible increase
    # in each interval between successive increases of the old row.
    size = 1 << n
    transitions = []
    for state in range(size):
        start = (state << 1) | 1
        row = []
        for mask in masks:
            candidates = state | mask
            row.append(candidates & ~(candidates - start))
        transitions.append(row)

    dp = [0] * size
    dp[0] = 1
    for _ in range(m):
        # Letters absent from S leave every state unchanged.
        nxt = [count * absent for count in dp]
        for state, count in enumerate(dp):
            if count:
                for dest in transitions[state]:
                    nxt[dest] += count
        dp = [count % MOD for count in nxt]

    ans = [0] * (n + 1)
    for state, count in enumerate(dp):
        ans[state.bit_count()] += count
    print(*(count % MOD for count in ans))


if __name__ == "__main__":
    main()
