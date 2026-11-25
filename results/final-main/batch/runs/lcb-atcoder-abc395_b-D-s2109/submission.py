import sys

def solve():
    try:
        data = sys.stdin.read().strip()
        if not data:
            return
        N = int(data)
    except ValueError:
        return

    # Initialize grid with white ('.')
    grid = [['.' for _ in range(N)] for _ in range(N)]

    # Apply operations for i from 1 to N
    for i in range(1, N + 1):
        j = N + 1 - i
        if i <= j:
            # Fill rectangle from (i-1, i-1) to (j-1, j-1)
            # (using 0-based indexing)
            r_start = i - 1
            r_end = j - 1
            c_start = i - 1
            c_end = j - 1
            color = '#' if i % 2 == 1 else '.'
            for r in range(r_start, r_end + 1):
                for c in range(c_start, c_end + 1):
                    grid[r][c] = color

    # Print the grid
    for row in grid:
        print(''.join(row))

if __name__ == "__main__":
    solve()
