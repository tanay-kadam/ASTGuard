# Review 27: `primevul:original:167579` (c)

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
   1 | static void timeout_func(unsigned long data)
   2 | {
   3 | 	struct aio_timeout *to = (struct aio_timeout *)data;
   4 | 
   5 | 	to->timed_out = 1;
   6 | 	wake_up_process(to->p);
   7 | }
   8 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `void` | 1:8 |
| 2 | `timeout_func` | 1:13 |
| 4 | `unsigned` | 1:26 |
| 5 | `long` | 1:35 |
| 6 | `data` | 1:40 |
| 9 | `struct` | 3:2 |
| 10 | `aio_timeout` | 3:9 |
| 12 | `to` | 3:22 |
| 15 | `struct` | 3:28 |
| 16 | `aio_timeout` | 3:35 |
| 19 | `data` | 3:49 |
| 21 | `to` | 5:2 |
| 23 | `timed_out` | 5:6 |
| 27 | `wake_up_process` | 6:2 |
| 29 | `to` | 6:18 |
| 31 | `p` | 6:22 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'void'` |
| 3 | `'timeout'` |
| 4 | `'_'` |
| 5 | `'func'` |
| 6 | `'('` |
| 7 | `'unsigned'` |
| 8 | `'long'` |
| 9 | `'data'` |
| 10 | `')'` |
| 11 | `'\n'` |
| 12 | `'{'` |
| 13 | `'\n'` |
| 14 | `'\t'` |
| 15 | `'struct'` |
| 16 | `'a'` |
| 17 | `'io'` |
| 18 | `'_'` |
| 19 | `'timeout'` |
| 20 | `'*'` |
| 21 | `'to'` |
| 22 | `'='` |
| 23 | `'('` |
| 24 | `'struct'` |
| 25 | `'a'` |
| 26 | `'io'` |
| 27 | `'_'` |
| 28 | `'timeout'` |
| 29 | `'*)'` |
| 30 | `'data'` |
| 31 | `';'` |
| 32 | `'\n\n'` |
| 33 | `'\t'` |
| 34 | `'to'` |
| 35 | `'->'` |
| 36 | `'tim'` |
| 37 | `'ed'` |
| 38 | `'_'` |
| 39 | `'out'` |
| 40 | `'='` |
| 41 | `'1'` |
| 42 | `';'` |
| 43 | `'\n'` |
| 44 | `'\t'` |
| 45 | `'wake'` |
| 46 | `'_'` |
| 47 | `'up'` |
| 48 | `'_'` |
| 49 | `'process'` |
| 50 | `'('` |
| 51 | `'to'` |
| 52 | `'->'` |
| 53 | `'p'` |
| 54 | `');'` |
| 55 | `'\n'` |
| 56 | `'}'` |
| 57 | `'\n'` |
