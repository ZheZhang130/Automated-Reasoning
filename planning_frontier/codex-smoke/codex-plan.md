## Observations

1. Edges are undirected, so every edge can be identified by its endpoints in sorted order.
2. Connectivity depends on whether an edge has at least one active copy, not on its exact positive multiplicity.
3. Because all operations can be read before answering, each edge’s periods of positive multiplicity can be represented as time intervals.
4. A segment tree over operation times can distribute each active interval among logarithmically many nodes.
5. During a traversal of that tree, a rollback disjoint-set union structure can maintain exactly the edges relevant to the current time.
6. Union by size without path compression gives logarithmic find operations and makes successful unions easy to undo.
7. Self-loops never change connectivity, and every vertex is always connected to itself.

## Solution sketch

1. **Normalize and record the operations.**

   > Edges are undirected, so every edge can be identified by its endpoints in sorted order.

   Read all Q operations and assign them times 0 through Q−1. For every edge update, replace its endpoints by their minimum and maximum. Thus an insertion written with reversed endpoints and its later removal use the same dictionary entry. Preserve query endpoints and their chronological positions.

2. **Build the active intervals.**

   > Connectivity depends on whether an edge has at least one active copy, not on its exact positive multiplicity.

   Maintain a multiplicity and an opening time for each normalized edge. An insertion changing the multiplicity from zero to one opens an interval at the current time. A removal changing it from one to zero closes that interval at the current time. Changes between positive counts do not open or close intervals. The promised valid removals ensure that counts never become negative.

3. **Finish intervals at the input boundary.**

   > Because all operations can be read before answering, each edge’s periods of positive multiplicity can be represented as time intervals.

   Use half-open intervals: an edge opened at time L and closed at time R is active on [L, R). After processing every operation, close all remaining open intervals at Q. This convention includes the insertion time and excludes the removal time. Neither time contains a query, so it also matches the required query semantics.

4. **Store intervals in a time segment tree.**

   > A segment tree over operation times can distribute each active interval among logarithmically many nodes.

   Build a segment tree covering [0, Q). Decompose each nonempty active interval into its canonical segment-tree nodes and append its edge to those nodes’ buckets. Store compact edge identifiers if useful for reducing Python memory usage. An edge appears exactly once along the root-to-leaf path for each time when it is active.

5. **Prepare reversible connectivity operations.**

   > Union by size without path compression gives logarithmic find operations and makes successful unions easy to undo.

   Initialize each vertex as its own component. Find roots by following parent pointers without modifying them. When merging different roots, attach the smaller component below the larger one and record the attached root, surviving root, and surviving root’s previous size. An attempted union within one component changes nothing and needs no history record.

6. **Traverse, answer, and roll back.**

   > During a traversal of that tree, a rollback disjoint-set union structure can maintain exactly the edges relevant to the current time.

   On entering a node, save the history length and apply its bucket’s unions. At a query leaf, answer YES exactly when both vertices have the same root. Visit leaves chronologically and collect answers in order. Before leaving each node, undo history records back to its saved length.

7. **Handle trivial cases and assess resources.**

   > Self-loops never change connectivity, and every vertex is always connected to itself.

   Self-loops may be omitted from interval storage entirely. Equal-endpoint queries always return YES. The method also handles isolated vertices, repeated insertion/removal cycles, no queries, and edges remaining active through the end. With K active intervals, time is O(Q + N + (K log Q + Q) log N), and space is O(N + Q + K log Q). Since K ≤ Q, these bounds meet the requested polylogarithmic amortized target.
