## Description
Provide a standalone Python program at `/workspace/solution.py` that maintains an initially empty undirected multigraph on vertices `1..N`. It processes `Q` operations from standard input and reports connectivity for each query, preserving operation order.

## Preconditions
- **PRE-1 — Unverified:** Input supplies `N Q`, followed by `Q` operations, with `1 ≤ N ≤ 200000` and `1 ≤ Q ≤ 200000`.
- **PRE-2 — Unverified:** Operations have the stated forms `+ u v`, `- u v`, or `? u v`, with vertices in `1..N`.
- **PRE-3 — Unverified:** Each removal names an edge copy that exists at that point.

## Postconditions
- **POST-1 — Unverified:** The standalone program exists at `/workspace/solution.py`, reads standard input, and writes standard output.
- **POST-2 — Unverified:** Initially, the graph has all `N` vertices and no edges.
- **POST-3 — Unverified:** Insertion adds exactly one edge copy; removal deletes exactly one existing copy.
- **POST-4 — Unverified:** Edges are undirected, so reversed endpoints identify the same edge. Parallel edges and self-loops are supported.
- **POST-5 — Unverified:** Each query prints `YES` exactly when its vertices are connected in the current graph, and `NO` otherwise. Every vertex is connected to itself.
- **POST-6 — Unverified:** Answers appear in query order. Removing one parallel copy preserves connectivity when another remains.
- **POST-7 — Unverified:** Processing meets the stated aim of near-linear or polylogarithmic amortized performance.
- **POST-8 — Unverified:** `python -I /public/check.py` has been run; no execution or passing result is claimed here.

## Test suggestions
- For **POST-2** and **POST-5**, query distinct isolated vertices and a vertex against itself, including `N=1`.
- For **POST-3–POST-6**, suggest insertions, reversed-endpoint removals, parallel-copy removals, self-loops, and queries between updates.
- For **PRE-1** and **POST-7**, suggest workloads at the stated size limits.
- For **POST-1** and **POST-8**, check the artifact and record the prescribed command’s result.

## Unspecified behavior
Malformed input, out-of-range values, and nonexistent-edge removals are unspecified. Exact runtime thresholds, memory limits, and output whitespace beyond the required answers are unspecified.
