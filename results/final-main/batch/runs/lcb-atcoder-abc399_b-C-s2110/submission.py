import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    P = [int(input_data[i+1]) for i in range(N)]
    
    # Store original indices
    indexed_P = list(enumerate(P))
    
    # Sort by score descending
    indexed_P.sort(key=lambda x: x[1], reverse=True)
    
    # Assign ranks
    rank = 1
    i = 0
    while i < N:
        j = i
        # Find all people with the same score
        while j < N and indexed_P[j][1] == indexed_P[i][1]:
            j += 1
        # All people from i to j-1 have the same score
        # They all get rank = rank
        for k in range(i, j):
            original_index = indexed_P[k][0]
            # Store the rank for this person
            pass
        # Update rank
        rank += (j - i)
        i = j
    
    # Now assign ranks back to original order
    ranks = [0] * N
    rank = 1
    indexed_P.sort(key=lambda x: x[1], reverse=True)
    i = 0
    while i < N:
        j = i
        while j < N and indexed_P[j][1] == indexed_P[i][1]:
            j += 1
        for k in range(i, j):
            original_index = indexed_P[k][0]
            ranks[original_index] = rank
        rank += (j - i)
        i = j
    
    for r in ranks:
        print(r)

if __name__ == "__main__":
    solve()
