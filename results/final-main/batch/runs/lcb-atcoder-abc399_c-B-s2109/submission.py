import sys


def main():
    read = sys.stdin.buffer.readline
    n, m = map(int, read().split())
    parent = [-1] * (n + 1)

    def find(x):
        while parent[x] >= 0:
            p = parent[x]
            if parent[p] >= 0:
                parent[x] = parent[p]
            x = parent[x]
        return x

    removed = 0
    for _ in range(m):
        u, v = map(int, read().split())
        a, b = find(u), find(v)
        if a == b:
            removed += 1
        else:
            if parent[a] > parent[b]:
                a, b = b, a
            parent[a] += parent[b]
            parent[b] = a

    print(removed)


if __name__ == "__main__":
    main()
