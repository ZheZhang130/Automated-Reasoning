import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    P = list(map(int, input_data[1:N+1]))
    
    # Group people by their scores
    score_to_people = defaultdict(list)
    for i, score in enumerate(P):
        score_to_people[score].append(i)
    
    # Get all unique scores in descending order
    unique_scores = sorted(score_to_people.keys(), reverse=True)
    
    # Track ranks
    ranks = [0] * N
    
    r = 1
    for score in unique_scores:
        people_with_score = score_to_people[score]
        # Assign current rank r to all these people
        for person_idx in people_with_score:
            ranks[person_idx] = r
        # Update r by adding the number of people with this score
        r += len(people_with_score)
    
    # Output ranks for each person (1-indexed in problem, but we stored 0-indexed)
    for rank in ranks:
        print(rank)

if __name__ == "__main__":
    solve()
