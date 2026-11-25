import sys
from sys import stdin

def main():
    input = stdin.readline
    
    N = int(input().strip())
    P = list(map(int, input().strip().split()))
    Q = list(map(int, input().strip().split()))
    
    # P[i-1] is the person that person i is staring at
    # Q[i-1] is the bib number worn by person i
    
    # We need to find: for each bib number i (from 1 to N),
    # who is the person wearing bib i staring at, and what bib number they are wearing.
    
    # Step 1: Create a mapping from person_id to bib_number
    # person_to_bib[person_id] = bib_number
    person_to_bib = [0] * (N + 1)
    for i in range(N):
        person_id = i + 1
        bib_number = Q[i]
        person_to_bib[person_id] = bib_number
    
    # Step 2: For each bib number i (from 1 to N), find the person wearing it
    # Then find who that person is staring at, and get their bib number.
    
    # bib_to_person[bib_number] = person_id
    bib_to_person = [0] * (N + 1)
    for i in range(N):
        bib_number = Q[i]
        person_id = i + 1
        bib_to_person[bib_number] = person_id
    
    # Step 3: For each bib number i, compute the answer
    result = []
    for bib_num in range(1, N + 1):
        person_wearing_bib = bib_to_person[bib_num]
        person_staring_at = P[person_wearing_bib - 1]  # P is 0-indexed
        bib_of_person_staring_at = person_to_bib[person_staring_at]
        result.append(bib_of_person_staring_at)
    
    print(*(result))

if __name__ == "__main__":
    main()
