import sys

def solve():
    d = sys.stdin.read().strip()
    result = []
    for char in d:
        if char == 'N':
            result.append('S')
        elif char == 'S':
            result.append('N')
        elif char == 'E':
            result.append('W')
        elif char == 'W':
            result.append('E')
        else:
            result.append(char)
    print(''.join(result))

if __name__ == "__main__":
    solve()
