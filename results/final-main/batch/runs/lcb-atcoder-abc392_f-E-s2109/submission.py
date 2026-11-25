import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    P = [int(x) for x in input_data[1:]]
    
    # We process from i = N down to 1
    # At step i, we insert i at position P[i-1] (1-indexed)
    # When going backwards, we know the final position of i is P[i-1]
    # relative to the elements that were inserted AFTER i.
    
    # Let's think about it differently.
    # When we insert i at position P_i, it shifts all elements that were
    # inserted before i (and are still in the array) that are at positions >= P_i.
    # 
    # Consider the final array. The element at position k (1-indexed) in the final array
    # is the number i such that when i was inserted, it was placed at position P_i,
    # and no subsequent insertions moved it to a different relative position among the
    # elements that were inserted after i.
    #
    # Actually, let's reverse the process.
    # Start with an empty array of size N.
    # We want to place numbers 1, 2, ..., N.
    # But the operations are: insert i at P_i.
    # 
    # Key insight: 
    # When we insert i at position P_i, it becomes the P_i-th element.
    # Any element that was already in the array at position >= P_i gets shifted to position +1.
    # 
    # If we process from N down to 1:
    # At step i (going backwards), we know that i was inserted at position P_i.
    # In the final array, i will be at some position.
    # The elements that are to the right of i in the final array are exactly those
    # that were inserted AFTER i and were placed at positions >= P_i (relative to the state at step i).
    # 
    # Actually, a simpler view:
    # Let's maintain a list of "available positions" for the final array.
    # Initially, we have positions 1, 2, ..., N.
    # When we insert i at P_i (1-indexed), we are saying that i will occupy the P_i-th
    # available slot from the left.
    # Then we remove that slot.
    # 
    # Example: N=4, P = [1, 1, 2, 1]
    # i=4: P_4 = 1. We take the 1st available slot. Available: [1,2,3,4]. Take 1.
    #   So 4 goes to position 1. Remaining slots: [2,3,4].
    # i=3: P_3 = 2. We take the 2nd available slot. Available: [2,3,4]. Take 3 (which is the 2nd).
    #   So 3 goes to position 3 (in the original indexing). Remaining slots: [2,4].
    # i=2: P_2 = 1. We take the 1st available slot. Available: [2,4]. Take 2.
    #   So 2 goes to position 2. Remaining slots: [4].
    # i=1: P_1 = 1. We take the 1st available slot. Available: [4]. Take 4.
    #   So 1 goes to position 4.
    # 
    # Result: position 1 -> 4, position 2 -> 2, position 3 -> 3, position 4 -> 1.
    # Array: [4, 2, 3, 1]. Matches sample!
    #
    # Example 2: N=5, P = [1, 2, 3, 4, 5]
    # i=5: P_5=5. Available: [1,2,3,4,5]. Take 5th -> 5. Remaining: [1,2,3,4].
    # i=4: P_4=4. Available: [1,2,3,4]. Take 4th -> 4. Remaining: [1,2,3].
    # i=3: P_3=3. Available: [1,2,3]. Take 3rd -> 3. Remaining: [1,2].
    # i=2: P_2=2. Available: [1,2]. Take 2nd -> 2. Remaining: [1].
    # i=1: P_1=1. Available: [1]. Take 1st -> 1. Remaining: [].
    # Result: position 1->1, 2->2, 3->3, 4->4, 5->5. Array: [1,2,3,4,5]. Matches!
    
    # Algorithm:
    # 1. Create a list of available positions: [1, 2, ..., N]
    # 2. For i from N down to 1:
    #      pos = P[i-1]  (since P is 0-indexed in Python, P[i-1] corresponds to P_i)
    #      The actual position in the final array is available_positions[pos-1]
    #      Store result[actual_position] = i
    #      Remove the element at pos-1 from available_positions
    # 3. Print the result array.
    
    # To efficiently remove elements, we can use a Fenwick tree or a simple list if N is small.
    # But N up to 5*10^5, so O(N^2) is too slow.
    # We need O(N log N) or O(N).
    # 
    # Using a Fenwick tree (Binary Indexed Tree) to find the k-th available position.
    # Initially, all positions 1..N are available (value 1).
    # When we "remove" a position, we set its value to 0.
    # To find the k-th available position, we find the smallest index x such that sum(1..x) = k.
    # This can be done in O(log N) with binary lifting on the BIT.
    
    # Steps with BIT:
    # 1. Initialize BIT of size N with 1s.
    # 2. For i from N down to 1:
    #      k = P[i-1]
    #      Find the smallest index x such that query(x) == k.
    #      Set result[x] = i
    #      Update BIT at x by -1 (remove x).
    # 3. Print result.
    
    # BIT implementation
    bit = [0] * (N + 1)
    
    def update(idx, delta):
        while idx <= N:
            bit[idx] += delta
            idx += idx & (-idx)
            
    def query(idx):
        s = 0
        while idx > 0:
            s += bit[idx]
            idx -= idx & (-idx)
        return s
    
    # Initialize BIT with 1s at all positions 1..N
    # We can do this by updating each position, but that's O(N log N).
    # Alternatively, we can build it in O(N).
    # For simplicity and since O(N log N) is acceptable for N=5e5 (approx 10^7 ops),
    # we'll just update each. But let's do O(N) build.
    # Actually, the standard way to build a BIT from an array is:
    # for i in 1..N: bit[i] += arr[i]; j = i + (i&-i); if j<=N: bit[j] += bit[i]
    # Here arr is all 1s.
    
    # Let's just do the O(N log N) initialization for simplicity, it's fine.
    # Actually, we can initialize the BIT such that query(i) = i.
    # That means bit[i] should be such that the prefix sums are correct.
    # For an array of all 1s, the BIT structure is:
    # bit[i] = i & (-i)
    # Because the sum of 1s in the range covered by bit[i] is exactly (i & (-i)).
    # So we can initialize bit[i] = i & (-i) for i in 1..N.
    
    for i in range(1, N + 1):
        bit[i] = i & (-i)
    
    result = [0] * (N + 1)  # 1-indexed
    
    for i in range(N, 0, -1):
        k = P[i-1]  # P_i
        # Find the smallest x such that query(x) == k
        # We can use binary lifting on the BIT.
        # Start with idx = 0, and try to add powers of 2.
        idx = 0
        current_sum = 0
        # We want to find x such that sum(1..x) = k.
        # We iterate from the highest bit down to 0.
        # The maximum index is N. Let's find the highest power of 2 <= N.
        # But we can just iterate from a fixed high bit (e.g., 1<<18 for 5e5)
        
        # Binary lifting:
        # We maintain idx such that query(idx) < k.
        # Then we try to add 2^b to idx. If query(idx + 2^b) < k, we add it.
        # Finally, idx + 1 is the answer.
        
        # Determine the highest bit. 2^19 = 524288 > 5e5.
        for b in range(19, -1, -1):
            next_idx = idx + (1 << b)
            if next_idx <= N and current_sum + bit[next_idx] < k:
                idx = next_idx
                current_sum += bit[idx]
        
        # Now idx is the largest index such that query(idx) < k.
        # So the k-th available position is idx + 1.
        pos = idx + 1
        result[pos] = i
        
        # Remove this position: update(pos, -1)
        # But we need to update the BIT. The bit array is not just the raw values.
        # We need to update the BIT structure.
        # The standard update function works.
        # However, we can also update the bit array directly if we know the structure.
        # But let's use the update function for correctness.
        # But wait, the update function modifies the BIT. We need to do that.
        
        # Actually, we can update the BIT by subtracting 1 from the position pos.
        # The update function does exactly that.
        # But we need to be careful: the bit array we built initially is the BIT.
        # So we use the update function.
        
        # However, the update function is O(log N). Total time O(N log N).
        # This is acceptable.
        
        # Let's implement the update.
        # But note: the bit array we have is the BIT. We need to update it.
        # The update function:
        # while idx <= N: bit[idx] += delta; idx += idx & (-idx)
        # We need to call this.
        
        # But wait, we can also update the bit array directly without a function.
        # Let's write the update inline.
        
        idx = pos
        while idx <= N:
            bit[idx] -= 1
            idx += idx & (-idx)
    
    # Output result[1..N]
    print(*(result[1:]))

solve()
