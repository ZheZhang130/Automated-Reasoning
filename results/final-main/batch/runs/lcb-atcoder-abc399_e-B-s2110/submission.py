import sys


def main():
    _, s, t = sys.stdin.buffer.read().split()
    dest = [-1] * 26
    for a, b in zip(s, t):
        a -= 97
        b -= 97
        if dest[a] != -1 and dest[a] != b:
            print(-1)
            return
        dest[a] = b

    answer = sum(b != -1 and a != b for a, b in enumerate(dest))
    indegree = [0] * 26
    for b in dest:
        if b != -1:
            indegree[b] += 1

    # If all letters are needed, the first effective operation would
    # irreversibly merge two groups.
    if answer and all(indegree):
        print(-1)
        return

    seen = [False] * 26
    for start in range(26):
        path = {}
        a = start
        while a != -1 and not seen[a]:
            seen[a] = True
            path[a] = len(path)
            a = dest[a]
        if a in path and len(path) - path[a] > 1:
            cycle_start = path[a]
            # An incoming edge lets its source double as temporary
            # storage: it and the cycle predecessor share a target.
            if all(indegree[v] == 1 for v, i in path.items() if i >= cycle_start):
                answer += 1

    print(answer)


if __name__ == "__main__":
    main()
