# Review 49: `primevul:original:218947` (cpp)

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
   1 |   explicit BinaryOp(OpKernelConstruction* ctx)
   2 |       : BinaryOpShared(ctx, DataTypeToEnum<Tout>::v(),
   3 |                        DataTypeToEnum<Tin>::v()) {}
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `explicit` | 1:3 |
| 1 | `BinaryOp` | 1:12 |
| 3 | `OpKernelConstruction` | 1:21 |
| 5 | `ctx` | 1:43 |
| 8 | `BinaryOpShared` | 2:9 |
| 10 | `ctx` | 2:24 |
| 12 | `DataTypeToEnum` | 2:29 |
| 14 | `Tout` | 2:44 |
| 17 | `v` | 2:51 |
| 21 | `DataTypeToEnum` | 3:24 |
| 23 | `Tin` | 3:39 |
| 26 | `v` | 3:45 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 2 | `'explicit'` |
| 3 | `'Binary'` |
| 4 | `'Op'` |
| 5 | `'('` |
| 6 | `'Op'` |
| 7 | `'K'` |
| 8 | `'ernel'` |
| 9 | `'Construction'` |
| 10 | `'*'` |
| 11 | `'c'` |
| 12 | `'tx'` |
| 13 | `')'` |
| 14 | `'\n'` |
| 20 | `':'` |
| 21 | `'Binary'` |
| 22 | `'Op'` |
| 23 | `'Sh'` |
| 24 | `'ared'` |
| 25 | `'('` |
| 26 | `'ctx'` |
| 27 | `','` |
| 28 | `'Data'` |
| 29 | `'Type'` |
| 30 | `'To'` |
| 31 | `'En'` |
| 32 | `'um'` |
| 33 | `'<'` |
| 34 | `'T'` |
| 35 | `'out'` |
| 36 | `'>'` |
| 37 | `'::'` |
| 38 | `'v'` |
| 39 | `'(),'` |
| 40 | `'\n'` |
| 63 | `'Data'` |
| 64 | `'Type'` |
| 65 | `'To'` |
| 66 | `'En'` |
| 67 | `'um'` |
| 68 | `'<'` |
| 69 | `'T'` |
| 70 | `'in'` |
| 71 | `'>'` |
| 72 | `'::'` |
| 73 | `'v'` |
| 74 | `'())'` |
| 75 | `'{}'` |
