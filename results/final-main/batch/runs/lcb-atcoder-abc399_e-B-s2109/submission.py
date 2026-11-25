import sys


def main():
    data = sys.stdin.buffer.read().split()
    s, t = data[1], data[2]
    dest = [-1] * 26
    for a, b in zip(s, t):
        a -= 97
        b -= 97
        if dest[a] != -1 and dest[a] != b:
            print(-1)
            return
        dest[a] = b

    indegree = [0] * 26
    answer = 0
    for a, b in enumerate(dest):
        if b != -1:
            indegree[b] += 1
            if a != b:
                answer += 1

    if answer and all(indegree):
        print(-1)
        return

    seen = [-1] * 26
    for start in range(26):
        a = start
        while a != -1 and seen[a] == -1:
            seen[a] = start
            a = dest[a]
        if a == -1 or seen[a] != start or dest[a] == a:
            continue

        # An incoming edge from outside the cycle provides a place
        # to merge two groups with the same eventual destination.
        isolated = indegree[a] == 1
        b = dest[a]
        while b != a:
            isolated &= indegree[b] == 1
            b = dest[b]
        if isolated:
            answer += 1

    print(answer)


if __name__ == "__main__":
    main()
