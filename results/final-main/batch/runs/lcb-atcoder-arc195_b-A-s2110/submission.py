import sys

def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    it = iter(data)
    N = int(next(it))
    A = [int(next(it)) for _ in range(N)]
    B = [int(next(it)) for _ in range(N)]

    # Find all S values that are required by positions where both A[i] and B[i] are fixed
    required_S = set()
    for a, b in zip(A, B):
        if a != -1 and b != -1:
            required_S.add(a + b)

    if required_S:
        S_candidates = sorted(required_S)
    else:
        # No fixed positions constrain S.
        # We need to pick an S such that for every position:
        #   If A[i] != -1, then S - A[i] >= 0 (if B[i] == -1)
        #   If B[i] != -1, then S - B[i] >= 0 (if A[i] == -1)
        #   If both are -1, no constraint on S from this position.
        # So S must be >= max of all fixed A[i] and all fixed B[i].
        fixed_vals = [x for x in A if x != -1] + [x for x in B if x != -1]
        if fixed_vals:
            min_S = max(fixed_vals)
        else:
            min_S = 0
        S_candidates = [min_S]

    for S in S_candidates:
        valid = True
        for a, b in zip(A, B):
            if a != -1 and b != -1:
                if a + b != S:
                    valid = False
                    break
            elif a != -1:
                # B is -1, need S - a >= 0
                if S - a < 0:
                    valid = False
                    break
            elif b != -1:
                # A is -1, need S - b >= 0
                if S - b < 0:
                    valid = False
                    break
        if valid:
            print("Yes")
            return

    print("No")

if __name__ == "__main__":
    solve()
