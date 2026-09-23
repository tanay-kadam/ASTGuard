# Review 29: `primevul:original:83790` (c)

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
   1 | static int first_hi_bfreg(struct mlx5_ib_dev *dev,
   2 | 			  struct mlx5_bfreg_info *bfregi)
   3 | {
   4 | 	int med;
   5 | 
   6 | 	med = num_med_bfreg(dev, bfregi);
   7 | 	return ++med;
   8 | }
   9 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `int` | 1:8 |
| 2 | `first_hi_bfreg` | 1:12 |
| 4 | `struct` | 1:27 |
| 5 | `mlx5_ib_dev` | 1:34 |
| 7 | `dev` | 1:47 |
| 9 | `struct` | 2:6 |
| 10 | `mlx5_bfreg_info` | 2:13 |
| 12 | `bfregi` | 2:30 |
| 15 | `int` | 4:2 |
| 16 | `med` | 4:6 |
| 18 | `med` | 6:2 |
| 20 | `num_med_bfreg` | 6:8 |
| 22 | `dev` | 6:22 |
| 24 | `bfregi` | 6:27 |
| 27 | `return` | 7:2 |
| 29 | `med` | 7:11 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'int'` |
| 3 | `'first'` |
| 4 | `'_'` |
| 5 | `'hi'` |
| 6 | `'_'` |
| 7 | `'bf'` |
| 8 | `'reg'` |
| 9 | `'('` |
| 10 | `'struct'` |
| 11 | `'ml'` |
| 12 | `'x'` |
| 13 | `'5'` |
| 14 | `'_'` |
| 15 | `'ib'` |
| 16 | `'_'` |
| 17 | `'dev'` |
| 18 | `'*'` |
| 19 | `'dev'` |
| 20 | `','` |
| 21 | `'\n'` |
| 22 | `'\t'` |
| 23 | `'\t'` |
| 24 | `'\t'` |
| 26 | `'struct'` |
| 27 | `'ml'` |
| 28 | `'x'` |
| 29 | `'5'` |
| 30 | `'_'` |
| 31 | `'bf'` |
| 32 | `'reg'` |
| 33 | `'_'` |
| 34 | `'info'` |
| 35 | `'*'` |
| 36 | `'bf'` |
| 37 | `'reg'` |
| 38 | `'i'` |
| 39 | `')'` |
| 40 | `'\n'` |
| 41 | `'{'` |
| 42 | `'\n'` |
| 43 | `'\t'` |
| 44 | `'int'` |
| 45 | `'med'` |
| 46 | `';'` |
| 47 | `'\n\n'` |
| 48 | `'\t'` |
| 49 | `'med'` |
| 50 | `'='` |
| 51 | `'num'` |
| 52 | `'_'` |
| 53 | `'med'` |
| 54 | `'_'` |
| 55 | `'bf'` |
| 56 | `'reg'` |
| 57 | `'('` |
| 58 | `'dev'` |
| 59 | `','` |
| 60 | `'b'` |
| 61 | `'f'` |
| 62 | `'reg'` |
| 63 | `'i'` |
| 64 | `');'` |
| 65 | `'\n'` |
| 66 | `'\t'` |
| 67 | `'return'` |
| 68 | `'++'` |
| 69 | `'med'` |
| 70 | `';'` |
| 71 | `'\n'` |
| 72 | `'}'` |
| 73 | `'\n'` |
