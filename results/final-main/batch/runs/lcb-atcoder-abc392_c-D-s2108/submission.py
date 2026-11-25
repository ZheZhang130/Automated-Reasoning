import sys

def main():
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
    
    # P[i] is the person that person (i+1) is staring at (1-indexed)
    # Q[i] is the bib number worn by person (i+1)
    # We need to find, for each bib number i (1 to N), who is wearing it,
    # then who that person is staring at, and finally what bib number that person is wearing.
    
    # Create a mapping from bib number to person index (0-indexed)
    bib_to_person = [0] * (N + 1)
    for person_idx, bib in enumerate(Q):
        bib_to_person[bib] = person_idx
    
    # For each bib number i from 1 to N:
    #   person_idx = bib_to_person[i]
    #   target_person_idx = P[person_idx] - 1 (convert to 0-indexed)
    #   target_bib = Q[target_person_idx]
    #   output target_bib
    
    results = []
    for bib in range(1, N + 1):
        person_idx = bib_to_person[bib]
        target_person_idx = P[person_idx] - 1  # Convert to 0-indexed
        target_bib = Q[target_person_idx]
        results.append(str(target_bib))
    
    print(" ".join(results))

if __name__ == "__main__":
    main()
