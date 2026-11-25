def solve():
    s = input().strip()
    result = ''.join(c for c in s if c == '2')
    print(result)

if __name__ == "__main__":
    solve()
