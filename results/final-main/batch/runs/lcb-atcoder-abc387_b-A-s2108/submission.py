def solve():
    try:
        x_str = input().strip()
        if not x_str:
            return
        x = int(x_str)
    except ValueError:
        return

    total_sum = 0
    for i in range(1, 10):
        for j in range(1, 10):
            val = i * j
            if val != x:
                total_sum += val

    print(total_sum)

if __name__ == "__main__":
    solve()
