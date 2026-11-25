import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    A = list(map(int, data[1:N+1]))
    
    # Precompute sums for all masks
    sum_mask = [0] * (1 << N)
    for mask in range(1, 1 << N):
        i = (mask & -mask).bit_length() - 1
        sum_mask[mask] = sum_mask[mask ^ (1 << i)] + A[i]
    
    # DP: dp[mask] = set of XOR values for all partitions of mask
    dp = [set() for _ in range(1 << N)]
    dp[0] = {0}
    
    for mask in range(1, 1 << N):
        low_bit = (mask & -mask).bit_length() - 1
        sub = mask
        while sub:
            if sub & (1 << low_bit):
                rest = mask ^ sub
                s = sum_mask[sub]
                for x in dp[rest]:
                    dp[mask].add(s ^ x)
            sub = (sub - 1) & mask
    
    print(len(dp[(1 << N) - 1]))

if __name__ == "__main__":
    solve()
