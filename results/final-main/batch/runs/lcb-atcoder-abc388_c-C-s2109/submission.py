import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    A = [int(x) for x in input_data[1:]]
    
    # Since A is sorted, for each bottom A[j], we need to count tops A[i] (i < j)
    # such that 2 * A[i] <= A[j].
    # As j increases, A[j] increases, so the condition 2*A[i] <= A[j] becomes easier to satisfy.
    # We can maintain a pointer 'left' that indicates the first index i where 2*A[i] <= A[j].
    # However, since we need to count all i < j satisfying the condition, and the condition
    # is monotonic with respect to A[i], we can use a two-pointer approach.
    
    # Actually, a simpler approach:
    # For each j from 0 to N-1, we want to find how many i < j satisfy 2*A[i] <= A[j].
    # Since A is sorted, if 2*A[i] <= A[j], then for any k < i, 2*A[k] <= 2*A[i] <= A[j].
    # So the valid i's form a prefix [0, k] where k is the largest index such that 2*A[k] <= A[j].
    # But we also need i < j. Since A[i] <= A[j] (sorted), and 2*A[i] <= A[j] implies A[i] <= A[j],
    # the condition i < j is automatically satisfied for all valid i because if 2*A[i] <= A[j],
    # then A[i] <= A[j]/2 < A[j] (since A[j] >= 1), so i must be less than j.
    # Wait, not necessarily. If A[i] = A[j], then 2*A[i] <= A[j] implies A[i] <= A[j]/2,
    # which is only possible if A[i] = 0, but A[i] >= 1. So actually, if 2*A[i] <= A[j],
    # then A[i] <= A[j]/2 < A[j], so A[i] < A[j], which implies i < j (since sorted).
    # Therefore, we just need to count i such that 2*A[i] <= A[j].
    
    # We can use a two-pointer approach:
    # left = 0
    # For each j from 0 to N-1:
    #   while left < j and 2*A[left] <= A[j]:
    #       left += 1
    #   But this is not correct because we want to count all i < j with 2*A[i] <= A[j].
    #   Actually, we want the count of i such that 2*A[i] <= A[j].
    #   Since A is sorted, the valid i's are from 0 to some k.
    #   We can maintain a pointer 'left' that is the first index where 2*A[left] > A[j].
    #   Then the count is 'left'.
    #   But as j increases, A[j] increases, so the threshold for 2*A[i] <= A[j] increases,
    #   meaning 'left' can only increase.
    
    # Let's reframe:
    # We want to count pairs (i, j) with i < j and 2*A[i] <= A[j].
    # For a fixed j, we want to find the largest k such that for all i in [0, k], 2*A[i] <= A[j].
    # Then the count for this j is k+1.
    # Since A[j] is non-decreasing with j, the maximum k for j is non-decreasing.
    # So we can maintain a pointer 'left' that is the first index where 2*A[left] > A[j].
    # Then the number of valid i's for this j is 'left'.
    # But we must ensure that we only count i < j. However, as argued, if 2*A[i] <= A[j],
    # then A[i] <= A[j]/2 < A[j], so i < j is automatically satisfied.
    
    # Algorithm:
    # left = 0
    # total = 0
    # for j in range(N):
    #     while left < N and 2*A[left] <= A[j]:
    #         left += 1
    #     # Now left is the first index where 2*A[left] > A[j] or left == N.
    #     # So the valid indices are 0 to left-1, which is 'left' indices.
    #     # But we must also ensure that we don't count i >= j.
    #     # However, as argued, if 2*A[i] <= A[j], then i < j.
    #     # So we can just add 'left' to total.
    #     # But wait, the above while loop condition is wrong.
    #     # We want to find the largest k such that 2*A[k] <= A[j].
    #     # Then the count is k+1.
    #     # But the above loop increments left until 2*A[left] > A[j].
    #     # So left is the first index where 2*A[left] > A[j].
    #     # So the valid indices are 0 to left-1, which is 'left' indices.
    #     # But we must ensure that left does not exceed j.
    #     # Actually, since 2*A[i] <= A[j] implies i < j, we don't need to check i < j.
    #     # However, the above loop might make left > j, which is fine because we only care about the count.
    #     # But wait, if left > j, then we are counting indices i >= j, which is not allowed.
    #     # So we need to cap left at j+1.
    #     # Actually, let's think again.
    #     # We want to count i < j such that 2*A[i] <= A[j].
    #     # Since A is sorted, the condition 2*A[i] <= A[j] is monotonic in i.
    #     # So the valid i's form a prefix [0, k].
    #     # We want to find k such that 2*A[k] <= A[j] and (k+1 > j or 2*A[k+1] > A[j]).
    #     # But actually, we can just find the largest k such that 2*A[k] <= A[j], and then take min(k+1, j).
    #     # However, since 2*A[i] <= A[j] implies i < j, we have k < j, so k+1 <= j.
    #     # So we don't need to cap.
    #     # But the above loop increments left until 2*A[left] > A[j].
    #     # So left is the first index where 2*A[left] > A[j].
    #     # So the valid indices are 0 to left-1, which is 'left' indices.
    #     # And since 2*A[i] <= A[j] implies i < j, we have left <= j.
    #     # So we can just add left to total.
    
    # But there's a problem: the above loop condition is "while left < N and 2*A[left] <= A[j]: left += 1".
    # This will make left the first index where 2*A[left] > A[j] or left == N.
    # So the count is left.
    # But we must ensure that left does not exceed j.
    # Actually, since 2*A[i] <= A[j] implies i < j, we have left <= j.
    # So we can just add left to total.
    
    # However, the above logic is flawed because the while loop condition is not correct.
    # We want to find the largest k such that 2*A[k] <= A[j].
    # Then the count is k+1.
    # But the above loop increments left until 2*A[left] > A[j].
    # So left is the first index where 2*A[left] > A[j].
    # So the valid indices are 0 to left-1, which is 'left' indices.
    # And since 2*A[i] <= A[j] implies i < j, we have left <= j.
    # So we can just add left to total.
    
    # But wait, the above loop might make left > j if we don't cap it.
    # Actually, since 2*A[i] <= A[j] implies i < j, we have left <= j.
    # So we don't need to cap.
    
    # Let's test with an example:
    # A = [2, 3, 4, 4, 7, 10]
    # j=0, A[j]=2: left=0 (since 2*A[0]=4 > 2), count=0
    # j=1, A[j]=3: left=0 (since 2*A[0]=4 > 3), count=0
    # j=2, A[j]=4: left=0 (since 2*A[0]=4 <= 4, left=1; 2*A[1]=6 > 4), count=1
    # j=3, A[j]=4: left=1 (since 2*A[1]=6 > 4), count=1
    # j=4, A[j]=7: left=1 (since 2*A[1]=6 <= 7, left=2; 2*A[2]=8 > 7), count=2
    # j=5, A[j]=10: left=2 (since 2*A[2]=8 <= 10, left=3; 2*A[3]=8 <= 10, left=4; 2*A[4]=14 > 10), count=4
    # Total = 0+0+1+1+2+4 = 8. Correct.
    
    # So the algorithm is:
    # left = 0
    # total = 0
    # for j in range(N):
    #     while left < N and 2*A[left] <= A[j]:
    #         left += 1
    #     total += left
    # print(total)
    
    left = 0
    total = 0
    for j in range(N):
        while left < N and 2 * A[left] <= A[j]:
            left += 1
        total += left
        # We don't need to reset left because as j increases, A[j] increases,
        # so the condition 2*A[i] <= A[j] becomes easier to satisfy, and left can only increase.
    
    print(total)

solve()
