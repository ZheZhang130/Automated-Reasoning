import sys


def main():
    read = sys.stdin.buffer.readline
    n, m = map(int, read().split())
    if n % 2:
        # Every terminal graph is complete bipartite. For odd n its
        # two side sizes have opposite parity, so its edge count is even.
        print("Aoki" if m % 2 else "Takahashi")
        return

    adj = [[] for _ in range(n)]
    for _ in range(m):
        u, v = map(int, read().split())
        u -= 1
        v -= 1
        adj[u].append(v)
        adj[v].append(u)

    color = bytearray(n)
    odd = 0
    nontrivial_odd = 0
    side_parity = 0
    for start in range(n):
        if color[start]:
            continue
        color[start] = 1
        stack = [start]
        size = 0
        first_side = 0
        while stack:
            v = stack.pop()
            size += 1
            c = color[v]
            first_side += c == 1
            for u in adj[v]:
                if not color[u]:
                    color[u] = 3 - c
                    stack.append(u)
        odd += size % 2
        if size % 2 == 0:
            side_parity ^= first_side % 2
        elif size > 1:
            nontrivial_odd += 1

    if nontrivial_odd == 0:
        # The odd components are isolated vertices. Joining two of them
        # flips both the edge parity and the even-component side parity.
        # Joining one to an even component gives the opponent a winning
        # state with exactly one nontrivial odd component.
        win = (side_parity ^ (m % 2) ^ ((odd // 2) % 2))
    elif nontrivial_odd <= 2:
        # Merge all nontrivial odd components into a single even one
        # (using an isolated vertex if there is just one). Either
        # resulting side parity is possible, so choose a losing state.
        win = True
    else:
        # Merging odd components either leaves at least three nontrivial
        # odd components or gives the opponent an immediately winning case.
        # With at least six odd components there is a merge that leaves
        # at least three nontrivial ones. With four odd components and
        # odd m, a move not merging odd components must exist: otherwise
        # all components would be odd and complete bipartite, making m even.
        win = m % 2
    print("Aoki" if win else "Takahashi")


if __name__ == "__main__":
    main()
