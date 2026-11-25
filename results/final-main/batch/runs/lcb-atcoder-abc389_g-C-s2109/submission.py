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
        for j in range(i + 1):
            C[i][j] = comb(i, j) % P
    
    # For a connected graph, the BFS layers from vertex 1 are:
    # L0 = {1} (even distance)
    # L1 = vertices at distance 1 (odd distance)
    # L2 = vertices at distance 2 (even distance)
    # etc.
    # 
    # For a graph to be balanced, we need |even| = |odd| = N/2
    # 
    # The structure is: L0, L1, L2, ..., Lk where:
    # - L0 has size 1 (vertex 1)
    # - Each Li (i > 0) must have at least one edge to Li-1
    # - Edges can only exist within layers or between consecutive layers
    # 
    # We need to count graphs where sum of sizes of even-indexed layers = sum of sizes of odd-indexed layers = N/2
    
    # Let's enumerate all possible layer size sequences
    # L0 = 1, and we need to partition N-1 vertices into layers L1, L2, ..., Lk
    # such that sum of even-indexed layers (L0, L2, L4, ...) = N/2
    # and sum of odd-indexed layers (L1, L3, L5, ...) = N/2
    
    # Since L0 = 1, we need sum of L2 + L4 + ... = N/2 - 1
    # And sum of L1 + L3 + ... = N/2
    
    # Let's enumerate all compositions of N-1 into k parts
    # and check which ones satisfy the balance condition
    
    # For each valid layer size sequence, we compute the number of graphs
    
    def count_graphs_for_layers(layer_sizes):
        """
        layer_sizes is a list [L0, L1, L2, ..., Lk] where L0 = 1
        Returns the number of graphs with this layer structure.
        """
        # Check balance condition
        even_sum = sum(layer_sizes[i] for i in range(0, len(layer_sizes), 2))
        odd_sum = sum(layer_sizes[i] for i in range(1, len(layer_sizes), 2))
        if even_sum != N // 2 or odd_sum != N // 2:
            return 0
        
        # Compute the number of ways to form this layer structure
        # For each layer Li (i > 0), we need at least one edge to Li-1
        # Edges within Li: any subset of possible edges
        # Edges between Li-1 and Li: at least one, at most all possible
        
        total_edges = 0
        ways = 1
        
        for i in range(1, len(layer_sizes)):
            Li = layer_sizes[i]
            Li_1 = layer_sizes[i - 1]
            
            # Edges within Li: any subset of Li*(Li-1)/2 edges
            edges_within = Li * (Li - 1) // 2
            ways_within = comb(2, edges_within) % P  # This is wrong, need to compute properly
            
            # Actually, we need to compute the polynomial for edges
            # Let's use a different approach
            
        return 0
    
    # Let me use a different approach: enumerate all layer structures and compute counts
    
    # Generate all compositions of N-1
    def generate_compositions(n, max_parts):
        """Generate all compositions of n into at most max_parts parts."""
        if n == 0:
            yield []
            return
        for first in range(1, n + 1):
            for rest in generate_compositions(n - first, max_parts - 1):
                yield [first] + rest
    
    # For each composition, check if it satisfies the balance condition
    # and compute the number of graphs
    
    # Precompute binomial coefficients for edge counting
    # For layer sizes a, b:
    # - Edges within layer of size b: (1+x)^(b*(b-1)/2)
    # - Edges between layer a and b: ((1+x)^a - 1)^b
    
    # Let's compute this more carefully
    # For a transition from layer of size a to layer of size b:
    # - Each vertex in b must have at least one edge to a
    # - Edges within b are optional
    
    # The polynomial for one vertex in b connecting to a is:
    # (1 + x)^a - 1 (at least one edge to a)
    # For b vertices: ((1+x)^a - 1)^b
    # Edges within b: (1+x)^(b*(b-1)/2)
    
    # Let's precompute these polynomials
    trans = [[None] * (N + 1) for _ in range(N + 1)]
    
    for a in range(1, N + 1):
        for b in range(1, N + 1):
            # Compute (1+x)^a - 1
            poly1 = [0] * (a + 1)
            for i in range(1, a + 1):
                poly1[i] = C[a][i] % P
            
            # Compute (1+x)^(b*(b-1)//2)
            exp1 = b * (b - 1) // 2
            poly2 = [0] * (exp1 + 1)
            for i in range(exp1 + 1):
                poly2[i] = C[exp1][i] % P
            
            # Compute ((1+x)^a - 1)^b
            poly3 = [0] * (a * b + 1)
            poly3[0] = 1
            for _ in range(b):
                new_poly = [0] * (len(poly3) + len(poly1) - 1)
                for i in range(len(poly3)):
                    if poly3[i] == 0:
                        continue
                    for j in range(len(poly1)):
                        new_poly[i + j] = (new_poly[i + j] + poly3[i] * poly1[j]) % P
                poly3 = new_poly
            
            # Multiply poly2 and poly3
            poly4 = [0] * (len(poly2) + len(poly3) - 1)
            for i in range(len(poly2)):
                if poly2[i] == 0:
                    continue
                for j in range(len(poly3)):
                    poly4[i + j] = (poly4[i + j] + poly2[i] * poly3[j]) % P
            
            trans[a][b] = poly4
    
    def convolve(poly1, poly2, mod):
        if not poly1 or not poly2:
            return []
        result = [0] * (len(poly1) + len(poly2) - 1)
        for i in range(len(poly1)):
            if poly1[i] == 0:
                continue
            for j in range(len(poly2)):
                result[i + j] = (result[i + j] + poly1[i] * poly2[j]) % mod
        return result
    
    # Now enumerate all layer structures
    # L0 = 1, and we need to partition N-1 into layers L1, L2, ..., Lk
    # such that sum of even-indexed layers = N/2 and sum of odd-indexed layers = N/2
    
    # Generate all compositions of N-1
    compositions = []
    def gen_comps(n, max_len):
        if n == 0:
            yield []
            return
        for first in range(1, n + 1):
            for rest in gen_comps(n - first, max_len - 1):
                yield [first] + rest
    
    for comp in gen_comps(N - 1, N):
        # comp is [L1, L2, ..., Lk]
        # Full layer sizes: [1] + comp
        full_layers = [1] + comp
        
        # Check balance
        even_sum = 1 + sum(full_layers[i] for i in range(2, len(full_layers), 2))
        odd_sum = sum(full_layers[i] for i in range(1, len(full_layers), 2))
        
        if even_sum == N // 2 and odd_sum == N // 2:
            # Compute the number of graphs for this layer structure
            # We need to choose which vertices go to each layer
            # and count the edge configurations
            
            # Number of ways to choose vertices for each layer
            # L0 is fixed (vertex 1)
            # For each subsequent layer, we choose vertices from remaining
            
            ways_choose = 1
            remaining = N - 1
            for i in range(1, len(full_layers)):
                Li = full_layers[i]
                ways_choose = (ways_choose * C[remaining][Li]) % P
                remaining -= Li
            
            # Now compute the edge configurations
            # For each transition from Li-1 to Li, multiply by trans[Li-1][Li]
            edge_poly = [1]  # Start with 1 (0 edges)
            for i in range(1, len(full_layers)):
                a = full_layers[i - 1]
                b = full_layers[i]
                edge_poly = convolve(edge_poly, trans[a][b], P)
            
            # Multiply by ways_choose
            edge_poly = [(c * ways_choose) % P for c in edge_poly]
            
            # Add to answer
            for m, coeff in enumerate(edge_poly):
                if m <= D:
                    ans[m] = (ans[m] + coeff) % P
    
    # Output for M = N-1 to D
    ans = [0] * (D + 1)
    
    # Re-run the computation
    for comp in gen_comps(N - 1, N):
        full_layers = [1] + comp
        
        even_sum = 1 + sum(full_layers[i] for i in range(2, len(full_layers), 2))
        odd_sum = sum(full_layers[i] for i in range(1, len(full_layers), 2))
        
        if even_sum == N // 2 and odd_sum == N // 2:
            ways_choose = 1
            remaining = N - 1
            for i in range(1, len(full_layers)):
                Li = full_layers[i]
                ways_choose = (ways_choose * C[remaining][Li]) % P
                remaining -= Li
            
            edge_poly = [1]
            for i in range(1, len(full_layers)):
                a = full_layers[i - 1]
                b = full_layers[i]
                edge_poly = convolve(edge_poly, trans[a][b], P)
            
            edge_poly = [(c * ways_choose) % P for c in edge_poly]
            
            for m, coeff in enumerate(edge_poly):
                if m <= D:
                    ans[m] = (ans[m] + coeff) % P
    
    result = []
    for M in range(N - 1, D + 1):
        result.append(str(ans[M]))
    
    print(" ".join(result))

if __name__ == "__main__":
    solve()
