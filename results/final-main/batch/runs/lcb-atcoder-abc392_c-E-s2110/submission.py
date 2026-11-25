import sys
from sys import stdin

def solve():
    input_data = stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    
    P = [0] * N
    for i in range(N):
        P[i] = int(next(iterator)) - 1  # Convert to 0-indexed
    
    Q = [0] * N
    for i in range(N):
        Q[i] = int(next(iterator)) - 1  # Convert to 0-indexed
    
    # Build inverse mapping: bib_number -> person_index
    # Q[i] is the bib number worn by person i
    # So person_index = bib_number - 1 maps to i
    bib_to_person = [0] * N
    for i in range(N):
        bib_to_person[Q[i]] = i
    
    # For each bib number i (0-indexed), find who person wearing bib i is staring at
    # Person wearing bib i is at index bib_to_person[i]
    # That person is staring at P[bib_to_person[i]]
    # We need to output the bib number of the person they are staring at
    # Which is Q[P[bib_to_person[i]]] + 1
    
    result = []
    for bib_num in range(N):
        person_wearing_bib = bib_to_person[bib_num]
        person_staring_at = P[person_wearing_bib]
        bib_of_person_staring_at = Q[person_staring_at] + 1
        result.append(str(bib_of_person_staring_at))
    
    print(' '.join(result))

if __name__ == "__main__":
    solve()
