import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    try:
        n = int(next(iterator))
        a = []
        for _ in range(n):
            a.append(int(next(iterator)))
    except StopIteration:
        return

    # F[i] = max sum after processing first i elements
    # F[0] = 0 (empty stack)
    # F[1] = a[0] (must append first element)
    # F[i] = max(F[i-1] + a[i-1], F[i-2]) for i >= 2
    
    if n == 0:
        print(0)
        return
    
    f_prev2 = 0  # F[0]
    f_prev1 = a[0]  # F[1]
    
    if n == 1:
        print(f_prev1)
        return
    
    for i in range(2, n + 1):
        current = max(f_prev1 + a[i-1], f_prev2)
        f_prev2 = f_prev1
        f_prev1 = current
    
    print(f_prev1)

if __name__ == "__main__":
    solve()
