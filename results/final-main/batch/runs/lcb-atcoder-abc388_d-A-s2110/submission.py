import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    A = [int(x) for x in data[1:N+1]]
    
    current_stones = list(A)
    
    for i in range(N):
        # Count how many adults (0 to i-1) have >= 1 stone
        count = 0
        for j in range(i):
            if current_stones[j] >= 1:
                count += 1
        
        # Alien i receives count stones
        current_stones[i] += count
        
        # All adults (0 to i-1) who have >= 1 stone give 1 stone and lose 1
        for j in range(i):
            if current_stones[j] >= 1:
                current_stones[j] -= 1
    
    print(*(current_stones))

solve()
