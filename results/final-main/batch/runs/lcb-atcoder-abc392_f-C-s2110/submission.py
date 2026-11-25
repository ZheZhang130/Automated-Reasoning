import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    P = [int(x) for x in input_data[1:]]
    
    # P is 0-indexed in our list, but problem uses 1-indexed P_i for i=1..N
    # So P[i-1] corresponds to P_i for number i+1
    # We need to process from N down to 1
    # P[N-1] is for number N, P[N-2] for number N-1, etc.
    
    # Fenwick tree (Binary Indexed Tree)
    # We want to find the k-th active position (where active means value 1)
    # Initially all positions 1..N are active (value 1)
    # When we place a number, we set that position to 0 (inactive)
    
    # BIT array (1-indexed internally)
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
    
    # Build initial BIT with all 1s
    # Instead of N updates, we can build in O(N)
    # bit[i] stores sum of range [i - (i&-i) + 1, i]
    # Initially all positions are 1, so bit[i] = i & (-i)
    for i in range(1, N + 1):
        bit[i] = i & (-i)
    
    # Result array (0-indexed, but we'll fill positions 0..N-1)
    result = [0] * N
    
    # Process from N down to 1
    # For number i (from N down to 1), its position is P[i-1] (which is 1-indexed rank among active slots)
    for i in range(N, 0, -1):
        p = P[i-1]  # 1-indexed rank
        
        # Find the position with cumulative sum = p
        # Using binary lifting on BIT
        idx = 0
        current_sum = 0
        bit_mask = 1 << (N.bit_length() - 1)  # Start from highest power of 2 <= N
        
        while bit_mask > 0:
            t_idx = idx + bit_mask
            if t_idx <= N and current_sum + bit[t_idx] < p:
                idx = t_idx
                current_sum += bit[idx]
            bit_mask >>= 1
        
        # idx is now the largest index such that sum[1..idx] < p
        # So the p-th active element is at idx + 1
        pos = idx + 1
        
        # Place i at this position (convert to 0-indexed)
        result[pos - 1] = i
        
        # Mark this position as inactive (subtract 1)
        update(pos, -1)
    
    # Output result
    print(' '.join(map(str, result)))

if __name__ == "__main__":
    solve()
