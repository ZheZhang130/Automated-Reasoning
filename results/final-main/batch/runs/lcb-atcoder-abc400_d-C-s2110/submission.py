import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    idx = 0
    H = int(input_data[idx]); idx += 1
    W = int(input_data[idx]); idx += 1
    S = []
    for _ in range(H):
        S.append(input_data[idx]); idx += 1
    A = int(input_data[idx]); idx += 1
    B = int(input_data[idx]); idx += 1
    C = int(input_data[idx]); idx += 1
    D = int(input_data[idx]); idx += 1

    # Convert to 0-indexed
    start_r, start_c = A - 1, B - 1
    target_r, target_c = C - 1, D - 1

    # Grid: 0 for road, 1 for wall
    grid = [[0]*W for _ in range(H)]
    for i in range(H):
        for j in range(W):
            if S[i][j] == '#':
                grid[i][j] = 1

    # 0-1 BFS
    dist = [[float('inf')] * W for _ in range(H)]
    dist[start_r][start_c] = 0
    dq = deque()
    dq.append((start_r, start_c))

    while dq:
        r, c = dq.popleft()
        d = dist[r][c]

        # Zero-cost moves: to adjacent roads
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W:
                if grid[nr][nc] == 0:
                    if dist[nr][nc] > d:
                        dist[nr][nc] = d
                        dq.appendleft((nr, nc))

        # One-cost moves: kick in a direction
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            # Kick clears walls at (r+dr, c+dc) and (r+2*dr, c+2*dc)
            # We can reach either of these cells with 1 kick
            for step in [1, 2]:
                nr, nc = r + dr * step, c + dc * step
                if 0 <= nr < H and 0 <= nc < W:
                    if dist[nr][nc] > d + 1:
                        dist[nr][nc] = d + 1
                        dq.append((nr, nc))

    print(dist[target_r][target_c])

if __name__ == "__main__":
    solve()
