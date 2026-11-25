import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0])
    a = list(map(int, data[1:]))
    
    # The problem is about finding the maximum score by repeatedly deleting adjacent pairs.
    # Key insight: This is equivalent to finding a matching where each pair (i, j) 
    # has an odd number of elements between them in the original sequence.
    # 
    # Actually, let's think about it differently.
    # When we delete a pair, the remaining elements shift.
    # The optimal strategy is to always delete the pair with the largest adjacent difference.
    # But the priority queue approach above has a bug: when we delete a pair, we need to
    # check if the new adjacent pair (i-1, i+2) should be added, but we also need to
    # consider that we might have missed some pairs.
    #
    # Let's try a different approach: dynamic programming or a different greedy.
    # 
    # Actually, there's a known solution using a stack:
    # Process elements left to right. Maintain a stack.
    # For each new element, if it forms a better pair with the stack top than the pair below,
    # delete the lower pair. But this needs refinement.
    #
    # Let's try: always delete the pair with the maximum adjacent difference among all current adjacent pairs.
    # We need to efficiently track and update adjacent pairs.
    #
    # New approach: Use a segment tree or just simulate with a list (since N is up to 300,000,
    # but we only do N/2 deletions, and each deletion is O(1) with a doubly linked list).
    #
    # Let's use a doubly linked list simulation:
    # - Maintain prev and next pointers for each element
    # - Use a max heap to track adjacent differences
    # - When we delete a pair, update the linked list and add the new adjacent pair to the heap
    
    import heapq
    
    # Build doubly linked list
    prev = [i-1 for i in range(n)]
    nxt = [i+1 for i in range(n)]
    nxt[n-1] = -1  # No next for last element
    
    # Max heap of adjacent differences: (-diff, i) where i is the index of the first element
    heap = []
    for i in range(n - 1):
        diff = abs(a[i] - a[i+1])
        heapq.heappush(heap, (-diff, i))
    
    total_score = 0
    deletions = 0
    
    while heap and deletions < n // 2:
        neg_diff, i = heapq.heappop(heap)
        diff = -neg_diff
        
        # Check if this pair is still valid
        if nxt[i] == -1 or nxt[i] != i + 1:
            continue
        
        # Delete this pair
        total_score += diff
        deletions += 1
        
        # Update linked list: connect prev[i] with nxt[i+1]
        left = prev[i]
        right = nxt[i+1]
        
        if left != -1:
            nxt[left] = right
        if right != -1:
            prev[right] = left
        
        # Add the new adjacent pair if both elements exist
        if left != -1 and right != -1:
            new_diff = abs(a[left] - a[right])
            heapq.heappush(heap, (-new_diff, left))
    
    print(total_score)

if __name__ == "__main__":
    solve()
