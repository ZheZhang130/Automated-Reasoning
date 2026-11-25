import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    P = [int(x) for x in data[1:]]
    
    # BIT to track empty slots
    bit = [0] * (N + 1)
    
    def update(i, delta):
        while i <= N:
            bit[i] += delta
            i += i & (-i)
    
    def query(i):
        s = 0
        while i > 0:
            s += bit[i]
            i -= i & (-i)
        return s
    
    # Initialize: all positions are empty
    for i in range(1, N + 1):
        update(i, 1)
    
    result = [0] * N
    
    # Process from last to first (numbers N down to 1)
    for i in range(N - 1, -1, -1):
        p = P[i]  # 1-indexed position for number (i+1)
        
        # Find the p-th empty slot using binary lifting on BIT
        idx = 0
        current_sum = 0
        for bit_idx in range(N.bit_length(), -1, -1):
            next_idx = idx + (1 << bit_idx)
            if next_idx <= N and current_sum + bit[next_idx] < p:
                idx = next_idx
                current_sum += bit[idx]
        
        pos = idx + 1  # 1-indexed position of p-th empty slot
        
        # Mark as occupied
        update(pos, -1)
        result[pos - 1] = i + 1
    
    print(*(result))

if __name__ == "__main__":
    solve()
