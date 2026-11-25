import sys


def main():
    _, s, t = sys.stdin.buffer.read().split()
    dest = [-1] * 26
    for x, y in zip(s, t):
        x -= 97
        y -= 97
        if dest[x] != -1 and dest[x] != y:
            print(-1)
            return
        dest[x] = y

    indegree = [0] * 26
    moves = 0
    for x, y in enumerate(dest):
        if y != -1:
            indegree[y] += 1
            moves += x != y

    if moves and all(indegree):
        print(-1)
        return

    # Every nontrivial cycle needs one extra move unless an incoming
    # branch supplies a letter with which a cycle letter can merge.
    seen = [-1] * 26
    for start in range(26):
        x = start
        while x != -1 and seen[x] == -1:
            seen[x] = start
            x = dest[x]
        if x == -1 or seen[x] != start or dest[x] == x:
            continue

        pure = indegree[x] == 1
        y = dest[x]
        while y != x:
            pure &= indegree[y] == 1
            y = dest[y]
        moves += pure

    print(moves)


if __name__ == "__main__":
    main()
