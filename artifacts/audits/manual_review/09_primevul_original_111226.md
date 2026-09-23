# Review 09: `primevul:original:111226` (cpp)

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
   1 | Document* ScreenOrientation::document() const
   2 | {
   3 |     if (!m_associatedDOMWindow || !m_associatedDOMWindow->isCurrentlyDisplayedInFrame())
   4 |         return 0;
   5 |     ASSERT(m_associatedDOMWindow->document());
   6 |     return m_associatedDOMWindow->document();
   7 | }
   8 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `Document` | 1:1 |
| 2 | `ScreenOrientation` | 1:11 |
| 4 | `document` | 1:30 |
| 7 | `const` | 1:41 |
| 9 | `if` | 3:5 |
| 12 | `m_associatedDOMWindow` | 3:10 |
| 15 | `m_associatedDOMWindow` | 3:36 |
| 17 | `isCurrentlyDisplayedInFrame` | 3:59 |
| 21 | `return` | 4:9 |
| 24 | `ASSERT` | 5:5 |
| 26 | `m_associatedDOMWindow` | 5:12 |
| 28 | `document` | 5:35 |
| 33 | `return` | 6:5 |
| 34 | `m_associatedDOMWindow` | 6:12 |
| 36 | `document` | 6:35 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'Document'` |
| 2 | `'*'` |
| 3 | `'Screen'` |
| 4 | `'O'` |
| 5 | `'rient'` |
| 6 | `'ation'` |
| 7 | `'::'` |
| 8 | `'document'` |
| 9 | `'()'` |
| 10 | `'const'` |
| 11 | `'\n'` |
| 12 | `'{'` |
| 13 | `'\n'` |
| 17 | `'if'` |
| 18 | `'(!'` |
| 19 | `'m'` |
| 20 | `'_'` |
| 21 | `'associated'` |
| 22 | `'DOM'` |
| 23 | `'Window'` |
| 24 | `'||'` |
| 25 | `'!'` |
| 26 | `'m'` |
| 27 | `'_'` |
| 28 | `'associated'` |
| 29 | `'DOM'` |
| 30 | `'Window'` |
| 31 | `'->'` |
| 32 | `'is'` |
| 33 | `'Currently'` |
| 34 | `'Display'` |
| 35 | `'edIn'` |
| 36 | `'Frame'` |
| 37 | `'())'` |
| 38 | `'\n'` |
| 46 | `'return'` |
| 47 | `'0'` |
| 48 | `';'` |
| 49 | `'\n'` |
| 53 | `'ASS'` |
| 54 | `'ERT'` |
| 55 | `'('` |
| 56 | `'m'` |
| 57 | `'_'` |
| 58 | `'associated'` |
| 59 | `'DOM'` |
| 60 | `'Window'` |
| 61 | `'->'` |
| 62 | `'document'` |
| 63 | `'());'` |
| 64 | `'\n'` |
| 68 | `'return'` |
| 69 | `'m'` |
| 70 | `'_'` |
| 71 | `'associated'` |
| 72 | `'DOM'` |
| 73 | `'Window'` |
| 74 | `'->'` |
| 75 | `'document'` |
| 76 | `'();'` |
| 77 | `'\n'` |
| 78 | `'}'` |
| 79 | `'\n'` |
