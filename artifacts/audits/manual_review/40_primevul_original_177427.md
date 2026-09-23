# Review 40: `primevul:original:177427` (cpp)

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
   1 | void GraphicsContext::setMiterLimit(float limit)
   2 | {
   3 |     if (paintingDisabled())
   4 |         return;
   5 |     platformContext()->setMiterLimit(limit);
   6 | }
   7 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `void` | 1:1 |
| 1 | `GraphicsContext` | 1:6 |
| 3 | `setMiterLimit` | 1:23 |
| 5 | `float` | 1:37 |
| 6 | `limit` | 1:43 |
| 9 | `if` | 3:5 |
| 11 | `paintingDisabled` | 3:9 |
| 15 | `return` | 4:9 |
| 17 | `platformContext` | 5:5 |
| 21 | `setMiterLimit` | 5:24 |
| 23 | `limit` | 5:38 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'void'` |
| 2 | `'Graphics'` |
| 3 | `'Context'` |
| 4 | `'::'` |
| 5 | `'set'` |
| 6 | `'M'` |
| 7 | `'iter'` |
| 8 | `'Limit'` |
| 9 | `'('` |
| 10 | `'float'` |
| 11 | `'limit'` |
| 12 | `')'` |
| 13 | `'\n'` |
| 14 | `'{'` |
| 15 | `'\n'` |
| 19 | `'if'` |
| 20 | `'('` |
| 21 | `'pain'` |
| 22 | `'ting'` |
| 23 | `'Dis'` |
| 24 | `'abled'` |
| 25 | `'())'` |
| 26 | `'\n'` |
| 34 | `'return'` |
| 35 | `';'` |
| 36 | `'\n'` |
| 40 | `'platform'` |
| 41 | `'Context'` |
| 42 | `'()'` |
| 43 | `'->'` |
| 44 | `'set'` |
| 45 | `'M'` |
| 46 | `'iter'` |
| 47 | `'Limit'` |
| 48 | `'('` |
| 49 | `'limit'` |
| 50 | `');'` |
| 51 | `'\n'` |
| 52 | `'}'` |
| 53 | `'\n'` |
