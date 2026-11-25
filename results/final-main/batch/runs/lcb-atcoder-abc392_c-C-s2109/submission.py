import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    
    P = [0] * (N + 1)
    for i in range(1, N + 1):
        P[i] = int(next(iterator))
    
    Q = [0] * (N + 1)
    for i in range(1, N + 1):
        Q[i] = int(next(iterator))
    
    # For each bib number i (from 1 to N), find who is wearing bib i,
    # then find who that person is staring at, and output the bib number of that person.
    
    # Let's denote:
    # - person j is wearing bib Q[j]
    # - person j is staring at person P[j]
    # - We want to find, for each bib number i, the bib number of the person that the person wearing bib i is staring at.
    
    # Step 1: Find the person wearing bib i. Let this be person j such that Q[j] == i.
    # Step 2: That person j is staring at person P[j].
    # Step 3: The bib number of person P[j] is Q[P[j]].
    
    # So for each bib number i, we need to find j such that Q[j] == i, then output Q[P[j]].
    
    # Since Q is a permutation, we can create an inverse mapping: bib_to_person[bib] = person
    bib_to_person = [0] * (N + 1)
    for person in range(1, N + 1):
        bib_to_person[Q[person]] = person
    
    result = []
    for bib_i in range(1, N + 1):
        person_wearing_bib_i = bib_to_person[bib_i]
        person_stared_at = P[person_wearing_bib_i]
        bib_of_person_stared_at = Q[person_stared_at]
        result.append(str(bib_of_person_stared_at))
    
    print(" ".join(result))

if __name__ == "__main__":
    solve()
