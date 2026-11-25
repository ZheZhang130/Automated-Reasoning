import sys

def solve():
    # Read input
    input_data = sys.stdin.read().split()
    N = int(input_data[0])
    M = int(input_data[1])
    S = input_data[2]
    
    MOD = 998244353
    
    # Convert S to 0..25
    S_int = [ord(c) - ord('a') for c in S]
    
    # State representation: we store the entire LCS row as a tuple
    # The row has N+1 entries: row[0]=0, row[1], ..., row[N]
    # We use a tuple of N+1 integers as the state key
    
    # Start with the initial row (all zeros)
    initial_row = tuple([0] * (N + 1))
    
    # We'll use a dictionary for sparse storage, but since N is small, we can use a list
    # Actually, let's use a dict mapping row tuple to list of 26 next rows
    from collections import defaultdict
    next_rows = defaultdict(list)
    
    # For each possible row, precompute transitions for each character
    # We'll do this iteratively as we go, but we need to handle all reachable states
    
    # Simpler approach: just compute on the fly and cache
    # But we need to know all states beforehand. Let's enumerate all possible rows.
    
    # A row is determined by its increments (differences between consecutive entries)
    # row[0] = 0
    # row[i] = row[i-1] + increment[i-1] for i=1..N
    # increment[i] is either 0 or 1 (since LCS length increases by at most 1)
    # So there are 2^N possible rows.
    
    # Let's enumerate all possible rows by their increment patterns
    num_states = 1 << N
    
    # Precompute transitions
    next_mask = [[0] * 26 for _ in range(num_states)]
    
    for state in range(num_states):
        # Decode state into increments
        # state bits: bit i corresponds to increment[i]
        increments = [(state >> i) & 1 for i in range(N)]
        
        # Build the row
        row = [0] * (N + 1)
        for i in range(N):
            row[i+1] = row[i] + increments[i]
        
        # For each character, compute the new row
        for char in range(26):
            # Standard LCS update: when adding character c,
            # new_row[i] = max(old_row[i], old_row[i-1] + 1) if S[i-1] == c else old_row[i]
            # But we need to be careful about the order of updates.
            # The standard DP update is done in place, but we need the old values.
            
            # Let's compute the new row from the old row
            new_row = list(row)  # Copy
            
            # For each position i from 0 to N-1:
            # If S[i] == char, we can potentially increase the LCS length
            # new_row[i+1] = max(old_row[i+1], old_row[i] + 1)
            # But we need to use the old row values, not the updated ones.
            
            # Actually, the standard update is:
            # dp[i][j] = max(dp[i][j-1], dp[i-1][j] + 1) if S[i-1] == c else dp[i][j-1]
            # where dp[i][j] is LCS of S[0:i] and T[0:j]
            # When we add c to T, we update dp[i][j] for all i.
            # dp[i][j] = max(dp[i][j-1], dp[i-1][j] + 1) if S[i-1] == c else dp[i][j-1]
            # But dp[i-1][j] is from the previous step (old row), and dp[i][j-1] is also from the previous step.
            
            # So for each i from 0 to N-1:
            #   if S[i] == char:
            #       new_row[i+1] = max(row[i+1], row[i] + 1)
            #   else:
            #       new_row[i+1] = row[i+1]
            
            for i in range(N):
                if S_int[i] == char:
                    new_row[i+1] = max(row[i+1], row[i] + 1)
            
            # Now compute the increments for the new row
            new_increments = [new_row[i+1] - new_row[i] for i in range(N)]
            
            # Encode new_increments into a state
            new_state = 0
            for i in range(N):
                if new_increments[i]:
                    new_state |= (1 << i)
            
            next_mask[state][char] = new_state
    
    # Now simulate M steps
    # dp[state] = number of strings of current length that have the given state
    dp = [0] * num_states
    dp[0] = 1  # empty string has state 0 (all zeros)
    
    for step in range(M):
        new_dp = [0] * num_states
        for state in range(num_states):
            if dp[state] == 0:
                continue
            count = dp[state]
            for char in range(26):
                next_state = next_mask[state][char]
                new_dp[next_state] = (new_dp[next_state] + count) % MOD
        dp = new_dp
    
    # Aggregate answers
    ans = [0] * (N + 1)
    for state in range(num_states):
        if dp[state] == 0:
            continue
        # Count set bits in state
        bits = bin(state).count('1')
        ans[bits] = (ans[bits] + dp[state]) % MOD
    
    # Print answers
    print(*(ans))

if __name__ == '__main__':
    solve()
