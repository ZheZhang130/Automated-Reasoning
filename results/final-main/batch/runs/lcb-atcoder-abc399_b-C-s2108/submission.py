import sys
from collections import Counter

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    P = [int(input_data[i+1]) for i in range(N)]
    
    # Count frequencies of each score
    score_counts = Counter(P)
    
    # Get unique scores in descending order
    unique_scores = sorted(score_counts.keys(), reverse=True)
    
    # Calculate rank for each score group
    current_rank = 1
    rank_map = {}
    for score in unique_scores:
        count = score_counts[score]
        # All people with this score get the current rank
        rank_map[score] = current_rank
        # Advance rank by the number of people with this score
        current_rank += count
    
    # Print ranks in original order
    for i in range(N):
        print(rank_map[P[i]])

if __name__ == "__main__":
    solve()
