a = list(map(int, input().split()))
inversions = sum(a[i] > a[j] for i in range(5) for j in range(i + 1, 5))
print("Yes" if inversions == 1 else "No")
