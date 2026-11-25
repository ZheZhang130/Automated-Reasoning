import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    A = [int(x) for x in input_data[1:N+1]]
    
    # The operation allows us to merge any two bags.
    # This means we can form any partition of the multiset A into groups.
    # For each partition, the final XOR is the XOR of the sums of the groups.
    # We need to count the number of distinct XOR values achievable.
    
    # Since N is small (<=12), we can use recursion to try all partitions.
    # We'll use a recursive approach where we assign each element to a group.
    # To handle unlabeled groups, we'll use a canonical representation.
    
    # Actually, a simpler approach: use BFS on the state space.
    # State: sorted tuple of bag contents.
    # This correctly models the problem.
    
    start_state = tuple(sorted(A))
    visited = set()
    visited.add(start_state)
    queue = deque([start_state])
    
    while queue:
        state = queue.popleft()
        n = len(state)
        for i in range(n):
            for j in range(i+1, n):
                new_state_list = list(state)
                new_state_list[i] = 0
                new_state_list[j] += new_state_list[i]
                new_state = tuple(sorted(new_state_list))
                if new_state not in visited:
                    visited.add(new_state)
                    queue.append(new_state)
    
    xor_values = set()
    for state in visited:
        xor_val = 0
        for x in state:
            xor_val ^= x
        xor_values.add(xor_val)
    
    print(len(xor_values))

if __name__ == "__main__":
    solve()
