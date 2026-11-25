n = int(input())
side = "-" * ((n - 1) // 2)
print(side + "=" * (n - 2 * len(side)) + side)
