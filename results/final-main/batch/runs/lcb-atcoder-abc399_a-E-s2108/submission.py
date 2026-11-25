def solve():
    n = int(input())
    s = input().strip()
    t = input().strip()
    
    hamming_distance = 0
    for i in range(n):
        if s[i] != t[i]:
            hamming_distance += 1
    
    print(hamming_distance)

if __name__ == "__main__":
    solve()
