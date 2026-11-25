import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    A = [int(x) for x in data[1:N+1]]
    
    # Track current stones for each alien
    current = A[:]
    
    # For each year from 1 to N:
    # - Alien i becomes adult at year i
    # - All previously adult aliens (1 to i-1) with >=1 stone give 1 stone to alien i
    # - Alien i receives (number of adults with >=1 stone) stones
    # - Each adult who gave loses 1 stone
    
    for year in range(1, N+1):
        # Alien 'year' becomes adult this year
        # Count how many aliens 1..year-1 have >=1 stone
        donors = 0
        for i in range(1, year):
            if current[i-1] >= 1:
                donors += 1
                current[i-1] -= 1
        
        # Alien 'year' receives donors stones
        current[year-1] += donors
    
    print(' '.join(map(str, current)))

if __name__ == "__main__":
    main()
