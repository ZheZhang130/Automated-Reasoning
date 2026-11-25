import sys

def count_good_integers(N):
    # We need to count numbers X <= N such that X = 2^a * b^2 for positive integers a, b.
    # This is equivalent to: X = 2^a * b^2
    # We can iterate over possible values of b.
    # Since b^2 <= N, b <= sqrt(N).
    # For each b, we iterate over possible values of a such that 2^a * b^2 <= N.
    # a can range from 1 to floor(log2(N / b^2)).
    # We use a set to count unique values.
    
    seen = set()
    b = 1
    while True:
        b_sq = b * b
        if b_sq > N:
            break
        
        # For this b, find max a such that 2^a * b_sq <= N
        # 2^a <= N / b_sq
        # a <= log2(N / b_sq)
        # We can compute max_a by repeatedly multiplying by 2
        
        max_val = N // b_sq
        a = 1
        while True:
            val = b_sq << a  # b_sq * 2^a
            if val > N:
                break
            seen.add(val)
            a += 1
        
        b += 1
    
    return len(seen)

def main():
    try:
        line = sys.stdin.read().strip()
        if not line:
            return
        N = int(line)
        result = count_good_integers(N)
        print(result)
    except Exception:
        pass

if __name__ == "__main__":
    main()
