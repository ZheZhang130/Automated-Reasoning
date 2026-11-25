import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    P = [int(x) for x in input_data[1:]]
    
    # We process from last to first
    # When we insert i at position P_i, it shifts existing elements
    # Instead of simulating, we can think backwards:
    # The final position of each number depends on how many numbers are inserted after it
    # and where they are inserted relative to it.
    
    # Alternative approach:
    # Use a deque and simulate backwards from N to 1
    # But that's O(N^2) in worst case.
    
    # Better approach:
    # Notice that when we insert i at position P_i, it becomes the P_i-th element.
    # Elements before P_i stay before, elements after P_i stay after.
    # 
    # Key insight: Process from N down to 1.
    # Maintain a list of "slots" that will be filled.
    # Initially, we have N empty slots.
    # When we consider number i (going backwards from N to 1),
    # it should end up at position P_i in the current array.
    # But the current array has some elements already placed (for j > i).
    # 
    # Actually, let's think differently:
    # When we insert i at position P_i, it means in the final array,
    # there will be exactly P_i - 1 elements before i that were inserted AFTER i.
    # 
    # So if we process from N down to 1:
    # - We maintain a list of available positions (initially [0, 1, 2, ..., N-1])
    # - For number i, we need to place it at the (P_i - 1)-th available position
    # - Then we remove that position from the list
    # 
    # This works because:
    # - When we insert i at position P_i, it becomes the P_i-th element.
    # - The elements that will be before i in the final array are exactly those
    #   that are inserted AFTER i and have position <= P_i.
    # - By processing backwards, we're placing numbers that were inserted later.
    
    # Let's implement this:
    available = list(range(N))  # positions 0 to N-1
    result = [0] * N
    
    for i in range(N, 0, -1):
        p = P[i-1]  # P is 1-indexed, convert to 0-indexed count
        # We need the (p-1)-th element in available
        pos = available.pop(p-1)
        result[pos] = i
    
    print(' '.join(map(str, result)))

if __name__ == "__main__":
    solve()
