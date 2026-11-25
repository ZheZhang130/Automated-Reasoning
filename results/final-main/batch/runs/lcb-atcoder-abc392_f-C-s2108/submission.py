import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    P = [int(x) for x in input_data[1:]]
    
    # P is 0-indexed in our list, but problem uses 1-indexed positions
    # P[i] corresponds to insertion of number i+1
    # We need to process from N down to 1
    # P[N-1] is the position for number N
    # P[0] is the position for number 1
    
    # Fenwick tree (Binary Indexed Tree) to track available slots
    # Initially all slots 1..N are available (value 1)
    # We want to find the k-th available slot (where k = P_i)
    # Then mark that slot as unavailable (subtract 1)
    
    # Build Fenwick tree
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
    
    # Initialize: all positions 1..N have value 1
    # We can build the tree in O(N) by updating each position
    # But since we start with all 1s, we can just set bit[i] = i & (-i)
    # because the sum of 1s in range [i - (i&-i) + 1, i] is exactly (i&-i)
    for i in range(1, N + 1):
        bit[i] = i & (-i)
    
    # Process from N down to 1
    # For number i (where i goes from N down to 1), the position is P[i-1]
    # We need to find the P[i-1]-th available slot
    
    result = [0] * N
    
    for i in range(N, 0, -1):
        pos = P[i-1]  # 1-indexed position for number i
        
        # Find the smallest index idx such that query(idx) >= pos
        # Using binary lifting on Fenwick tree
        idx = 0
        current_sum = 0
        bit_mask = 1 << (N.bit_length() - 1)  # Start from highest power of 2 <= N
        
        while bit_mask > 0:
            t_idx = idx + bit_mask
            if t_idx <= N and current_sum + bit[t_idx] < pos:
                idx = t_idx
                current_sum += bit[t_idx]
            bit_mask >>= 1
        
        # idx is now the largest index with sum < pos
        # So idx + 1 is the position we want
        target_idx = idx + 1
        
        result[target_idx - 1] = i
        
        # Update the Fenwick tree: subtract 1 at target_idx
        update(target_idx, -1)
    
    print(*(result))

if __name__ == "__main__":
    solve()
