import sys
from collections import deque

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    iterator = iter(input_data)
    N = int(next(iterator))
    M = int(next(iterator))
    
    adj = [[] for _ in range(N + 1)]
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        adj[u].append(v)
        adj[v].append(u)
    
    color = [-1] * (N + 1)
    odd_comp_count = 0
    even_comp_count = 0
    odd_non_singleton_count = 0
    
    for start in range(1, N + 1):
        if color[start] != -1:
            continue
        q = deque([start])
        color[start] = 0
        comp_size = 0
        while q:
            u = q.popleft()
            comp_size += 1
            for v in adj[u]:
                if color[v] == -1:
                    color[v] = 1 - color[u]
                    q.append(v)
        
        c0 = sum(1 for i in range(1, N + 1) if color[i] == 0)
        c1 = sum(1 for i in range(1, N + 1) if color[i] == 1)
        
        if comp_size == 1:
            if c0 == 1 and c1 == 0:
                odd_comp_count += 1
                odd_non_singleton_count += 1
            elif c0 == 0 and c1 == 1:
                odd_comp_count += 1
                odd_non_singleton_count += 1
        else:
            if comp_size % 2 == 1:
                odd_comp_count += 1
            else:
                even_comp_count += 1
    
    if N % 2 == 1:
        print("Aoki" if M % 2 == 1 else "Takahashi")
        return
    
    k = odd_comp_count
    t = odd_non_singleton_count
    d = (M + k) % 2
    
    if k == 0:
        print("Aoki" if d == 1 else "Takahashi")
    elif k == 1:
        if t > 0:
            print("Aoki")
        else:
            print("Takahashi" if d == 0 else "Aoki")
    else:
        if t >= 3:
            print("Aoki" if d == 1 else "Takahashi")
        elif t == 2:
            print("Aoki")
        elif t == 1:
            print("Aoki")
        else:
            print("Takahashi" if d == (k - 1) % 2 else "Aoki")

if __name__ == "__main__":
    solve()
