import sys

MOD = 998244353


def main():
    n = int(sys.stdin.buffer.readline())
    s = sys.stdin.buffer.readline().strip()
    m = n // 2

    fact = [1] * (m + 1)
    for i in range(1, m + 1):
        fact[i] = fact[i - 1] * i % MOD
    inv_fact = [1] * (m + 1)
    inv_fact[m] = pow(fact[m], MOD - 2, MOD)
    for i in range(m, 0, -1):
        inv_fact[i - 1] = inv_fact[i] * i % MOD

    # A balanced substring consists of consecutive sibling subtrees.
    # Mirroring it preserves the unordered tree. Mirroring two adjacent
    # subtrees together and then each separately swaps the two, so all
    # sibling orders can be realized independently.
    types = {}
    answer = 1

    def finish(children):
        nonlocal answer
        children.sort()
        key = tuple(children)
        # Every occurrence contributes the number of distinct orders of
        # its child types, independently of orders inside those children.
        answer = answer * fact[len(key)] % MOD
        i = 0
        while i < len(key):
            j = i + 1
            while j < len(key) and key[j] == key[i]:
                j += 1
            answer = answer * inv_fact[j - i] % MOD
            i = j
        return types.setdefault(key, len(types))

    stack = [[]]  # Virtual root for the top-level sequence.
    for c in s:
        if c == 40:
            stack.append([])
        else:
            node_type = finish(stack.pop())
            stack[-1].append(node_type)
    finish(stack[0])
    print(answer)


if __name__ == "__main__":
    main()
