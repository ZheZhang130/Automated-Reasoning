import sys

def solve():
    input = sys.stdin.read
    data = input().split()
    
    N = int(data[0])
    P = [0] + [int(x) for x in data[1:N+1]]  # 1-indexed
    Q = [0] + [int(x) for x in data[N+1:2*N+1]]  # 1-indexed
    
    # For each bib number i (from 1 to N), find who is wearing it (person j where Q[j] == i)
    # Then find who person j is staring at (P[j])
    # Then find the bib number of that person (Q[P[j]])
    
    # We need to map bib number -> person number
    bib_to_person = [0] * (N + 1)
    for person in range(1, N + 1):
        bib_to_person[Q[person]] = person
    
    # For each bib number i from 1 to N:
    # person wearing bib i is bib_to_person[i]
    # they are staring at P[bib_to_person[i]]
    # the bib of that person is Q[P[bib_to_person[i]]]
    
    result = []
    for i in range(1, N + 1):
        person_wearing = bib_to_person[i]
        person_stared_at = P[person_wearing]
        bib_of_person_stared_at = Q[person_stared_at]
        result.append(str(bib_of_person_stared_at))
    
    print(" ".join(result))

if __name__ == "__main__":
    solve()
