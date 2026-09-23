# Review 34: `primevul:original:413570` (c)

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
   1 | static void free_partial_reqs(gpointer value)
   2 | {
   3 | 	struct tcp_partial_client_data *data = value;
   4 | 
   5 | 	client_reset(data);
   6 | 	g_free(data);
   7 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `void` | 1:8 |
| 2 | `free_partial_reqs` | 1:13 |
| 4 | `gpointer` | 1:31 |
| 5 | `value` | 1:40 |
| 8 | `struct` | 3:2 |
| 9 | `tcp_partial_client_data` | 3:9 |
| 11 | `data` | 3:34 |
| 13 | `value` | 3:41 |
| 15 | `client_reset` | 5:2 |
| 17 | `data` | 5:15 |
| 20 | `g_free` | 6:2 |
| 22 | `data` | 6:9 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'void'` |
| 3 | `'free'` |
| 4 | `'_'` |
| 5 | `'partial'` |
| 6 | `'_'` |
| 7 | `'req'` |
| 8 | `'s'` |
| 9 | `'('` |
| 10 | `'g'` |
| 11 | `'pointer'` |
| 12 | `'value'` |
| 13 | `')'` |
| 14 | `'\n'` |
| 15 | `'{'` |
| 16 | `'\n'` |
| 17 | `'\t'` |
| 18 | `'struct'` |
| 19 | `'tcp'` |
| 20 | `'_'` |
| 21 | `'partial'` |
| 22 | `'_'` |
| 23 | `'client'` |
| 24 | `'_'` |
| 25 | `'data'` |
| 26 | `'*'` |
| 27 | `'data'` |
| 28 | `'='` |
| 29 | `'value'` |
| 30 | `';'` |
| 31 | `'\n\n'` |
| 32 | `'\t'` |
| 33 | `'client'` |
| 34 | `'_'` |
| 35 | `'reset'` |
| 36 | `'('` |
| 37 | `'data'` |
| 38 | `');'` |
| 39 | `'\n'` |
| 40 | `'\t'` |
| 41 | `'g'` |
| 42 | `'_'` |
| 43 | `'free'` |
| 44 | `'('` |
| 45 | `'data'` |
| 46 | `');'` |
| 47 | `'\n'` |
| 48 | `'}'` |
