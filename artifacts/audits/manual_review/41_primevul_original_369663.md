# Review 41: `primevul:original:369663` (cpp)

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
   1 | set_num_723(unsigned char *p, uint16_t value)
   2 | {
   3 | 	archive_le16enc(p, value);
   4 | 	archive_be16enc(p+2, value);
   5 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `set_num_723` | 1:1 |
| 2 | `unsigned` | 1:13 |
| 3 | `char` | 1:22 |
| 5 | `p` | 1:28 |
| 7 | `uint16_t` | 1:31 |
| 8 | `value` | 1:40 |
| 11 | `archive_le16enc` | 3:2 |
| 13 | `p` | 3:18 |
| 15 | `value` | 3:21 |
| 18 | `archive_be16enc` | 4:2 |
| 20 | `p` | 4:18 |
| 24 | `value` | 4:23 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'set'` |
| 2 | `'_'` |
| 3 | `'num'` |
| 4 | `'_'` |
| 5 | `'7'` |
| 6 | `'23'` |
| 7 | `'('` |
| 8 | `'unsigned'` |
| 9 | `'char'` |
| 10 | `'*'` |
| 11 | `'p'` |
| 12 | `','` |
| 13 | `'uint'` |
| 14 | `'16'` |
| 15 | `'_'` |
| 16 | `'t'` |
| 17 | `'value'` |
| 18 | `')'` |
| 19 | `'\n'` |
| 20 | `'{'` |
| 21 | `'\n'` |
| 22 | `'\t'` |
| 23 | `'archive'` |
| 24 | `'_'` |
| 25 | `'le'` |
| 26 | `'16'` |
| 27 | `'enc'` |
| 28 | `'('` |
| 29 | `'p'` |
| 30 | `','` |
| 31 | `'value'` |
| 32 | `');'` |
| 33 | `'\n'` |
| 34 | `'\t'` |
| 35 | `'archive'` |
| 36 | `'_'` |
| 37 | `'be'` |
| 38 | `'16'` |
| 39 | `'enc'` |
| 40 | `'('` |
| 41 | `'p'` |
| 42 | `'+'` |
| 43 | `'2'` |
| 44 | `','` |
| 45 | `'value'` |
| 46 | `');'` |
| 47 | `'\n'` |
| 48 | `'}'` |
