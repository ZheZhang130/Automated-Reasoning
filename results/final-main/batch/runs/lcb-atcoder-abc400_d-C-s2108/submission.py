import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    H = int(input_data[0])
    W = int(input_data[1])
    grid = input_data[2:2+H]
    A, B, C, D = map(int, input_data[2+H:2+H+4])
    
    # Convert to 0-indexed
    start = (A-1, B-1)
    target = (C-1, D-1)
    
    # Distance array
    dist = [[-1]*W for _ in range(H)]
    dist[start[0]][start[1]] = 0
    
    dq = deque([start])
    
    while dq:
        r, c = dq.popleft()
        d = dist[r][c]
        
        # Zero cost moves: adjacent roads
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < H and 0 <= nc < W:
                if grid[nr][nc] == '.':
                    if dist[nr][nc] == -1 or dist[nr][nc] > d:
                        dist[nr][nc] = d
                        dq.appendleft((nr, nc))
        
        # One cost moves: kick in each direction
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            # Kick up to 2 steps
            for step in range(1, 3):
                nr, nc = r + dr*step, c + dc*step
                if 0 <= nr < H and 0 <= nc < W:
                    if dist[nr][nc] == -1 or dist[nr][nc] > d + 1:
                        dist[nr][nc] = d + 1
                        dq.append((nr, nc))
    
    print(dist[target[0]][target[1]])

if __name__ == "__main__":
    solve()
