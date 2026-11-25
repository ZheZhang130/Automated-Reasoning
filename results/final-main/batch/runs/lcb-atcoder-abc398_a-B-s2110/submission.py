n = int(input())
side = "-" * ((n - 1) // 2)
print(side + "=" * (2 - n % 2) + side)
