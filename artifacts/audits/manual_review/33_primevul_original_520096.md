# Review 33: `primevul:original:520096` (c)

Author edges from the source alone. Do not open the pack file or any extractor output.

Record directed scalar dependencies as `[consumer_id, source_id]` using the identifier token ids below.

- A read `u` of a local scalar or parameter links `[u, d]` to every definition `d` of that binding that can reach it
  (declaration with initializer, assignment, `++`/`--`, compound assignment, or the parameter declarator).
- A new assignment/definition occurrence `d_new` links `[d_new, r]` to every scalar read `r` in its right-hand side.
  Compound assignment and increment read the old value before writing, so `i++` or `i += n` inside a loop
  can give a self-edge `[k, k]` (the read at token `k` reached by the write at `k` from the previous iteration).
- Pointer, array, and member expressions contribute only their scalar base/index reads; do not add memory or alias edges.
- Calls contribute only scalar argument reads; no callee effects or return provenance.
- Type names, function names, member selectors, and unknown globals have no bindings or edges.
  Keywords such as `return` appear in the token table because the lexer tags them as identifiers; they never have edges.
- Branches, loops, `break`, `continue`, and `return` follow normal control flow; loop back edges can carry definitions.

## Source

```c
   1 | void  Jsi_Free(void *n) { Assert(n); free(n); }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `void` | 1:1 |
| 1 | `Jsi_Free` | 1:7 |
| 3 | `void` | 1:16 |
| 5 | `n` | 1:22 |
| 8 | `Assert` | 1:27 |
| 10 | `n` | 1:34 |
| 13 | `free` | 1:38 |
| 15 | `n` | 1:43 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'void'` |
| 3 | `'J'` |
| 4 | `'si'` |
| 5 | `'_'` |
| 6 | `'Free'` |
| 7 | `'('` |
| 8 | `'void'` |
| 9 | `'*'` |
| 10 | `'n'` |
| 11 | `')'` |
| 12 | `'{'` |
| 13 | `'Ass'` |
| 14 | `'ert'` |
| 15 | `'('` |
| 16 | `'n'` |
| 17 | `');'` |
| 18 | `'free'` |
| 19 | `'('` |
| 20 | `'n'` |
| 21 | `');'` |
| 22 | `'}'` |
