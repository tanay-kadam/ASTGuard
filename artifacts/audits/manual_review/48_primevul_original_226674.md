# Review 48: `primevul:original:226674` (cpp)

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
   1 | AP4_DcfdAtom::WriteFields(AP4_ByteStream& stream)
   2 | {
   3 |     stream.WriteUI32(m_Duration);
   4 |     return AP4_SUCCESS;
   5 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `AP4_DcfdAtom` | 1:1 |
| 2 | `WriteFields` | 1:15 |
| 4 | `AP4_ByteStream` | 1:27 |
| 6 | `stream` | 1:43 |
| 9 | `stream` | 3:5 |
| 11 | `WriteUI32` | 3:12 |
| 13 | `m_Duration` | 3:22 |
| 16 | `return` | 4:5 |
| 17 | `AP4_SUCCESS` | 4:12 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'AP'` |
| 2 | `'4'` |
| 3 | `'_'` |
| 4 | `'D'` |
| 5 | `'cf'` |
| 6 | `'d'` |
| 7 | `'At'` |
| 8 | `'om'` |
| 9 | `'::'` |
| 10 | `'Write'` |
| 11 | `'Field'` |
| 12 | `'s'` |
| 13 | `'('` |
| 14 | `'AP'` |
| 15 | `'4'` |
| 16 | `'_'` |
| 17 | `'Byte'` |
| 18 | `'Stream'` |
| 19 | `'&'` |
| 20 | `'stream'` |
| 21 | `')'` |
| 22 | `'\n'` |
| 23 | `'{'` |
| 24 | `'\n'` |
| 28 | `'stream'` |
| 29 | `'.'` |
| 30 | `'Write'` |
| 31 | `'UI'` |
| 32 | `'32'` |
| 33 | `'('` |
| 34 | `'m'` |
| 35 | `'_'` |
| 36 | `'Duration'` |
| 37 | `');'` |
| 38 | `'\n'` |
| 42 | `'return'` |
| 43 | `'AP'` |
| 44 | `'4'` |
| 45 | `'_'` |
| 46 | `'SU'` |
| 47 | `'CC'` |
| 48 | `'ESS'` |
| 49 | `';'` |
| 50 | `'\n'` |
| 51 | `'}'` |
