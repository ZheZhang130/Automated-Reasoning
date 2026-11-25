import sys
from sys import stdin

def main():
    data = stdin.read().split()
    if not data:
        return
    n = int(data[0])
    a = [int(data[i+1]) for i in range(n)]
    
    # Count how many aliens have >= 1 stone
    count_with_stones = sum(1 for x in a if x > 0)
    
    # For each alien i (0-indexed), they become adult at year i+1
    # When they become adult, they receive stones from all currently adult aliens with >= 1 stone
    # An alien j (j < i) is adult when i becomes adult if j <= i (which is always true for j < i)
    # So alien i receives stones from all aliens j where j < i and a[j] > 0
    # But wait, the stones given are consumed! So we need to track current stones.
    
    # Let's simulate properly:
    # We need to track current stones for each alien
    current_stones = list(a)
    
    for year in range(1, n + 1):
        # Alien 'year' becomes adult (1-indexed year, so alien index year-1)
        new_adult_idx = year - 1
        # Count how many adults (indices 0 to new_adult_idx) have >= 1 stone
        # But we need to check current_stones for indices 0 to new_adult_idx-1
        # Actually, all aliens from 0 to new_adult_idx are now adults
        # The new adult (new_adult_idx) receives stones from adults 0 to new_adult_idx-1 that have >= 1 stone
        
        # Count eligible donors (adults before this one becoming adult)
        donors = 0
        for i in range(new_adult_idx):
            if current_stones[i] > 0:
                donors += 1
        
        # Give stones
        current_stones[new_adult_idx] += donors
        # Remove stones from donors
        for i in range(new_adult_idx):
            if current_stones[i] > 0:
                current_stones[i] -= 1
    
    # Output
    print(' '.join(map(str, current_stones)))

if __name__ == "__main__":
    main()
