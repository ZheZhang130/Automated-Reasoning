n = int(input())
padding = '-' * ((n - 1) // 2)
center = '=' if n % 2 else '=='
print(padding + center + padding)
