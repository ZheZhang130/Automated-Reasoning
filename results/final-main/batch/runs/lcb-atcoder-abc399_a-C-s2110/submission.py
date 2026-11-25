import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    n = int(input_data[0])
    s = input_data[1]
    t = input_data[2]
    
    hamming_distance = 0
    for i in range(n):
        if s[i] != t[i]:
            hamming_distance += 1
    
    print(hamming_distance)

if __name__ == "__main__":
    solve()
