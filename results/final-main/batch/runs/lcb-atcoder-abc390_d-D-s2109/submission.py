import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    A = list(map(int, input_data[1:N+1]))
    
    total_mask = (1 << N) - 1
    
    # Precompute sums for each mask
    sum_mask = [0] * (1 << N)
    for i in range(N):
        bit = 1 << i
        for mask in range(1 << N):
            if mask & bit:
                sum_mask[mask] = sum_mask[mask ^ bit] + A[i]
            else:
                sum_mask[mask] = sum_mask[mask]
    
    # dp[mask] = set of possible XOR values for partitioning 'mask' into any number of non-empty groups
    dp = [set() for _ in range(1 << N)]
    dp[0] = {0}
    
    for mask in range(1, 1 << N):
        # Find the smallest bit in mask
        i = (mask & -mask).bit_length() - 1
        rest = mask ^ (1 << i)
        s_base = 1 << i
        # Iterate over all submasks t of rest
        t = rest
        while True:
            s = s_base | t
            rest_sub = mask ^ s
            if rest_sub in dp:
                for x in dp[rest_sub]:
                    dp[mask].add(x ^ sum_mask[s])
            t = (t - rest) & rest
            if t == rest:
                break
    
    # The answer is the size of dp[total_mask]
    print(len(dp[total_mask]))

if __name__ == "__main__":
    solve()
