import sys

def solve():
    input_data = sys.stdin.read().split()
    N = int(input_data[0])
    M = int(input_data[1])
    S = input_data[2]
    T = input_data[3]

    # We have M operations, each replaces one character in S with a character from T.
    # We want to maximize the resulting number.
    #
    # Key insight: We can think of this as having a multiset of digits from T.
    # We want to place these digits into S to maximize the result.
    # We should place the largest digits from T into the positions where they give the most benefit.
    #
    # Greedy approach from left to right:
    # At each position in S, if we can improve it with an available digit from T, do it.
    # But we need to be careful: using a very large digit early might prevent us from
    # using it later where it could be even more beneficial? No, because all positions
    # are equally important from left to right.
    #
    # Actually, the correct greedy strategy:
    # Sort T in descending order.
    # For each position in S from left to right:
    #   If the current digit is less than the largest available digit in T,
    #   replace it with that largest digit.
    #   Otherwise, keep the current digit.
    #
    # But wait, we might run out of digits from T before processing all positions.
    # In that case, we keep the original digits.
    #
    # However, we can also choose to NOT use a digit from T at a position and instead
    # use a later digit. But since we want to maximize, we should always use the
    # largest available digit if it improves the current position.
    #
    # Let's implement this:
    S_list = list(S)
    sorted_T = sorted(T, reverse=True)
    t_idx = 0
    
    for i in range(N):
        if t_idx < M:
            best_digit = sorted_T[t_idx]
            if best_digit > S_list[i]:
                S_list[i] = best_digit
                t_idx += 1
            # else: keep current digit, move to next position
        else:
            break
    
    result = ''.join(S_list)
    print(result)

solve()
