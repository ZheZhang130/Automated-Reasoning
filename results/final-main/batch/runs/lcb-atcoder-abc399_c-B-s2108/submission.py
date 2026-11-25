import sys


def main():
    readline = sys.stdin.buffer.readline
    n, m = map(int, readline().split())
    parent = [-1] * (n + 1)

    def find(v):
        while parent[v] >= 0:
            p = parent[v]
            if parent[p] >= 0:
                parent[v] = parent[p]
            v = p
        return v

    deleted = 0
    for _ in range(m):
        u, v = map(int, readline().split())
        a, b = find(u), find(v)
        if a == b:
            deleted += 1
        else:
            if parent[a] > parent[b]:
                a, b = b, a
            parent[a] += parent[b]
            parent[b] = a

    print(deleted)


if __name__ == "__main__":
    main()
