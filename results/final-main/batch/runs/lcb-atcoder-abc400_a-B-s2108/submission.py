a = int(input())
b, remainder = divmod(400, a)
print(-1 if remainder else b)
