import sys

def solve():
    input_data = sys.stdin.read().strip()
    if not input_data:
        return
    N = int(input_data)
    
    for r in range(1, N + 1):
        row_chars = []
        for c in range(1, N + 1):
            # Determine the last operation index that colors this cell
            # A square from operation k covers cells where k <= row <= N+1-k and k <= col <= N+1-k
            # So the last operation is min(r, c, N+1-r, N+1-c)
            k = min(r, c, N + 1 - r, N + 1 - c)
            if k % 2 == 1:
                row_chars.append('#')
            else:
                row_chars.append('.')
        print(''.join(row_chars))

if __name__ == '__main__':
    solve()
