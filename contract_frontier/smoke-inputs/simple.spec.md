## Description
Provide a standalone Python program at `/workspace/solution.py` that reads two signed integers from standard input and prints their sum. The required result is the arithmetic sum of the two supplied values. Positive, negative, and zero values are within the stated input category.

## Preconditions
- **PRE-1 — Unverified:** Standard input supplies two signed integers.
- **PRE-2 — Unverified:** The program is invoked in an environment that can execute the required standalone Python file.

## Postconditions
- **POST-1 — Unverified:** A standalone Python program exists at `/workspace/solution.py`.
- **POST-2 — Unverified:** The program reads both supplied integers from standard input.
- **POST-3 — Unverified:** Standard output prints the arithmetic sum of those integers.
- **POST-4 — Unverified:** The sum requirement applies when either or both operands are negative, positive, or zero.
- **POST-5 — Unverified:** The prescribed verification command, `python -I /public/check.py`, has been run. This contract does not claim that execution has occurred or that checks have passed.

## Test suggestions
- For **PRE-1**, **POST-2**, and **POST-3**, supply two positive integers and compare the printed value with their expected sum.
- For **POST-3** and **POST-4**, suggest cases containing two negative values, operands with opposite signs, equal magnitudes with opposite signs, and zero operands.
- For **POST-1** and **PRE-2**, check that the specified file can be invoked as a standalone Python program.
- For **POST-5**, run the prescribed command and record its result.

## Unspecified behavior
Integer magnitude limits, exact input whitespace, extra input, malformed input, and exact output whitespace are not specified. No persistent state or behavior across separate invocations is specified.
