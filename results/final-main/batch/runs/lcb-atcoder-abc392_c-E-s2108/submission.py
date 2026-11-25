import sys
from sys import stdin

def solve():
    input_data = stdin.read().split()
    idx = 0
    N = int(input_data[idx])
    idx += 1
    
    P = [0] * N
    for i in range(N):
        P[i] = int(input_data[idx])
        idx += 1
    
    Q = [0] * N
    for i in range(N):
        Q[i] = int(input_data[idx])
        idx += 1
    
    # P[i] is the person that person (i+1) is staring at
    # Q[i] is the bib number worn by person (i+1)
    # We need to find: for each bib number i (1 to N), 
    # who is the person wearing bib i, and then who that person is staring at,
    # and finally what bib number that person is wearing.
    
    # Step 1: Create a mapping from bib number to person index
    # bib_to_person[bib_number] = person_index (0-based)
    bib_to_person = [0] * (N + 1)
    for i in range(N):
        person_idx = i  # 0-based index for person (i+1)
        bib_num = Q[i]
        bib_to_person[bib_num] = person_idx
    
    # Step 2: For each bib number i from 1 to N:
    # - Find the person wearing bib i: person_idx = bib_to_person[i]
    # - Find who that person is staring at: target_person = P[person_idx] - 1 (convert to 0-based)
    # - Find the bib number worn by target_person: bib_num = Q[target_person]
    
    result = []
    for bib_num in range(1, N + 1):
        person_idx = bib_to_person[bib_num]
        target_person_idx = P[person_idx] - 1  # P is 1-based, convert to 0-based
        bib_num_target = Q[target_person_idx]
        result.append(str(bib_num_target))
    
    print(" ".join(result))

if __name__ == "__main__":
    solve()
