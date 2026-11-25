import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    A = [int(x) for x in input_data[1:]]
    
    # Since A is sorted in ascending order, we can use a two-pointer approach.
    # For each bottom mochi A[j], we want to count how many tops A[i] satisfy 2*A[i] <= A[j].
    # Since A is sorted, as j increases, A[j] increases, so the condition 2*A[i] <= A[j]
    # will be satisfied by more (or the same) i's.
    # We maintain a pointer 'left' which is the index of the first valid top for the current bottom.
    # However, since we want to count ALL valid tops for each bottom, and the valid tops form a prefix,
    # we can just find the largest 'left' such that 2*A[left] <= A[j].
    # Actually, since A is sorted, for a fixed j, the valid i's are 0 <= i <= k where k is the largest index
    # such that 2*A[k] <= A[j]. But wait, the problem says "choose two mochi out of the N mochi".
    # It doesn't say distinct indices, but typically "choose two" implies distinct items.
    # Also, a mochi cannot be placed on itself (a <= a/2 => a <= 0, impossible since sizes >= 1).
    # So we need distinct indices i and j with i < j (since A is sorted and positive, A[i] < A[j] for i < j).
    # The condition is 2*A[i] <= A[j].
    
    # We iterate j from 0 to N-1. For each j, we want to find the count of i < j such that 2*A[i] <= A[j].
    # Since A is sorted, the condition 2*A[i] <= A[j] is monotonic with respect to i.
    # We can maintain a pointer 'left' which is the smallest index such that 2*A[left] <= A[j].
    # Actually, we want the count of such i's. Since A is sorted, if 2*A[i] <= A[j], then for any k < i,
    # 2*A[k] <= 2*A[i] <= A[j], so all indices from 0 to some max_index are valid.
    # We can find the largest index 'max_i' such that 2*A[max_i] <= A[j]. Then the count is max_i + 1.
    # But we must also ensure i < j. However, since A[i] <= A[j] and A is sorted, if i == j, then 2*A[j] <= A[j] => A[j] <= 0, impossible.
    # So any valid i must be strictly less than j. Thus, we just need to find the largest index 'k' such that 2*A[k] <= A[j].
    # Then the number of valid tops for bottom j is k + 1.
    # We can use a two-pointer approach: as j increases, A[j] increases, so the threshold for A[i] increases.
    # Thus, the largest valid k (let's call it 'right') will also non-decrease.
    
    total_kagamimochi = 0
    right = 0  # This will point to the largest index such that 2*A[right] <= A[j]
    
    for j in range(N):
        # We want to find the largest 'right' such that 2*A[right] <= A[j].
        # Since A[j] is increasing, 'right' can only move to the right.
        # We start from the current 'right' and move it forward as long as the condition holds.
        # Note: 'right' should not exceed j-1 because if right == j, then 2*A[j] <= A[j] is false.
        # But our loop condition will naturally handle this because 2*A[j] > A[j] for positive A[j].
        
        while right < N and 2 * A[right] <= A[j]:
            right += 1
        
        # Now, 'right' is the first index such that 2*A[right] > A[j] or right == N.
        # So the valid indices are 0, 1, ..., right-1.
        # The count is right.
        # However, we must ensure that we are only counting tops that are strictly before the bottom.
        # But as established, if 2*A[i] <= A[j], then A[i] <= A[j]/2 < A[j] (since A[j] >= 1), so i < j is guaranteed.
        # So we can just add 'right' to the total.
        
        total_kagamimochi += right
        
        # Optimization: if right reaches j, we can cap it at j-1? 
        # Actually, the condition 2*A[right] <= A[j] implies A[right] <= A[j]/2.
        # Since A[j] >= 1, A[j]/2 < A[j], so A[right] < A[j], which implies right < j (since A is sorted and distinct? No, A can have duplicates).
        # If A has duplicates, say A = [2, 2, 2], j=1, A[j]=2. 2*A[0]=4 > 2, so right=0. Count=0.
        # j=2, A[j]=2. 2*A[0]=4 > 2, right=0. Count=0.
        # So duplicates don't break the logic.
        # But we must ensure right doesn't go beyond j. 
        # Actually, the condition 2*A[right] <= A[j] ensures A[right] <= A[j]/2.
        # Since A[j] >= 1, A[j]/2 < A[j], so A[right] < A[j].
        # If A is sorted, then right < j is guaranteed if A[right] < A[j].
        # What if A[right] == A[j]? Then 2*A[right] <= A[j] => 2*A[j] <= A[j] => A[j] <= 0, impossible.
        # So right will always be less than j.
        # Thus, we don't need to explicitly cap right at j.
        
        # However, there is a subtle point: the pointer 'right' is maintained across iterations.
        # For the next j, A[j] is larger, so the condition 2*A[k] <= A[j] might hold for larger k.
        # So we continue from the current 'right'.
        
        # But wait, what if for the current j, the condition 2*A[right] <= A[j] holds for right = current_right,
        # but for the next j, we might need to check right = current_right + 1, etc.
        # Yes, that's what the while loop does.
        
        # One more thing: the pointer 'right' should not be reset. It only moves forward.
        # This is correct because A[j] is non-decreasing.
        
        # However, there is a potential issue: if for some j, no i satisfies the condition, then right remains at its previous value.
        # But if for j-1, right was k, meaning 2*A[k] > A[j-1], then for j, we have A[j] >= A[j-1], so 2*A[k] might be <= A[j].
        # So we need to advance right from k.
        # But what if for j-1, right was 0 (no valid tops), and for j, there are valid tops?
        # Then we start checking from right=0.
        # But our loop starts from the current 'right'. If 'right' is 0, we check 0, then 1, etc.
        # This is correct.
        
        # But wait, if for j-1, right was k, it means 2*A[k] > A[j-1].
        # For j, we have A[j] >= A[j-1]. It's possible that 2*A[k] <= A[j] now.
        # So we need to check from k onwards.
        # But our while loop does exactly that: it starts from the current 'right' and increments.
        # However, we must ensure that we don't skip any indices.
        # Since 'right' is the first index that fails the condition for the previous j,
        # for the current j, we start checking from 'right' because indices < 'right' definitely satisfy the condition (since they satisfied it for a smaller A[j]).
        # Wait, no. For a smaller A[j_prev], we had 2*A[k] > A[j_prev].
        # For a larger A[j], we might have 2*A[k] <= A[j].
        # So we need to check from the current 'right' onwards.
        # But what about indices less than 'right'? They satisfied 2*A[i] <= A[j_prev] <= A[j], so they definitely satisfy 2*A[i] <= A[j].
        # So the valid range for j is [0, right-1] where 'right' is the first index that fails.
        # So we just need to advance 'right' as long as 2*A[right] <= A[j].
        # This is correct.
        
        # But there is a catch: the pointer 'right' is global.
        # For j=0, we start with right=0. Check 2*A[0] <= A[0] -> false (since A[0]>=1). So right remains 0. Count=0.
        # For j=1, we start with right=0. Check 2*A[0] <= A[1]. If true, right becomes 1. Then check 2*A[1] <= A[1] -> false. So right=1. Count=1.
        # This seems correct.
        
        # However, consider the case where A = [2, 3, 4].
        # j=0, A[0]=2. right=0. 2*2=4 > 2. right=0. Count=0.
        # j=1, A[1]=3. right=0. 2*2=4 > 3. right=0. Count=0.
        # j=2, A[2]=4. right=0. 2*2=4 <= 4. right=1. 2*3=6 > 4. right=1. Count=1.
        # Total=1.
        # But wait, for j=2 (bottom=4), top=2 is valid. So count should be 1. Correct.
        
        # Another example: A = [2, 2, 4].
        # j=0, A[0]=2. right=0. Count=0.
        # j=1, A[1]=2. right=0. 2*2=4 > 2. right=0. Count=0.
        # j=2, A[2]=4. right=0. 2*2=4 <= 4. right=1. 2*2=4 <= 4. right=2. 2*4=8 > 4. right=2. Count=2.
        # Total=2.
        # Valid pairs: (index0, index2) and (index1, index2). Both have top=2, bottom=4.
        # The problem says: "Two kagamimochi are distinguished if at least one of the mochi is different, even if the sizes of the mochi are the same."
        # So (mochi at index0, mochi at index2) is different from (mochi at index1, mochi at index2) because the mochi are different (different indices).
        # So we count 2. Correct.
        
        # So the logic is sound.
        
        pass # Just a placeholder to avoid unused variable warning if any
    
    print(total_kagamimochi)

if __name__ == '__main__':
    solve()
