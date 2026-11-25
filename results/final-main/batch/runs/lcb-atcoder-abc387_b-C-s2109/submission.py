import sys

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        X = int(line)
    except ValueError:
        return

    total_sum = 0
    for i in range(1, 10):
        for j in range(1, 10):
            product = i * j
            if product != X:
                total_sum += product
    print(total_sum)

if __name__ == "__main__":
    solve()
