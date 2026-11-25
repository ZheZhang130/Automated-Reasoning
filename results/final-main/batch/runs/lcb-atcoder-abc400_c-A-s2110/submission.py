import sys

def solve():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        N = int(line)
    except ValueError:
        return

    # We need to count X in [1, N] such that X = 2^a * b^2 for positive integers a, b.
    # This is equivalent to: X = 2^E * m^2, where m is odd and E >= 1.
    # We iterate over odd m such that m^2 <= N.
    # For each m, let M = m^2. Then we need 2^E * M <= N => 2^E <= N // M.
    # Let K = N // M. The number of E >= 1 such that 2^E <= K is floor(log2(K)) if K >= 2.
    # This is computed as K.bit_length() - 1.
    
    count = 0
    m = 1
    while True:
        m2 = m * m
        if m2 > N:
            break
        K = N // m2
        if K >= 2:
            count += (K.bit_length() - 1)
        m += 2

    print(count)

if __name__ == "__main__":
    solve()
