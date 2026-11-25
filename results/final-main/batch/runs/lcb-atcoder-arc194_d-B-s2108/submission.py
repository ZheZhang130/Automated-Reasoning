import sys

MOD = 998244353


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    n = int(data[0]) // 2
    s = data[1]

    fact = [1] * (n + 1)
    for i in range(1, n + 1):
        fact[i] = fact[i - 1] * i % MOD
    inv_fact = [1] * (n + 1)
    inv_fact[n] = pow(fact[n], MOD - 2, MOD)
    for i in range(n, 0, -1):
        inv_fact[i - 1] = inv_fact[i] * i % MOD

    # A closing parenthesis completes a node. Its sorted child types
    # identify its unordered rooted subtree.
    types = {}
    stack = [[]]
    answer = 1
    for c in s:
        if c == 40:
            stack.append([])
        else:
            children = stack.pop()
            children.sort()
            key = tuple(children)
            node_type = types.get(key)
            if node_type is None:
                node_type = len(types)
                types[key] = node_type
            stack[-1].append(node_type)

            # An interval reversal followed by individual mirrors lets us
            # swap neighboring children without changing their interiors.
            answer = answer * fact[len(children)] % MOD
            start = 0
            for end in range(1, len(children) + 1):
                if end == len(children) or children[end] != children[start]:
                    answer = answer * inv_fact[end - start] % MOD
                    start = end

    # Count permutations of the top-level trees as well.
    roots = stack[0]
    answer = answer * fact[len(roots)] % MOD
    counts = {}
    for t in roots:
        counts[t] = counts.get(t, 0) + 1
    for count in counts.values():
        answer = answer * inv_fact[count] % MOD

    print(answer)


if __name__ == "__main__":
    main()
