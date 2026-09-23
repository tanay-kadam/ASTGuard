# Review 45: `primevul:original:504560` (cpp)

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

```cpp
   1 | discrete_component_transfer_func (gint C, RsvgNodeComponentTransferFunc * user_data)
   2 | {
   3 |     gint k;
   4 | 
   5 |     if (!user_data->nbTableValues)
   6 |         return C;
   7 | 
   8 |     k = (C * user_data->nbTableValues) / 255;
   9 | 
  10 |     return user_data->tableValues[CLAMP (k, 0, user_data->nbTableValues - 1)];
  11 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `discrete_component_transfer_func` | 1:1 |
| 2 | `gint` | 1:35 |
| 3 | `C` | 1:40 |
| 5 | `RsvgNodeComponentTransferFunc` | 1:43 |
| 7 | `user_data` | 1:75 |
| 10 | `gint` | 3:5 |
| 11 | `k` | 3:10 |
| 13 | `if` | 5:5 |
| 16 | `user_data` | 5:10 |
| 18 | `nbTableValues` | 5:21 |
| 20 | `return` | 6:9 |
| 21 | `C` | 6:16 |
| 23 | `k` | 8:5 |
| 26 | `C` | 8:10 |
| 28 | `user_data` | 8:14 |
| 30 | `nbTableValues` | 8:25 |
| 35 | `return` | 10:5 |
| 36 | `user_data` | 10:12 |
| 38 | `tableValues` | 10:23 |
| 40 | `CLAMP` | 10:35 |
| 42 | `k` | 10:42 |
| 46 | `user_data` | 10:48 |
| 48 | `nbTableValues` | 10:59 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'disc'` |
| 2 | `'rete'` |
| 3 | `'_'` |
| 4 | `'component'` |
| 5 | `'_'` |
| 6 | `'transfer'` |
| 7 | `'_'` |
| 8 | `'func'` |
| 9 | `'('` |
| 10 | `'g'` |
| 11 | `'int'` |
| 12 | `'C'` |
| 13 | `','` |
| 14 | `'Rs'` |
| 15 | `'vg'` |
| 16 | `'Node'` |
| 17 | `'Component'` |
| 18 | `'Transfer'` |
| 19 | `'F'` |
| 20 | `'unc'` |
| 21 | `'*'` |
| 22 | `'user'` |
| 23 | `'_'` |
| 24 | `'data'` |
| 25 | `')'` |
| 26 | `'\n'` |
| 27 | `'{'` |
| 28 | `'\n'` |
| 32 | `'g'` |
| 33 | `'int'` |
| 34 | `'k'` |
| 35 | `';'` |
| 36 | `'\n\n'` |
| 40 | `'if'` |
| 41 | `'(!'` |
| 42 | `'user'` |
| 43 | `'_'` |
| 44 | `'data'` |
| 45 | `'->'` |
| 46 | `'nb'` |
| 47 | `'Table'` |
| 48 | `'Values'` |
| 49 | `')'` |
| 50 | `'\n'` |
| 58 | `'return'` |
| 59 | `'C'` |
| 60 | `';'` |
| 61 | `'\n\n'` |
| 65 | `'k'` |
| 66 | `'='` |
| 67 | `'('` |
| 68 | `'C'` |
| 69 | `'*'` |
| 70 | `'user'` |
| 71 | `'_'` |
| 72 | `'data'` |
| 73 | `'->'` |
| 74 | `'nb'` |
| 75 | `'Table'` |
| 76 | `'Values'` |
| 77 | `')'` |
| 78 | `'/'` |
| 79 | `'255'` |
| 80 | `';'` |
| 81 | `'\n\n'` |
| 85 | `'return'` |
| 86 | `'user'` |
| 87 | `'_'` |
| 88 | `'data'` |
| 89 | `'->'` |
| 90 | `'table'` |
| 91 | `'Values'` |
| 92 | `'['` |
| 93 | `'CL'` |
| 94 | `'AMP'` |
| 95 | `'('` |
| 96 | `'k'` |
| 97 | `','` |
| 98 | `'0'` |
| 99 | `','` |
| 100 | `'user'` |
| 101 | `'_'` |
| 102 | `'data'` |
| 103 | `'->'` |
| 104 | `'nb'` |
| 105 | `'Table'` |
| 106 | `'Values'` |
| 107 | `'-'` |
| 108 | `'1'` |
| 109 | `')'` |
| 110 | `'];'` |
| 111 | `'\n'` |
| 112 | `'}'` |
