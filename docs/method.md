# Method

The binding mathematical definitions are Sections 6-7 of
`IMPLEMENTATION_SPEC.md`. Code locations are indexed by `EQUATION_CODE_MAP.md`.
The model adds signed, soft AST/DFG biases to ordinary attention logits at
layers 2, 5, 8, and 11; it never hard-masks nonedges.

