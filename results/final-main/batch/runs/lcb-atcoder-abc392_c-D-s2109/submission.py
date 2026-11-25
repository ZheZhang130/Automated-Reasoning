import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    
    # P is the list of gaze targets: P[i] is the person that person (i+1) is staring at
    P = [int(next(iterator)) for _ in range(N)]
    
    # Q is the list of bib numbers: Q[i] is the bib number worn by person (i+1)
    Q = [int(next(iterator)) for _ in range(N)]
    
    # We need to find, for each bib number i (from 1 to N), 
    # the bib number of the person that the wearer of bib i is staring at.
    
    # Step 1: Create a mapping from person number to bib number
    # person_to_bib[person] = bib
    person_to_bib = [0] * (N + 1)
    for person_idx, bib in enumerate(Q):
        person = person_idx + 1
        person_to_bib[person] = bib
    
    # Step 2: For each bib number i (from 1 to N), find the person wearing bib i
    # Then find who that person is staring at, and get that person's bib number.
    
    # We can create an inverse mapping: bib_to_person[bib] = person
    bib_to_person = [0] * (N + 1)
    for person_idx, bib in enumerate(Q):
        bib_to_person[bib] = person_idx + 1
    
    # Now, for each bib i from 1 to N:
    #   person_staring_at = bib_to_person[i]
    #   target_person = P[person_staring_at - 1]  (since P is 0-indexed)
    #   target_bib = person_to_bib[target_person]
    
    result = []
    for bib in range(1, N + 1):
        person_wearing_bib = bib_to_person[bib]
        target_person = P[person_wearing_bib - 1]
        target_bib = person_to_bib[target_person]
        result.append(str(target_bib))
    
    print(" ".join(result))

if __name__ == "__main__":
    solve()
