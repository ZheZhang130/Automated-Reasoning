import sys
from collections import defaultdict

def main():
    data = sys.stdin.read().split()
    if not data:
        return
    
    N = int(data[0])
    P = [int(data[i+1]) for i in range(N)]
    
    # Track which people have undetermined ranks
    undetermined = set(range(N))
    
    # Current rank counter
    r = 1
    
    # We need to process scores in descending order
    # Group people by their scores
    score_to_people = defaultdict(list)
    for i, score in enumerate(P):
        score_to_people[score].append(i)
    
    # Get all unique scores and sort them in descending order
    unique_scores = sorted(score_to_people.keys(), reverse=True)
    
    # Assign ranks
    result = [0] * N
    
    for score in unique_scores:
        people_with_score = score_to_people[score]
        
        # Determine rank for all people with this score
        for person_idx in people_with_score:
            result[person_idx] = r
        
        # Update r by adding the number of people with this score
        r += len(people_with_score)
    
    # Print results
    for rank in result:
        print(rank)

if __name__ == "__main__":
    main()
