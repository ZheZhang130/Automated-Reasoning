import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    P = [int(input_data[i+1]) for i in range(N)]
    
    # We process insertions from N down to 1.
    # When inserting i at position P[i-1] (1-indexed), 
    # in the final array, i will be at a position that is 
    # P[i-1] - (number of elements inserted after i that are placed before it).
    # 
    # Instead of simulating forward (which is O(N^2)), we simulate backward.
    # We maintain a list of "slots" that are currently empty.
    # Initially, we have N empty slots.
    # When we consider inserting i at position P_i (1-indexed),
    # we need to find the P_i-th empty slot and place i there.
    # Then we mark that slot as filled.
    # 
    # However, a simpler way is to use a Fenwick tree or just a list of available positions.
    # Since we are filling positions, we can think of it as:
    # We have positions 1 to N. We want to assign values to these positions.
    # When we insert i at P_i, it means i will be the P_i-th element in the current array.
    # But the current array only contains elements {i, i+1, ..., N}.
    # So, if we process from N down to 1:
    #   - We have a set of available positions. Initially {1, 2, ..., N}.
    #   - For i from N down to 1:
    #       - We need to place i at the P_i-th available position.
    #       - Remove that position from the set of available positions.
    # 
    # To efficiently find the k-th available position, we can use a Fenwick tree.
    # The Fenwick tree will store 1 at each available position.
    # The sum of the tree from 1 to x gives the number of available positions <= x.
    # We want to find the smallest x such that sum(1..x) == P_i.
    
    # Build Fenwick tree for positions 1 to N
    # tree[i] stores sum of frequencies in range [i - (i&-i) + 1, i]
    # We'll use 1-based indexing for the Fenwick tree.
    
    size = N
    tree = [0] * (size + 1)
    
    def update(idx, delta):
        while idx <= size:
            tree[idx] += delta
            idx += idx & (-idx)
            
    def query(idx):
        s = 0
        while idx > 0:
            s += tree[idx]
            idx -= idx & (-idx)
        return s
    
    def find_kth(k):
        # Find smallest idx such that query(idx) == k
        # We can do this by walking the Fenwick tree
        idx = 0
        current_sum = 0
        bit_mask = 1 << (size.bit_length())
        while bit_mask > 0:
            next_idx = idx + bit_mask
            if next_idx <= size:
                if current_sum + tree[next_idx] < k:
                    idx = next_idx
                    current_sum += tree[idx]
            bit_mask >>= 1
        return idx + 1
    
    # Initialize Fenwick tree with 1 at each position
    # Instead of N updates, we can build it in O(N)
    # But O(N log N) is fine for N=5e5.
    # Actually, let's just build it properly.
    # tree[i] = sum of frequencies in range covered by i
    # Initially all positions are available, so frequency is 1.
    # We can compute tree array directly.
    # tree[i] = 1 + sum of tree[j] for j in some range?
    # Standard build: for i from 1 to N: update(i, 1)
    # But that's O(N log N). Let's do it.
    
    for i in range(1, size + 1):
        update(i, 1)
    
    result = [0] * (size + 1)
    
    # Process from N down to 1
    for i in range(N, 0, -1):
        p = P[i-1]  # P_i is 1-indexed
        pos = find_kth(p)
        result[pos] = i
        update(pos, -1)  # Mark position as filled
    
    # Output result[1] to result[N]
    print(*(result[1:]))

if __name__ == "__main__":
    solve()
