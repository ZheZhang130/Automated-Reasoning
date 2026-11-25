import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    try:
        N = int(next(iterator))
        D = int(next(iterator))
        
        snakes = []
        for _ in range(N):
            T = int(next(iterator))
            L = int(next(iterator))
            snakes.append((T, L))
        
        for k in range(1, D + 1):
            max_weight = 0
            for T, L in snakes:
                weight = T * (L + k)
                if weight > max_weight:
                    max_weight = weight
            print(max_weight)
    except StopIteration:
        pass

if __name__ == "__main__":
    solve()
