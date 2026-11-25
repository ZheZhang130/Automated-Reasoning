import sys

def solve():
    x = int(sys.stdin.read().strip())
    total_sum = 0
    for i in range(1, 10):
        for j in range(1, 10):
            val = i * j
            if val != x:
                total_sum += val
    print(total_sum)

if __name__ == "__main__":
    solve()
