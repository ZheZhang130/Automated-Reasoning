import sys
from collections import deque

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    P = [int(x) for x in data[1:N+1]]
    
    # We simulate the process in reverse:
    # Start with an empty array of size N (all positions empty)
    # When we insert i at position P[i-1] (0-indexed: P[i-1]-1),
    # we are placing i into the array.
    # But simulating forward is O(N^2) which is too slow for N=5e5.
    #
    # Reverse simulation idea:
    # Consider the final array. The last element inserted is N, placed at position P[N-1].
    # The element before that is N-1, placed at position P[N-2] in the array that existed at that time.
    #
    # Key insight: 
    # When we insert i at position P_i (1-indexed), it means i will be at index P_i-1 (0-indexed)
    # in the current array. The elements that were already there are shifted.
    #
    # Reverse approach:
    # Start with an array of size N, all marked as empty.
    # Process from i = N down to 1.
    # At step i, we want to place i at a position such that when we later insert i-1, etc.,
    # the relative positions work out.
    #
    # Actually, a better reverse simulation:
    # Maintain a list of "available slots" (indices) in the final array.
    # Initially, all indices 0 to N-1 are available.
    # When we consider inserting i at position P_i (1-indexed), 
    # we need to pick the P_i-th available slot (0-indexed: P_i-1) and place i there.
    # Then that slot is no longer available.
    #
    # Example: N=4, P=[1,1,2,1]
    # Available slots: [0,1,2,3]
    # i=4, P[3]=1 -> pick 1st available (index 0) -> place 4 at slot 0. Available: [1,2,3]
    # i=3, P[2]=2 -> pick 2nd available (index 1) -> place 3 at slot 1. Available: [2,3]
    # i=2, P[1]=1 -> pick 1st available (index 0) -> place 2 at slot 0. Available: [3]
    # i=1, P[0]=1 -> pick 1st available (index 0) -> place 1 at slot 0. Available: []
    # Result: [4,3,2,1] -> but expected is [4,2,3,1]. Hmm, this doesn't match.
    #
    # Let me re-think.
    # The issue is that the "available slots" approach doesn't directly map because
    # the positions are relative to the current array size, not the final array.
    #
    # Correct reverse simulation:
    # We maintain a list of positions that are "free" in the final array.
    # But actually, we can think of it as: 
    # The last operation (inserting N) places N at position P[N-1] in an array of size N.
    # So N is at index P[N-1]-1 in the final array.
    # Then for N-1, it was inserted into an array of size N-1 at position P[N-2].
    # But in the final array, the positions of elements inserted before N are shifted if N was inserted before them? 
    # No, N is inserted last, so it doesn't shift anyone. But earlier insertions are shifted by later ones.
    #
    # Actually, the reverse approach is:
    # Start with an array of size N, all empty.
    # Process from i = N down to 1.
    # At step i, we want to place i at a position such that if we consider only the elements 1..i,
    # i is at the P_i-th position among them.
    # 
    # We maintain a list of "gaps" or "available positions" in the final array.
    # Initially, we have N gaps: [0, 1, 2, ..., N-1].
    # When we place i, we choose the (P_i)-th gap (0-indexed: P_i-1) and place i there, then remove that gap.
    #
    # Let's trace with N=4, P=[1,1,2,1]:
    # Gaps: [0,1,2,3]
    # i=4, P[3]=1 -> choose 1st gap (0) -> result[0]=4, gaps=[1,2,3]
    # i=3, P[2]=2 -> choose 2nd gap (2) -> result[2]=3, gaps=[1,3]
    # i=2, P[1]=1 -> choose 1st gap (1) -> result[1]=2, gaps=[3]
    # i=1, P[0]=1 -> choose 1st gap (3) -> result[3]=1, gaps=[]
    # Result: [4,2,3,1] -> matches!
    #
    # So the algorithm is:
    # 1. Create a list of gaps: [0, 1, 2, ..., N-1]
    # 2. For i from N down to 1:
    #      pos = P[i-1] - 1  (convert to 0-indexed)
    #      result[gaps[pos]] = i
    #      remove gaps[pos]
    # 3. Print result.
    #
    # But removing from a list is O(N), so total O(N^2). We need O(N) or O(N log N).
    # We can use a Fenwick tree or segment tree to find the k-th available position and delete it.
    # Or use a balanced BST, but in Python we can use a Fenwick tree.
    #
    # Fenwick tree approach:
    # - Initialize a Fenwick tree of size N with 1 at each position.
    # - To find the k-th available position: find the smallest index i such that sum(1..i) == k.
    # - Then update position i to 0 (remove it).
    #
    # Steps:
    # 1. Build Fenwick tree with all 1s.
    # 2. For i from N down to 1:
    #      k = P[i-1]
    #      Find the smallest index idx such that query(idx) == k.
    #      result[idx] = i
    #      Update idx to 0 (add -1 at idx).
    # 3. Print result.
    #
    # Fenwick tree operations are O(log N), so total O(N log N).
    
    # Implement Fenwick tree
    class Fenwick:
        def __init__(self, n):
            self.n = n
            self.tree = [0] * (n + 1)
        
        def update(self, i, delta):
            while i <= self.n:
                self.tree[i] += delta
                i += i & (-i)
        
        def query(self, i):
            s = 0
            while i > 0:
                s += self.tree[i]
                i -= i & (-i)
            return s
        
        def find_kth(self, k):
            # Find smallest i such that query(i) == k
            # We can do this by binary lifting on the Fenwick tree.
            idx = 0
            current_sum = 0
            bit_mask = 1 << (self.n.bit_length() - 1)
            while bit_mask > 0:
                t_idx = idx + bit_mask
                if t_idx <= self.n and current_sum + self.tree[t_idx] < k:
                    idx = t_idx
                    current_sum += self.tree[idx]
                bit_mask >>= 1
            return idx + 1
    
    n = N
    ft = Fenwick(n)
    for i in range(1, n + 1):
        ft.update(i, 1)
    
    result = [0] * n
    for i in range(n, 0, -1):
        k = P[i-1]
        idx = ft.find_kth(k)
        result[idx-1] = i
        ft.update(idx, -1)
    
    print(*(result))

if __name__ == "__main__":
    solve()
