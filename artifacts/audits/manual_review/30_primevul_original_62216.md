# Review 30: `primevul:original:62216` (c)

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
   1 | static int mailimf_greater_parse(const char * message, size_t length,
   2 | 				      size_t * indx)
   3 | {
   4 |   return mailimf_unstrict_char_parse(message, length, indx, '>');
   5 | }
   6 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `int` | 1:8 |
| 2 | `mailimf_greater_parse` | 1:12 |
| 4 | `const` | 1:34 |
| 5 | `char` | 1:40 |
| 7 | `message` | 1:47 |
| 9 | `size_t` | 1:56 |
| 10 | `length` | 1:63 |
| 12 | `size_t` | 2:11 |
| 14 | `indx` | 2:20 |
| 17 | `return` | 4:3 |
| 18 | `mailimf_unstrict_char_parse` | 4:10 |
| 20 | `message` | 4:38 |
| 22 | `length` | 4:47 |
| 24 | `indx` | 4:55 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'int'` |
| 3 | `'mail'` |
| 4 | `'im'` |
| 5 | `'f'` |
| 6 | `'_'` |
| 7 | `'great'` |
| 8 | `'er'` |
| 9 | `'_'` |
| 10 | `'parse'` |
| 11 | `'('` |
| 12 | `'const'` |
| 13 | `'char'` |
| 14 | `'*'` |
| 15 | `'message'` |
| 16 | `','` |
| 17 | `'size'` |
| 18 | `'_'` |
| 19 | `'t'` |
| 20 | `'length'` |
| 21 | `','` |
| 22 | `'\n'` |
| 23 | `'\t'` |
| 24 | `'\t'` |
| 25 | `'\t'` |
| 26 | `'\t'` |
| 32 | `'size'` |
| 33 | `'_'` |
| 34 | `'t'` |
| 35 | `'*'` |
| 36 | `'ind'` |
| 37 | `'x'` |
| 38 | `')'` |
| 39 | `'\n'` |
| 40 | `'{'` |
| 41 | `'\n'` |
| 43 | `'return'` |
| 44 | `'mail'` |
| 45 | `'im'` |
| 46 | `'f'` |
| 47 | `'_'` |
| 48 | `'un'` |
| 49 | `'st'` |
| 50 | `'rict'` |
| 51 | `'_'` |
| 52 | `'char'` |
| 53 | `'_'` |
| 54 | `'parse'` |
| 55 | `'('` |
| 56 | `'message'` |
| 57 | `','` |
| 58 | `'length'` |
| 59 | `','` |
| 60 | `'ind'` |
| 61 | `'x'` |
| 62 | `','` |
| 63 | `"'"` |
| 64 | `'>'` |
| 65 | `"');"` |
| 66 | `'\n'` |
| 67 | `'}'` |
| 68 | `'\n'` |
