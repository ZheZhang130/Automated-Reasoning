import sys
from collections import defaultdict

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    N = int(input_data[0])
    P = [int(x) for x in input_data[1:]]
    
    # Group people by their scores
    score_to_people = defaultdict(list)
    for i, score in enumerate(P):
        score_to_people[score].append(i + 1)  # Store 1-based person index
    
    # Get unique scores in descending order
    unique_scores = sorted(score_to_people.keys(), reverse=True)
    
    r = 1
    ranks = [0] * (N + 1)  # 1-based indexing for convenience
    
    for score in unique_scores:
        people_with_score = score_to_people[score]
        num_people = len(people_with_score)
        
        # Assign rank r to all these people
        for person_idx in people_with_score:
            ranks[person_idx] = r
        
        # Update r
        r += num_people
    
    # Output ranks for persons 1 to N
    for i in range(1, N + 1):
        print(ranks[i])

if __name__ == "__main__":
    solve()
