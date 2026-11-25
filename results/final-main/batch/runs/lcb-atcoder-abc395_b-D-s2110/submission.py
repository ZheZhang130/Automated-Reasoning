import sys

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        n = int(line)
    except ValueError:
        return

    # Initialize grid with white ('.')
    grid = [['.' for _ in range(n)] for _ in range(n)]

    # Apply operations for i from 1 to n
    for i in range(1, n + 1):
        j = n + 1 - i
        if i <= j:
            # Fill rectangle from (i-1, i-1) to (j-1, j-1)
            # (using 0-based indexing)
            top = i - 1
            left = i - 1
            bottom = j - 1
            right = j - 1
            color = '#' if i % 2 == 1 else '.'
            for row in range(top, bottom + 1):
                for col in range(left, right + 1):
                    grid[row][col] = color

    # Print the grid
    for row in grid:
        print(''.join(row))

if __name__ == "__main__":
    solve()
