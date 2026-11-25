import sys

def solve():
    input_data = sys.stdin.read().split()
    N = int(input_data[0])
    M = int(input_data[1])
    S = input_data[2]
    
    MOD = 998244353
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    
    # The state needs to encode the full LCS row
    # row[i] = LCS length between target prefix and S[0:i+1]
    # When we append a character c:
    #   new_row[i] = row[i-1] + 1 if c == S[i] else max(row[i], row[i-1])
    # 
    # The key insight: row[i] - row[i-1] is either 0 or 1.
    # So the state can be represented by a bitmask where bit i is set iff row[i] > row[i-1].
    # But we also need to know the actual values of row[i].
    # 
    # Actually, row[i] = number of set bits in state[0:i+1] (prefix of state bits)
    # So the state is fully determined by which positions have row[i] > row[i-1].
    
    num_states = 1 << N
    transitions = [[0] * num_states for _ in range(26)]
    
    for char_idx, char in enumerate(alphabet):
        for state in range(num_states):
            # Decode state to row
            row = [0] * N
            current = 0
            for i in range(N):
                if state & (1 << i):
                    current += 1
                row[i] = current
            
            # Compute new row after appending char
            new_row = [0] * N
            for i in range(N):
                if char == S[i]:
                    new_row[i] = row[i-1] + 1 if i > 0 else 1
                else:
                    new_row[i] = max(row[i], row[i-1] if i > 0 else 0)
            
            # Encode new_row back to state
            new_state = 0
            for i in range(N):
                if new_row[i] > 0:
                    new_state |= (1 << i)
            
            transitions[char_idx][state] = new_state
    
    count = [0] * num_states
    count[0] = 1
    
    for _ in range(M):
        new_count = [0] * num_states
        for char_idx in range(26):
            for state in range(num_states):
                if count[state] > 0:
                    next_state = transitions[char_idx][state]
                    new_count[next_state] = (new_count[next_state] + count[state]) % MOD
        count = new_count
    
    ans = [0] * (N + 1)
    for state in range(num_states):
        if count[state] > 0:
            k = bin(state).count('1')
            ans[k] = (ans[k] + count[state]) % MOD
    
    print(' '.join(map(str, ans)))

if __name__ == "__main__":
    solve()
