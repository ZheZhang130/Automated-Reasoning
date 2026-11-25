import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    
    H = int(next(iterator))
    W = int(next(iterator))
    
    grid = []
    for _ in range(H):
        grid.append(next(iterator))
    
    A = int(next(iterator))
    B = int(next(iterator))
    C = int(next(iterator))
    D = int(next(iterator))
    
    # Convert to 0-indexed
    start_r, start_c = A - 1, B - 1
    target_r, target_c = C - 1, D - 1
    
    # Distance array
    dist = [[-1] * W for _ in range(H)]
    dist[start_r][start_c] = 0
    
    dq = deque([ (start_r, start_c) ])
    
    # Directions: up, down, left, right
    dr = [-1, 1, 0, 0]
    dc = [0, 0, -1, 1]
    
    while dq:
        r, c = dq.popleft()
        d = dist[r][c]
        
        # Zero-cost moves: to adjacent road cells
        for i in range(4):
            nr, nc = r + dr[i], c + dc[i]
            if 0 <= nr < H and 0 <= nc < W:
                if grid[nr][nc] == '.':
                    if dist[nr][nc] == -1 or dist[nr][nc] > d:
                        dist[nr][nc] = d
                        dq.appendleft((nr, nc))
        
        # One-cost moves: kick in each direction
        for i in range(4):
            # Kick direction: dr[i], dc[i]
            # Cells affected: (r + dr[i], c + dc[i]) and (r + 2*dr[i], c + 2*dc[i])
            # We can reach any cell in that line segment that is within bounds
            # The kick clears walls up to 2 steps away.
            # So from current cell (r,c), we can reach:
            #   (r + dr[i], c + dc[i]) if in bounds
            #   (r + 2*dr[i], c + 2*dc[i]) if in bounds
            # regardless of what they were originally.
            
            # First cell
            nr1 = r + dr[i]
            nc1 = c + dc[i]
            if 0 <= nr1 < H and 0 <= nc1 < W:
                if dist[nr1][nc1] == -1 or dist[nr1][nc1] > d + 1:
                    dist[nr1][nc1] = d + 1
                    dq.append((nr1, nc1))
            
            # Second cell
            nr2 = r + 2 * dr[i]
            nc2 = c + 2 * dc[i]
            if 0 <= nr2 < H and 0 <= nc2 < W:
                if dist[nr2][nc2] == -1 or dist[nr2][nc2] > d + 1:
                    dist[nr2][nc2] = d + 1
                    dq.append((nr2, nc2))
    
    print(dist[target_r][target_c])

if __name__ == "__main__":
    solve()
