import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    A = [int(x) for x in input_data[1:]]
    
    # A is already sorted in ascending order as per constraints.
    # We need to count pairs (i, j) such that i < j and A[i] <= A[j] / 2.
    # Since A is sorted, for a fixed j, we want to count i < j such that 2*A[i] <= A[j].
    # As j increases, A[j] increases (non-decreasing), so the condition 2*A[i] <= A[j]
    # becomes easier to satisfy. Thus, the number of valid i's for a given j is non-decreasing.
    # We can use a two-pointer approach.
    
    # left pointer: index of the first element that satisfies 2*A[left] <= A[j]
    # Actually, we want to count all i < j such that 2*A[i] <= A[j].
    # Since A is sorted, if 2*A[i] <= A[j], then for any k < i, 2*A[k] <= 2*A[i] <= A[j].
    # So the valid i's form a prefix [0, right-1] where right is the largest index such that 2*A[right-1] <= A[j].
    # But we also need i < j. Since A is sorted and non-decreasing, if 2*A[i] <= A[j], 
    # and i < j, then i is definitely a valid top for bottom j.
    # However, we must ensure we don't count i >= j. But since A[i] <= A[j]/2 and A[i] >= 1,
    # we have A[i] < A[j], so i must be less than j (since array is sorted non-decreasingly,
    # equal values are adjacent, but if A[i] == A[j], then 2*A[i] <= A[j] implies A[i] <= 0 which is impossible).
    # Actually, if A[i] == A[j], then 2*A[i] <= A[j] => 2*A[i] <= A[i] => A[i] <= 0, impossible.
    # So if the condition holds, A[i] < A[j], which implies i < j because the array is sorted.
    # Therefore, we just need to count i such that 2*A[i] <= A[j].
    
    # Let's use two pointers:
    # left: the smallest index such that 2*A[left] <= A[j]
    # But actually, we want the count of all i such that 2*A[i] <= A[j].
    # Since A is sorted, these i's are from 0 to some index k.
    # We can maintain a pointer 'right' that is the largest index such that 2*A[right] <= A[j].
    # Then the count for bottom j is (right + 1).
    # As j increases, A[j] increases, so 'right' can only move forward.
    
    right = 0
    total = 0
    
    for j in range(N):
        # We want to find the largest 'right' such that 2*A[right] <= A[j]
        # and right < j (but as argued, if condition holds, right < j automatically)
        # However, we must ensure right doesn't exceed j.
        # Actually, since A is sorted, if 2*A[right] <= A[j], then A[right] <= A[j]/2 < A[j] (since A[j] >= 1),
        # so right < j is guaranteed.
        
        # Advance right while condition holds
        while right < N and 2 * A[right] <= A[j]:
            right += 1
        
        # Now, right is the first index such that 2*A[right] > A[j] or right == N.
        # So indices 0 to right-1 satisfy the condition.
        # The count is right.
        # But we must also ensure that we only count i < j.
        # However, as argued, if 2*A[i] <= A[j], then A[i] < A[j], so i < j.
        # So we can just add 'right' to total.
        
        # Wait, there's a catch: what if right >= j?
        # Let's re-examine: if 2*A[i] <= A[j], then A[i] <= A[j]/2.
        # Since A[j] >= 1, A[j]/2 < A[j], so A[i] < A[j].
        # Since the array is sorted non-decreasingly, A[i] < A[j] implies i < j.
        # So we don't need to worry about i >= j.
        
        # However, the pointer 'right' might have advanced beyond j in previous iterations?
        # No, because for a fixed j, we start from the current 'right' and advance.
        # But 'right' is global. For j=0, right will be 0 (since 2*A[0] <= A[0] is false for A[0]>=1).
        # Then for j=1, we continue from current right.
        # But we must ensure that we don't count i >= j.
        # Actually, the condition 2*A[i] <= A[j] with i < j is what we want.
        # But if we just count all i with 2*A[i] <= A[j], and since i < j is implied, it's fine.
        # However, the pointer 'right' is maintained across j. 
        # For j=0, right=0. For j=1, we check from right=0.
        # But what if for j=0, right=0, and for j=1, we find that 2*A[0] <= A[1], so right becomes 1.
        # Then for j=2, we continue from right=1.
        # This is correct because as j increases, A[j] increases, so the set of valid i's grows.
        # But we must ensure that we don't count i >= j.
        # However, as argued, if 2*A[i] <= A[j], then i < j.
        # So the count is simply 'right'.
        
        # But wait: the pointer 'right' is the count of elements from 0 to right-1 that satisfy the condition.
        # However, we must ensure that we only consider i < j.
        # But since i < j is implied by the condition, we are safe.
        # However, there's a problem: the pointer 'right' might be greater than j?
        # Let's test: suppose A = [1, 1, 1]. 
        # j=0: A[0]=1. 2*A[0]=2 > 1, so right=0. total=0.
        # j=1: A[1]=1. 2*A[0]=2 > 1, so right=0. total=0.
        # j=2: A[2]=1. 2*A[0]=2 > 1, so right=0. total=0.
        # Correct.
        # Another example: A = [1, 2, 4].
        # j=0: A[0]=1. 2*1=2 > 1, right=0. total=0.
        # j=1: A[1]=2. 2*1=2 <= 2, so right becomes 1. 2*2=4 > 2, stop. right=1. total=1.
        # j=2: A[2]=4. 2*1=2 <= 4, right=1. 2*2=4 <= 4, right=2. 2*4=8 > 4, stop. right=2. total=1+2=3.
        # Pairs: (0,1): 1<=2/2 -> 1<=1 yes. (0,2): 1<=4/2 -> 1<=2 yes. (1,2): 2<=4/2 -> 2<=2 yes.
        # Total 3. Correct.
        
        # But what if A = [2, 3, 4, 4, 7, 10] (Sample 1)
        # j=0: A[0]=2. 2*2=4>2, right=0. total=0.
        # j=1: A[1]=3. 2*2=4>3, right=0. total=0.
        # j=2: A[2]=4. 2*2=4<=4, right=1. 2*3=6>4, stop. right=1. total=1.
        # j=3: A[3]=4. 2*2=4<=4, right=1. 2*3=6>4, stop. right=1. total=1+1=2.
        # j=4: A[4]=7. 2*2=4<=7, right=1. 2*3=6<=7, right=2. 2*4=8>7, stop. right=2. total=2+2=4.
        # j=5: A[5]=10. 2*2=4<=10, right=1. 2*3=6<=10, right=2. 2*4=8<=10, right=3. 2*4=8<=10, right=4. 2*7=14>10, stop. right=4. total=4+4=8.
        # Total 8. Correct.
        
        # However, there's a subtle issue: the pointer 'right' is not reset for each j.
        # But since A[j] is non-decreasing, the set of valid i's for j+1 is a superset of that for j.
        # So we can continue from the current 'right'.
        # But we must ensure that we don't count i >= j.
        # However, as argued, if 2*A[i] <= A[j], then i < j.
        # So the count is simply 'right'.
        
        # But wait: what if the array has duplicate values?
        # Example: A = [2, 2, 4].
        # j=0: A[0]=2. 2*2=4>2, right=0. total=0.
        # j=1: A[1]=2. 2*2=4>2, right=0. total=0.
        # j=2: A[2]=4. 2*2=4<=4, right=1. 2*2=4<=4, right=2. 2*4=8>4, stop. right=2. total=2.
        # Pairs: (0,2): 2<=4/2 -> 2<=2 yes. (1,2): 2<=4/2 -> 2<=2 yes.
        # Total 2. Correct.
        
        # So the algorithm is:
        # right = 0
        # total = 0
        # for j in range(N):
        #     while right < N and 2 * A[right] <= A[j]:
        #         right += 1
        #     total += right
        # print(total)
        
        # But wait: the condition is 2*A[i] <= A[j]. 
        # In the loop, we are checking 2*A[right] <= A[j].
        # And we advance right as long as this holds.
        # Then right is the count of indices i (from 0 to right-1) that satisfy the condition.
        # And since i < j is implied, we are good.
        
        # However, there's a problem: the pointer 'right' is not bounded by j.
        # But as argued, if 2*A[i] <= A[j], then i < j.
        # So right will never exceed j? 
        # Let's check: if right > j, then there exists i in [j, right) such that 2*A[i] <= A[j].
        # But since i >= j and the array is sorted, A[i] >= A[j].
        # So 2*A[i] >= 2*A[j] > A[j] (since A[j] >= 1).
        # So 2*A[i] <= A[j] is impossible for i >= j.
        # Therefore, right will never exceed j.
        # So we don't need to bound right by j.
        
        # Thus, the algorithm is correct.
        
        total += right
        
    print(total)

if __name__ == '__main__':
    solve()
