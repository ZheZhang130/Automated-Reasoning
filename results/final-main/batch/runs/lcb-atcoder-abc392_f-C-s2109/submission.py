import sys

# Increase recursion depth just in case, though we use iterative approach
sys.setrecursionlimit(2000)

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    P = [int(x) for x in input_data[1:]]
    
    # P is 1-indexed in problem, but we'll use 0-indexed internally
    # P[i] corresponds to insertion of number i+1
    # We need to process from N down to 1
    
    # Fenwick tree (Binary Indexed Tree) to track available slots
    # Initially all slots 1..N are available (value 1)
    # We need to find the k-th available slot (where k = P[i-1])
    # and mark it as unavailable (set value to 0)
    
    # BIT array (1-indexed)
    bit = [0] * (N + 1)
    
    def update(idx, delta):
        """Add delta to element at idx (1-indexed)"""
        while idx <= N:
            bit[idx] += delta
            idx += idx & (-idx)
    
    def query(idx):
        """Return prefix sum up to idx (1-indexed)"""
        s = 0
        while idx > 0:
            s += bit[idx]
            idx -= idx & (-idx)
        return s
    
    def find_kth(k):
        """Find the smallest index such that prefix sum >= k"""
        # Using binary lifting on BIT
        idx = 0
        current_sum = 0
        # Start from highest power of 2 <= N
        bit_mask = 1 << (N.bit_length() - 1)
        while bit_mask > 0:
            t_idx = idx + bit_mask
            if t_idx <= N and current_sum + bit[t_idx] < k:
                idx = t_idx
                current_sum += bit[idx]
            bit_mask >>= 1
        return idx + 1
    
    # Initialize BIT with all 1s
    # We can do this by building in O(N)
    # bit[i] stores sum of range [i - (i&-i) + 1, i]
    # For initial state where all positions have 1:
    # bit[i] = i & -i
    for i in range(1, N + 1):
        bit[i] = i & (-i)
    
    # Process from N down to 1
    # P[i-1] is the position for number i (1-indexed)
    result = [0] * N
    
    for i in range(N, 0, -1):
        pos = P[i-1]  # 1-indexed position
        slot = find_kth(pos)  # Find the slot index (1-indexed)
        result[slot - 1] = i
        update(slot, -1)  # Mark slot as unavailable
    
    # Output result
    print(' '.join(map(str, result)))

if __name__ == '__main__':
    solve()
