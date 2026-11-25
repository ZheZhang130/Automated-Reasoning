import sys

def solve():
    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            return
        N = int(input_data)
    except ValueError:
        return

    # For each cell (i, j) with 1-based indexing (1 <= i, j <= N):
    # The last operation that colors this cell is k = min(i, j, N+1-i, N+1-j)
    # If k is odd -> '#', if k is even -> '.'
    
    for i in range(1, N + 1):
        row_chars = []
        for j in range(1, N + 1):
            k = min(i, j, N + 1 - i, N + 1 - j)
            if k % 2 == 1:
                row_chars.append('#')
            else:
                row_chars.append('.')
        print(''.join(row_chars))

if __name__ == "__main__":
    solve()
