import sys


def main():
    nums = iter(map(int, sys.stdin.buffer.read().split()))
    n, m = next(nums), next(nums)

    # Every terminal graph is complete bipartite. For odd n its edge
    # count is even, so all plays have the same parity of length.
    if n & 1:
        print("Aoki" if m & 1 else "Takahashi")
        return

    adj = [[] for _ in range(n)]
    for _ in range(m):
        u, v = next(nums) - 1, next(nums) - 1
        adj[u].append(v)
        adj[v].append(u)

    color = [-1] * n
    odd = large_odd = 0
    p = m & 1
    for root in range(n):
        if color[root] != -1:
            continue
        color[root] = 0
        stack = [root]
        a, b = 1, 0
        while stack:
            u = stack.pop()
            c = color[u] ^ 1
            for v in adj[u]:
                if color[v] == -1:
                    color[v] = c
                    stack.append(v)
                    if c:
                        b += 1
                    else:
                        a += 1
        if (a + b) & 1:
            odd += 1
            large_odd += a + b > 1
        else:
            p ^= a & 1

    if large_odd == 0:
        # Joining two singletons leaves p unchanged and lowers odd/2
        # by one. An internal or even-even move flips p instead.
        # Joining a singleton to an even component gives the opponent
        # a winning position with one nonsingleton odd component.
        win = p ^ ((odd // 2) & 1)
    elif large_odd <= 2:
        # Merge two odd components, including all nonsingleton ones.
        # Since at least one has both colors, either alignment works,
        # so we can choose p for the resulting zero-large-odd position.
        win = True
    else:
        # No move can leave zero large odd components. Moves into the
        # one/two-large-odd cases are losing moves. Within this case
        # each move flips the parity of m. If m is odd there is always
        # a move staying in this case: an internal or even-odd move
        # if available, otherwise all components are odd and complete,
        # which would imply m is even.
        win = m & 1

    print("Aoki" if win else "Takahashi")


if __name__ == "__main__":
    main()
