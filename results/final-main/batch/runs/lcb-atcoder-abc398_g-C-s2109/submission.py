import sys

# Increase recursion depth just in case, though we use iterative BFS
sys.setrecursionlimit(300000)

def solve():
    input = sys.stdin.read
    data = input().split()
    iterator = iter(data)
    
    try:
        N = int(next(iterator))
        M = int(next(iterator))
    except StopIteration:
        return

    adj = [[] for _ in range(N + 1)]
    for _ in range(M):
        u = int(next(iterator))
        v = int(next(iterator))
        adj[u].append(v)
        adj[v].append(u)

    # 2-color each connected component
    color = [-1] * (N + 1)
    comp_info = []  # List of (size_a, size_b) for each component

    for i in range(1, N + 1):
        if color[i] == -1:
            # BFS
            q = [i]
            color[i] = 0
            size_a = 0
            size_b = 0
            idx = 0
            while idx < len(q):
                u = q[idx]
                idx += 1
                if color[u] == 0:
                    size_a += 1
                else:
                    size_b += 1
                for v in adj[u]:
                    if color[v] == -1:
                        color[v] = 1 - color[u]
                        q.append(v)
            comp_info.append((size_a, size_b))

    # Count number of odd-sized components
    # A component is odd-sized if (size_a + size_b) is odd
    odd_comp_count = 0
    for sa, sb in comp_info:
        if (sa + sb) % 2 == 1:
            odd_comp_count += 1

    # Count number of odd-sized components that are NOT singletons
    # A singleton component has size 1 (so sa=1, sb=0 or vice versa)
    odd_non_singleton_count = 0
    for sa, sb in comp_info:
        if (sa + sb) % 2 == 1 and (sa + sb) > 1:
            odd_non_singleton_count += 1

    # Apply the logic from the plan
    # k = number of odd-sized components = odd_comp_count
    # t = number of odd-sized components that are not singletons = odd_non_singleton_count
    # m = M (current edge count)
    
    k = odd_comp_count
    t = odd_non_singleton_count
    m = M

    if N % 2 == 1:
        # N is odd
        # Terminal graph has even number of edges because one color class has even size.
        # Number of moves remaining is odd exactly when M is odd.
        # Aoki wins if moves remaining is odd (since Aoki goes first and wins if he can make the last move)
        # Wait, let's re-read: "A player who cannot perform this operation loses"
        # So if moves remaining is odd, Aoki (1st) makes move 1, Takahashi (2nd) makes move 2, ...
        # If total moves is odd, Aoki makes the last move and Takahashi cannot move -> Aoki wins.
        # If total moves is even, Takahashi makes the last move -> Takahashi wins.
        # So Aoki wins if (max_moves - M) is odd.
        # But the plan says: "Thus the number of moves remaining is odd exactly when M is odd."
        # This implies max_moves is even when N is odd.
        # So if M is odd, moves remaining is odd -> Aoki wins.
        # If M is even, moves remaining is even -> Takahashi wins.
        if M % 2 == 1:
            print("Aoki")
        else:
            print("Takahashi")
    else:
        # N is even
        # k = number of odd-sized components
        # t = number of odd-sized components that are not singletons
        # d = (sum of capacity parities of even-sized components - M) mod 2
        # But the plan doesn't explicitly use d for the final decision in all cases.
        # Let's re-read the plan's conclusion for even N:
        # "For t>=3, the player to move wins exactly when m is odd."
        # "For t=0, the player to move wins exactly when d=(k-1) mod 2"
        # "For t=1 or t=2, the player to move always wins."
        # "For k=0, all subsequent components remain even-sized, so the parity of the remaining number of moves is fixed at d.
        #  The player to move wins exactly when d=1"
        
        # We need to compute d.
        # d = (sum of capacity parities of even-sized components - M) mod 2
        # Capacity parity of a component = (size_a * size_b) mod 2
        # For even-sized components (size_a + size_b is even), capacity parity is 0 if both sizes are even, 1 if one is odd.
        # But wait, if size_a + size_b is even, then either both are even or both are odd.
        # If both are even, size_a * size_b is even -> capacity parity 0.
        # If both are odd, size_a * size_b is odd -> capacity parity 1.
        # So for even-sized components, capacity parity is 1 if both sizes are odd, 0 otherwise.
        
        d = 0
        for sa, sb in comp_info:
            if (sa + sb) % 2 == 0:
                # Even-sized component
                if (sa % 2 == 1) and (sb % 2 == 1):
                    d = (d + 1) % 2
            else:
                # Odd-sized component
                # Capacity parity is 0 (as per plan: "Odd-sized components have capacity parity zero")
                pass
        
        d = (d - M) % 2
        if d < 0:
            d += 2
        d = d % 2
        
        if k == 0:
            # All components are even-sized
            if d == 1:
                print("Aoki")
            else:
                print("Takahashi")
        elif k == 1:
            # One odd-sized component
            if t > 0:
                print("Aoki")
            else:
                # t = 0, so the odd-sized component is a singleton
                # But wait, if k=1 and t=0, then the only odd-sized component is a singleton.
                # The plan says: "If k=1 and t>0, the player to move wins."
                # What if k=1 and t=0?
                # The plan doesn't explicitly cover this, but let's think.
                # If k=1 and t=0, then we have one singleton odd component and the rest are even-sized.
                # The plan's rule for t=0 says: "the player to move wins exactly when d=(k-1) mod 2"
                # Here k=1, so (k-1) mod 2 = 0.
                # So if d=0, Aoki wins; if d=1, Takahashi wins.
                if d == 0:
                    print("Aoki")
                else:
                    print("Takahashi")
        else:
            # k >= 2
            if t >= 3:
                if m % 2 == 1:
                    print("Aoki")
                else:
                    print("Takahashi")
            elif t == 0:
                # t=0, so all odd-sized components are singletons
                # The plan says: "For t=0, the player to move wins exactly when d=(k-1) mod 2"
                if d == (k - 1) % 2:
                    print("Aoki")
                else:
                    print("Takahashi")
            else:
                # t=1 or t=2
                print("Aoki")

solve()
