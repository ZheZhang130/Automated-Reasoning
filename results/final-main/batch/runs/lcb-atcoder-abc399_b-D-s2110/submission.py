import sys
from collections import defaultdict

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    P = [int(data[i+1]) for i in range(N)]
    
    # Group people by score
    score_to_people = defaultdict(list)
    for i, score in enumerate(P):
        score_to_people[score].append(i)
    
    # Get all unique scores in descending order
    unique_scores = sorted(score_to_people.keys(), reverse=True)
    
    r = 1
    ranks = [0] * N
    
    for score in unique_scores:
        people_with_score = score_to_people[score]
        # Assign current rank r to all these people
        for person_idx in people_with_score:
            ranks[person_idx] = r
        # Add the number of people with this score to r
        r += len(people_with_score)
    
    # Output ranks in person-label order (1 to N)
    for i in range(N):
        print(ranks[i])

if __name__ == "__main__":
    solve()
