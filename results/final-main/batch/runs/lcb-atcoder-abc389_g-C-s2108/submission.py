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
    
    # Helper to compute (1+x)^k mod P
    def poly_pow_one_plus_x(k):
        res = [1] * (k + 1)
        for i in range(1, k + 1):
            res[i] = res[i-1] % P
        return res
    
    # Helper to compute (1+x)^a - 1
    def poly_minus_one(p):
        return p[1:]
    
    # Precompute powers of (1+x) for a from 1 to N
    pow_1_plus_x = [None] * (N + 1)
    for a in range(1, N + 1):
        pow_1_plus_x[a] = poly_pow_one_plus_x(a)
    
    # Precompute transition polynomials
    trans = [[None] * (N + 1) for _ in range(N + 1)]
    
    for a in range(1, N + 1):
        for b in range(1, N + 1):
            edges_in_layer = b * (b - 1) // 2
            poly1 = poly_pow_one_plus_x(edges_in_layer)
            
            poly2_base = poly_minus_one(pow_1_plus_x[a])
            poly2 = [1]
            for _ in range(b):
                new_poly = [0] * (len(poly2) + len(poly2_base) - 1)
                for i in range(len(poly2)):
                    for j in range(len(poly2_base)):
                        new_poly[i+j] = (new_poly[i+j] + poly2[i] * poly2_base[j]) % P
                poly2 = new_poly
            
            poly_trans = [0] * (len(poly1) + len(poly2) - 1)
            for i in range(len(poly1)):
                for j in range(len(poly2)):
                    poly_trans[i+j] = (poly_trans[i+j] + poly1[i] * poly2[j]) % P
            
            trans[a][b] = poly_trans
    
    # DP state: dp[e][o][parity][last_size] = list of polynomials
    dp = {}
    start_state = (1, 0, 0, 1)
    dp[start_state] = [[1]]
    
    # Process states in increasing order of e + o
    for total in range(1, N):
        states = [(e, o, parity, last_size, polys) for (e, o, parity, last_size), polys in dp.items() if e + o == total]
        
        for e, o, parity, last_size, polys in states:
            for b in range(1, N - total + 1):
                new_e = e + (1 if parity == 0 else 0)
                new_o = o + (1 if parity == 1 else 0)
                
                remaining = N - (e + o)
                if b > remaining:
                    continue
                
                new_parity = 1 - parity
                
                ways_choose = comb(remaining, b) % P
                
                for poly in polys:
                    poly_scaled = [(coeff * ways_choose) % P for coeff in poly]
                    
                    trans_poly = trans[last_size][b]
                    
                    new_poly = [0] * (len(poly_scaled) + len(trans_poly) - 1)
                    for i in range(len(poly_scaled)):
                        for j in range(len(trans_poly)):
                            new_poly[i+j] = (new_poly[i+j] + poly_scaled[i] * trans_poly[j]) % P
                    
                    new_state = (new_e, new_o, new_parity, b)
                    if new_state not in dp:
                        dp[new_state] = []
                    dp[new_state].append(new_poly)
    
    # Collect all terminal states (e + o == N)
    terminal_polys = []
    for (e, o, parity, last_size), polys in dp.items():
        if e + o == N:
            terminal_polys.extend(polys)
    
    # Debug: print terminal polys
    print(f"Terminal polys: {len(terminal_polys)}")
    for i, poly in enumerate(terminal_polys):
        print(f"  poly {i}: len={len(poly)}, {poly[:10]}...")
    
    # Sum all terminal polynomials
    if not terminal_polys:
        result = [0] * (D + 1)
    else:
        # Find max degree needed
        max_deg = D
        result = [0] * (max_deg + 1)
        for poly in terminal_polys:
            for i in range(len(poly)):
                result[i] = (result[i] + poly[i]) % P
    
    # Output coefficients from N-1 to D
    ans = ' '.join(str(result[i]) for i in range(N - 1, D + 1))
    print(ans)

if __name__ == '__main__':
    solve()
