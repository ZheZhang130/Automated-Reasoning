import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    M = int(input_data[1])
    S = input_data[2]
    
    MOD = 998244353
    
    # Precompute next_state[mask][char]
    # mask is an integer from 0 to 2^N - 1
    # char is 0..25
    num_states = 1 << N
    next_state = [[0] * 26 for _ in range(num_states)]
    
    for mask in range(num_states):
        # Decode mask into a row: row[i] = row[i-1] + (1 if bit i-1 is set else 0)
        row = [0] * (N + 1)
        for i in range(N):
            if (mask >> i) & 1:
                row[i+1] = row[i] + 1
            else:
                row[i+1] = row[i]
        
        # Now for each char, compute the next row
        for c in range(26):
            new_row = [0] * (N + 1)
            for i in range(N):
                if S[i] == chr(ord('a') + c):
                    new_row[i+1] = max(row[i+1], new_row[i] + 1)
                else:
                    new_row[i+1] = row[i+1]
            
            # Encode new_row into a mask
            new_mask = 0
            for i in range(N):
                diff = new_row[i+1] - new_row[i]
                if diff == 1:
                    new_mask |= (1 << i)
            next_state[mask][c] = new_mask
    
    # DP: count[mask] = number of strings of current length that result in this mask
    count = [0] * num_states
    count[0] = 1
    
    for step in range(M):
        new_count = [0] * num_states
        for mask in range(num_states):
            if count[mask] == 0:
                continue
            c_count = count[mask]
            for c in range(26):
                next_mask = next_state[mask][c]
                new_count[next_mask] = (new_count[next_mask] + c_count) % MOD
        count = new_count
    
    # Aggregate answers
    ans = [0] * (N + 1)
    for mask in range(num_states):
        if count[mask] == 0:
            continue
        bits = bin(mask).count('1')
        ans[bits] = (ans[bits] + count[mask]) % MOD
    
    print(" ".join(str(x) for x in ans))

if __name__ == "__main__":
    solve()
