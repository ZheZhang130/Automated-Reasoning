a = int(input())
b, remainder = divmod(400, a)
print(b if remainder == 0 else -1)
