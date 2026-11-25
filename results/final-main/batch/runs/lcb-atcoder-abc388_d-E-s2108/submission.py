import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    A = [int(x) for x in input_data[1:N+1]]
    
    current_stones = A[:]
    
    for i in range(N):
        count_adults_with_stones = 0
        for j in range(i):
            if current_stones[j] >= 1:
                count_adults_with_stones += 1
                current_stones[j] -= 1
        current_stones[i] += count_adults_with_stones
    
    print(*(current_stones))

if __name__ == "__main__":
    solve()
