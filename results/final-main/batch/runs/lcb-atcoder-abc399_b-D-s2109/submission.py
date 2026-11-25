import sys
from collections import defaultdict

def main():
    data = sys.stdin.read().split()
    if not data:
        return
    N = int(data[0])
    P = [int(data[i+1]) for i in range(N)]

    # Group people by score
    score_to_people = defaultdict(list)
    for i, score in enumerate(P):
        score_to_people[score].append(i)

    # Sort scores in descending order
    sorted_scores = sorted(score_to_people.keys(), reverse=True)

    # Determine ranks
    r = 1
    ranks = [0] * N
    for score in sorted_scores:
        people = score_to_people[score]
        for idx in people:
            ranks[idx] = r
        r += len(people)

    # Output ranks in person-label order (1 to N)
    for i in range(N):
        print(ranks[i])

if __name__ == "__main__":
    main()
