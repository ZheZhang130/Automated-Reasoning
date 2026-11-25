import sys

def solve():
    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            return
        X = int(input_data)
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
