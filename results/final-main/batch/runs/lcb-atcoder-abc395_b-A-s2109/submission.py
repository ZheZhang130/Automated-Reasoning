import sys

def solve():
    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            return
        N = int(input_data)
    except ValueError:
        return

    # Initialize grid with '.' (white)
    grid = [['.' for _ in range(N)] for _ in range(N)]

    # Process rows i from 1 to N (1-indexed)
    for i in range(1, N + 1):
        j = N + 1 - i
        if i <= j:
            # Fill the square from (i,i) to (j,j)
            # Note: i and j are 1-indexed, so we use i-1 and j-1 for 0-indexed access
            top = i - 1
            bottom = j - 1
            left = i - 1
            right = j - 1
            
            color = '#' if i % 2 == 1 else '.'
            for r in range(top, bottom + 1):
                for c in range(left, right + 1):
                    grid[r][c] = color

    # Print the grid
    for row in grid:
        print(''.join(row))

if __name__ == "__main__":
    solve()
