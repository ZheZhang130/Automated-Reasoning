import sys

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        X = int(line)
    except ValueError:
        return

    # Generate the 9x9 multiplication table
    total_sum = 0
    count_X = 0

    for i in range(1, 10):
        for j in range(1, 10):
            val = i * j
            total_sum += val
            if val == X:
                count_X += 1

    # Subtract X for each occurrence
    result = total_sum - count_X * X
    print(result)

if __name__ == "__main__":
    solve()
