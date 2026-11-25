import sys

# Increase recursion depth just in case, though we use iterative BFS
sys.setrecursionlimit(300000)

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
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

    # BFS to color components and count sizes
    color = [-1] * (N + 1)
    comp_info = []  # List of (size_a, size_b) for each component
    
    for i in range(1, N + 1):
        if color[i] == -1:
            # Start BFS
            q = [i]
            color[i] = 0
            cnt0 = 0
            cnt1 = 0
            idx = 0
            while idx < len(q):
                u = q[idx]
                idx += 1
                if color[u] == 0:
                    cnt0 += 1
                else:
                    cnt1 += 1
                for v in adj[u]:
                    if color[v] == -1:
                        color[v] = 1 - color[u]
                        q.append(v)
            
            comp_info.append((cnt0, cnt1))

    # Count odd-sized components
    # A component is odd-sized if (cnt0 + cnt1) is odd.
    # Note: cnt0 + cnt1 is the size of the component.
    
    odd_components = []
    even_components = []
    
    for (a, b) in comp_info:
        total = a + b
        if total % 2 == 1:
            odd_components.append((a, b))
        else:
            even_components.append((a, b))
    
    k = len(odd_components)  # Number of odd-sized components
    t = 0  # Number of odd-sized components that are NOT singletons
    
    # Singletons are components of size 1 (0+1 or 1+0)
    # An odd-sized component is a singleton if one of its color classes is 0 and the other is 1.
    # Actually, a singleton component has size 1, so one color class is 1, the other is 0.
    
    for (a, b) in odd_components:
        if a == 1 and b == 0:
            t += 1
        elif a == 0 and b == 1:
            t += 1
    
    # If N is odd, the terminal graph has an even number of edges.
    # So the number of moves remaining is odd iff M is odd.
    # In that case, the first player (Aoki) wins if M is odd, loses if M is even.
    # Wait, let's re-read the logic.
    # If N is odd, the terminal graph is a complete bipartite graph with partitions of size (N-1)/2 and (N+1)/2?
    # No, the terminal graph is a complete bipartite graph. One partition has size x, the other N-x.
    # If N is odd, one partition has even size, the other odd size.
    # The number of edges in a complete bipartite graph K_{x, N-x} is x*(N-x).
    # If x is even, x*(N-x) is even. If x is odd, x*(N-x) is odd (since N-x is even).
    # Wait, if N is odd, one partition is even, the other is odd. So x*(N-x) is even.
    # So the terminal graph always has an even number of edges if N is odd.
    # Thus, the number of moves to reach the terminal state is (Total possible edges - M).
    # Total possible edges = N*(N-1)/2.
    # If N is odd, N*(N-1)/2 is even (since N-1 is even).
    # So the number of moves is even - M.
    # If M is odd, moves is odd. If M is even, moves is even.
    # So if N is odd, Aoki wins if M is odd, Takahashi wins if M is even.
    
    if N % 2 == 1:
        if M % 2 == 1:
            print("Aoki")
        else:
            print("Takahashi")
        return

    # If N is even, we use the logic from the plan.
    # k = number of odd-sized components.
    # t = number of odd-sized components that are NOT singletons.
    # d = sum of (a*b % 2) for even-sized components - M (mod 2).
    # But the plan says: "let d be the sum of the even-sized components' capacity parities minus m, modulo two."
    # Actually, the plan says: "Adding an edge within a component or merging two even-sized components flips d."
    # "Merging two singletons leaves d unchanged."
    # "Merging an even-sized component with an odd-sized one..."
    # Let's re-read the plan carefully.
    # The plan defines d as: (sum of (a*b % 2) for even-sized components - M) % 2.
    # But wait, the plan says: "Adding an edge within a component or merging two even-sized components flips d."
    # This suggests d is a state variable that changes.
    # However, the initial d is fixed.
    # Let's compute the initial d.
    
    # For even-sized components, capacity parity is (a*b) % 2.
    # For odd-sized components, capacity parity is 0 (since a*b is even? No, a*b is even if at least one is even.
    # But odd-sized components have a+b odd, so one is even, one is odd. So a*b is even.
    # So capacity parity is 0 for odd-sized components.
    # So d = (sum of (a*b % 2) for even-sized components - M) % 2.
    
    d = 0
    for (a, b) in even_components:
        d = (d + (a * b) % 2) % 2
    d = (d - M) % 2
    if d < 0:
        d += 2
    
    # Now apply the rules:
    # If k == 0: Aoki wins if d == 1, else Takahashi.
    # If k == 1 and t > 0: Aoki wins.
    # If k > 1:
    #   If t == 0: Aoki wins if d == (k-1) % 2, else Takahashi.
    #   If t == 1 or t == 2: Aoki wins.
    #   If t >= 3: Aoki wins if M is odd, else Takahashi.
    
    if k == 0:
        if d == 1:
            print("Aoki")
        else:
            print("Takahashi")
    elif k == 1:
        if t > 0:
            print("Aoki")
        else:
            # k=1, t=0. This means the only odd-sized component is a singleton.
            # But if k=1 and t=0, then the odd-sized component is a singleton.
            # The plan says: "If k=1 and t>0, Aoki wins."
            # What if k=1 and t=0?
            # The plan doesn't explicitly cover k=1, t=0.
            # But let's think: if k=1 and t=0, then the only odd-sized component is a singleton.
            # The other components are even-sized.
            # The plan says: "If k=1 and t>0, Aoki wins."
            # What if k=1 and t=0?
            # The plan says: "If k=0, ... If k=1 and t>0, ... If k>0, ... If t=0, ... If t=1 or t=2, ... If t>=3, ..."
            # So k=1, t=0 is not covered by the "k>0" rules directly?
            # Actually, the plan says: "If k>0, establish two more rules: if t=0, ... if t=1 or t=2, ... If t>=3, ..."
            # So k=1, t=0 falls under "t=0".
            # But the rule for t=0 is: "Aoki wins exactly when d=(k-1)%2".
            # So for k=1, t=0: Aoki wins if d == (1-1)%2 = 0, else Takahashi.
            if d == (k - 1) % 2:
                print("Aoki")
            else:
                print("Takahashi")
    else:
        # k > 1
        if t == 0:
            if d == (k - 1) % 2:
                print("Aoki")
            else:
                print("Takahashi")
        elif t == 1 or t == 2:
            print("Aoki")
        else:
            # t >= 3
            if M % 2 == 1:
                print("Aoki")
            else:
                print("Takahashi")

solve()
