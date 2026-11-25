import sys
from math import comb

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    N = int(input_data[0])
    P = int(input_data[1])
    
    D = N * (N - 1) // 2
    
    # Precompute binomial coefficients modulo P
    C = [[0] * (D + 1) for _ in range(D + 1)]
    for i in range(D + 1):
        C[i][0] = 1
        for j in range(1, i + 1):
            C[i][j] = (C[i-1][j-1] + C[i-1][j]) % P if i > 0 else 1
    
    # Precompute powers of (1+x)
    pow_a = [[0] * (D + 1) for _ in range(N + 1)]
    for a in range(N + 1):
        for k in range(a + 1):
            pow_a[a][k] = C[a][k] % P
    
    # Function to multiply two polynomials, truncating to degree D
    def poly_mul(a, b):
        deg_a = len(a) - 1
        deg_b = len(b) - 1
        res = [0] * (deg_a + deg_b + 1)
        for i in range(len(a)):
            if a[i] == 0:
                continue
            for j in range(len(b)):
                idx = i + j
                if idx <= D:
                    res[idx] = (res[idx] + a[i] * b[j]) % P
        return res
    
    # Function to raise polynomial to power b
    def poly_pow(base, power):
        if power == 0:
            return [1]
        if power == 1:
            return base
        if power % 2 == 0:
            half = poly_pow(base, power // 2)
            return poly_mul(half, half)
        else:
            half = poly_pow(base, power // 2)
            res = poly_mul(half, half)
            return poly_mul(res, base)
    
    # Precompute transition polynomials
    trans = [[None] * (N + 1) for _ in range(N + 1)]
    
    for a in range(1, N + 1):
        for b in range(1, N + 1):
            # Compute (1+x)^a - 1
            base_poly = [0] * (D + 1)
            for k in range(a):
                base_poly[k] = pow_a[a][k]
            base_poly[0] = (base_poly[0] - 1) % P
            
            # Raise to power b
            poly_b = poly_pow(base_poly, b)
            
            # Multiply by (1+x)^C(b,2)
            edges_in_layer = C[b][2]
            if edges_in_layer == 0:
                final_poly = poly_b
            else:
                inner = [0] * (D + 1)
                for k in range(edges_in_layer + 1):
                    inner[k] = C[edges_in_layer][k]
                final_poly = poly_mul(poly_b, inner)
            
            # Trim trailing zeros
            while len(final_poly) > 1 and final_poly[-1] == 0:
                final_poly.pop()
            
            trans[a][b] = final_poly
    
    # DP state: (e, o, last_parity, last_size)
    dp = {}
    
    # Initial state: L0 = {1}, which is even distance
    initial_key = (1, 0, 0, 1)
    initial_poly = [1]
    dp[initial_key] = initial_poly
    
    # Process states in increasing order of e + o
    for total in range(1, N):
        states = []
        for (e, o, last_parity, last_size) in dp:
            if e + o == total:
                states.append((e, o, last_parity, last_size))
        
        for (e, o, last_parity, last_size) in states:
            current_poly = dp[(e, o, last_parity, last_size)]
            
            remaining = N - (e + o)
            for b in range(1, remaining + 1):
                new_parity = 1 - last_parity
                
                if new_parity == 0:
                    if e + b <= N // 2:
                        ways = C[remaining][b] % P
                        t_poly = trans[last_size][b]
                        new_poly = poly_mul(current_poly, t_poly)
                        new_poly = [(c * ways) % P for c in new_poly]
                        
                        new_e = e + b
                        new_o = o
                        new_key = (new_e, new_o, new_parity, b)
                        
                        if new_key not in dp:
                            dp[new_key] = [0] * (D + 1)
                        for i in range(len(new_poly)):
                            dp[new_key][i] = (dp[new_key][i] + new_poly[i]) % P
                else:
                    if o + b <= N // 2:
                        ways = C[remaining][b] % P
                        t_poly = trans[last_size][b]
                        new_poly = poly_mul(current_poly, t_poly)
                        new_poly = [(c * ways) % P for c in new_poly]
                        
                        new_e = e
                        new_o = o + b
                        new_key = (new_e, new_o, new_parity, b)
                        
                        if new_key not in dp:
                            dp[new_key] = [0] * (D + 1)
                        for i in range(len(new_poly)):
                            dp[new_key][i] = (dp[new_key][i] + new_poly[i]) % P
    
    # Collect all terminal states
    terminal_states = []
    for (e, o, last_parity, last_size) in dp:
        if e == N // 2 and o == N // 2:
            terminal_states.append((e, o, last_parity, last_size))
    
    # Sum all terminal polynomials
    result_poly = [0] * (D + 1)
    for (e, o, last_parity, last_size) in terminal_states:
        poly = dp[(e, o, last_parity, last_size)]
        for i in range(len(poly)):
            result_poly[i] = (result_poly[i] + poly[i]) % P
    
    # Output coefficients from N-1 to D
    ans = []
    for m in range(N - 1, D + 1):
        if m < len(result_poly):
            ans.append(str(result_poly[m]))
        else:
            ans.append("0")
    
    print(" ".join(ans))

if __name__ == "__main__":
    solve()
