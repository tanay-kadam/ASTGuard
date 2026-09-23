# Review 39: `primevul:original:382519` (c)

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
   1 | static void save_same_name_hfinfo(gpointer data)
   2 | {
   3 | 	same_name_hfinfo = (header_field_info*)data;
   4 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `void` | 1:8 |
| 2 | `save_same_name_hfinfo` | 1:13 |
| 4 | `gpointer` | 1:35 |
| 5 | `data` | 1:44 |
| 8 | `same_name_hfinfo` | 3:2 |
| 11 | `header_field_info` | 3:22 |
| 14 | `data` | 3:41 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'void'` |
| 3 | `'save'` |
| 4 | `'_'` |
| 5 | `'same'` |
| 6 | `'_'` |
| 7 | `'name'` |
| 8 | `'_'` |
| 9 | `'h'` |
| 10 | `'f'` |
| 11 | `'info'` |
| 12 | `'('` |
| 13 | `'g'` |
| 14 | `'pointer'` |
| 15 | `'data'` |
| 16 | `')'` |
| 17 | `'\n'` |
| 18 | `'{'` |
| 19 | `'\n'` |
| 20 | `'\t'` |
| 21 | `'same'` |
| 22 | `'_'` |
| 23 | `'name'` |
| 24 | `'_'` |
| 25 | `'h'` |
| 26 | `'f'` |
| 27 | `'info'` |
| 28 | `'='` |
| 29 | `'('` |
| 30 | `'header'` |
| 31 | `'_'` |
| 32 | `'field'` |
| 33 | `'_'` |
| 34 | `'info'` |
| 35 | `'*)'` |
| 36 | `'data'` |
| 37 | `';'` |
| 38 | `'\n'` |
| 39 | `'}'` |
