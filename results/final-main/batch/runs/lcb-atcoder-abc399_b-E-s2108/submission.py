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
    
    r = 1
    ranks = [0] * N
    
    for score in unique_scores:
        people_with_score = score_to_people[score]
        k = len(people_with_score)
        
        # Assign rank r to all these people
        for person_idx in people_with_score:
            ranks[person_idx] = r
        
        # Update r
        r += k
    
    # Print ranks (1-indexed people, so we print in order 0 to N-1)
    for rank in ranks:
        print(rank)

if __name__ == "__main__":
    solve()
