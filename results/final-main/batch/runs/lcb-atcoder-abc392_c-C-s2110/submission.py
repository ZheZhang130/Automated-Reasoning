import sys

def solve():
    input = sys.stdin.read
    data = input().split()
    
    N = int(data[0])
    P = [int(x) for x in data[1:N+1]]  # P_1 to P_N
    Q = [int(x) for x in data[N+1:2*N+1]]  # Q_1 to Q_N
    
    # P and Q are 1-indexed in the problem, but we'll use 0-indexed lists
    # P[i] is the person that person (i+1) is staring at
    # Q[i] is the bib number worn by person (i+1)
    
    # We need to find for each bib number i (from 1 to N):
    # Who is wearing bib i? Let's say person j is wearing bib i.
    # Then we need to find who person j is staring at, say person k.
    # Then the bib number worn by person k is the answer for bib i.
    
    # Let's create a mapping from bib number to person number
    # bib_to_person[bib_number] = person_number
    bib_to_person = [0] * (N + 1)
    for i in range(N):
        bib_to_person[Q[i]] = i + 1  # Person (i+1) wears bib Q[i]
    
    # Now for each bib number i from 1 to N:
    # Find the person wearing bib i: person = bib_to_person[i]
    # Find who that person is staring at: target_person = P[person - 1]
    # Find the bib number worn by target_person: answer = Q[target_person - 1]
    
    result = []
    for bib_num in range(1, N + 1):
        person_wearing_bib = bib_to_person[bib_num]
        person_staring_at = P[person_wearing_bib - 1]
        bib_of_person_staring_at = Q[person_staring_at - 1]
        result.append(str(bib_of_person_staring_at))
    
    print(" ".join(result))

if __name__ == "__main__":
    solve()
