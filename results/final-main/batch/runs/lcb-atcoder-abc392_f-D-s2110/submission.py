import sys
from collections import deque

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    P = [int(x) for x in data[1:N+1]]
    
    # We process insertions from N down to 1.
    # At step i (1-indexed), we insert i at position P[i-1] (1-indexed).
    # When going backwards, we know the final position of i in the array of size N.
    # Specifically, if we consider the array of size N, and we remove elements
    # from N down to 1, the position of i in the final array is determined by
    # how many elements are still "to the right" of it.
    #
    # Key insight: When we insert i at position P_i (1-indexed) in an array of size i,
    # and then later insert j > i, if j is inserted at a position <= P_i, then i
    # gets shifted to the right. If j is inserted at a position > P_i, i stays at
    # its relative position.
    #
    # Working backwards: Start with an empty array of size N.
    # For i from N down to 1:
    #   The element i should end up at a position such that when we consider only
    #   the elements >= i, it is at the P_i-th position among them.
    #   But since we are filling the array from right to left in terms of positions,
    #   we can maintain a list of available positions.
    #
    # Alternative approach (simpler):
    # Maintain a list of "slots" (positions) that are currently empty.
    # Initially, for N elements, we have positions 0 to N-1.
    # When we process i from N down to 1:
    #   We need to place i at the P_i-th position among the currently available slots.
    #   But wait, the logic is: at step i (forward), we insert i at P_i-th position.
    #   This means in the final array, i will be at some position.
    #   If we go backwards, we can determine the final position of i.
    #
    # Let's use the "available positions" method:
    # Start with a list of positions: [0, 1, 2, ..., N-1]
    # For i from N down to 1:
    #   We want to place i at the (P_i - 1)-th available position (0-indexed).
    #   Why? Because when we insert i at P_i-th position in an array of size i,
    #   it means there are P_i - 1 elements before it. In the final array,
    #   the elements that will be before i are exactly those that were inserted
    #   at positions <= P_i for steps > i.
    #   So, if we consider the final array, and we remove elements N, N-1, ..., i+1,
    #   then i should be at the P_i-th position among the remaining elements.
    #   Therefore, we pick the (P_i - 1)-th available position and place i there.
    #   Then we remove that position from the available list.
    #
    # Example N=4, P=[1,1,2,1]
    # Available positions: [0, 1, 2, 3]
    # i=4, P_4=1: place 4 at index 0 of available -> result[0] = 4, available = [1,2,3]
    # i=3, P_3=2: place 3 at index 1 of available -> result[1] = 3, available = [1,2]
    # i=2, P_2=1: place 2 at index 0 of available -> result[1] = 2? Wait, available[0]=1 -> result[1]=2, available=[2]
    # i=1, P_1=1: place 1 at index 0 of available -> result[2]=1, available=[]
    # But we have 4 positions, we need to fill all.
    # Let's re-trace:
    # available = [0,1,2,3]
    # i=4, P=1: take available[0]=0, result[0]=4, available=[1,2,3]
    # i=3, P=2: take available[1]=2, result[2]=3, available=[1,3]
    # i=2, P=1: take available[0]=1, result[1]=2, available=[3]
    # i=1, P=1: take available[0]=3, result[3]=1, available=[]
    # result = [4, 2, 3, 1] -> matches sample!
    
    available = list(range(N))
    result = [0] * N
    
    for i in range(N, 0, -1):
        p = P[i-1]  # P_i is 1-indexed
        idx = p - 1
        pos = available.pop(idx)
        result[pos] = i
    
    print(*(result))

if __name__ == "__main__":
    solve()
