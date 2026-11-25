import sys

def solve():
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    
    iterator = iter(input_data)
    N = int(next(iterator))
    
    P = []
    for _ in range(N):
        P.append(int(next(iterator)))
    
    Q = []
    for _ in range(N):
        Q.append(int(next(iterator)))
    
    # P[i] is the person that person (i+1) is staring at (0-indexed)
    # Q[i] is the bib number worn by person (i+1)
    # We need to find, for each bib number i (from 1 to N), 
    # the bib number of the person that the wearer of bib i is staring at.
    
    # Step 1: Create a mapping from person_id to their bib number
    # person_id is 1-indexed, so we'll use 0-indexed internally
    person_to_bib = [0] * N
    for i in range(N):
        person_id = i + 1
        bib_number = Q[i]
        person_to_bib[person_id - 1] = bib_number
    
    # Step 2: For each bib number i (from 1 to N), find the person wearing it
    # Then find who that person is staring at, and get that person's bib number.
    
    bib_to_person = [0] * N
    for i in range(N):
        bib_number = Q[i]
        person_id = i + 1
        bib_to_person[bib_number - 1] = person_id
    
    # Step 3: For each bib number i (from 1 to N), 
    # find the person wearing bib i, then find who they are staring at,
    # then get the bib number of that person.
    
    result = []
    for bib_num in range(1, N + 1):
        person_wearing_bib = bib_to_person[bib_num - 1]
        person_staring_at = P[person_wearing_bib - 1]
        bib_of_person_staring_at = person_to_bib[person_staring_at - 1]
        result.append(str(bib_of_person_staring_at))
    
    print(" ".join(result))

if __name__ == "__main__":
    solve()
