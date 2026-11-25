import sys
from collections import Counter

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    P = list(map(int, input_data[1:N+1]))
    
    # Count frequencies of each score
    score_counts = Counter(P)
    
    # Sort unique scores in descending order
    unique_scores = sorted(score_counts.keys(), reverse=True)
    
    # Calculate rank for each score group
    rank = 1
    score_to_rank = {}
    for score in unique_scores:
        count = score_counts[score]
        # All people with this score get the current rank
        score_to_rank[score] = rank
        # Then we add the count to rank for the next group
        rank += count
    
    # Print ranks in original input order
    for p in P:
        print(score_to_rank[p])

if __name__ == "__main__":
    solve()
