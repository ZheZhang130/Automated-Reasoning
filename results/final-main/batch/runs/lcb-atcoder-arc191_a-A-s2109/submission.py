import sys

def solve():
    data = sys.stdin.read().split()
    N = int(data[0])
    M = int(data[1])
    S = data[2]
    T = data[3]
    
    # Sort T in descending order
    T_sorted = sorted(T, reverse=True)
    
    # Convert S to list for mutability
    S_list = list(S)
    
    # For each position i from 0 to min(N, M)-1:
    # If T_sorted[i] > S[i], replace S[i] with T_sorted[i]
    # This greedy approach works because we want to put larger digits
    # in more significant positions, and we process left to right.
    for i in range(min(N, M)):
        if T_sorted[i] > S_list[i]:
            S_list[i] = T_sorted[i]
    
    print(''.join(S_list))

if __name__ == "__main__":
    solve()
