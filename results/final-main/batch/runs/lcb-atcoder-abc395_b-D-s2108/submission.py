import sys

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        N = int(line)
    except ValueError:
        return

    # Initialize grid with '.'
    grid = [['.' for _ in range(N)] for _ in range(N)]

    # Apply operations for i from 1 to N
    for i in range(1, N + 1):
        j = N + 1 - i
        if i <= j:
            # Fill rectangular region from (i-1, i-1) to (j-1, j-1)
            # (using 0-based indexing)
            color = '#' if i % 2 == 1 else '.'
            for r in range(i - 1, j):
                for c in range(i - 1, j):
                    grid[r][c] = color

    # Print the grid
    for row in grid:
        print(''.join(row))

if __name__ == "__main__":
    solve()
