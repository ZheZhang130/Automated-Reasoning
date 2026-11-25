import sys

def solve():
    s = sys.stdin.read().strip()
    # S is in format "dx" where d and x are digits 1-9
    # We need to parse the first and third characters as integers and multiply them
    first_digit = int(s[0])
    third_digit = int(s[2])
    result = first_digit * third_digit
    print(result)

if __name__ == "__main__":
    solve()
