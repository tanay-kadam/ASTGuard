# Review 02: `primevul:original:176035` (cpp)

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
   1 | PropertyBag* ExtensionService::GetPropertyBag(const Extension* extension) {
   2 |   return &extension_runtime_data_[extension->id()].property_bag;
   3 | }
   4 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `PropertyBag` | 1:1 |
| 2 | `ExtensionService` | 1:14 |
| 4 | `GetPropertyBag` | 1:32 |
| 6 | `const` | 1:47 |
| 7 | `Extension` | 1:53 |
| 9 | `extension` | 1:64 |
| 12 | `return` | 2:3 |
| 14 | `extension_runtime_data_` | 2:11 |
| 16 | `extension` | 2:35 |
| 18 | `id` | 2:46 |
| 23 | `property_bag` | 2:52 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'Property'` |
| 2 | `'B'` |
| 3 | `'ag'` |
| 4 | `'*'` |
| 5 | `'Extension'` |
| 6 | `'Service'` |
| 7 | `'::'` |
| 8 | `'Get'` |
| 9 | `'Property'` |
| 10 | `'B'` |
| 11 | `'ag'` |
| 12 | `'('` |
| 13 | `'const'` |
| 14 | `'Extension'` |
| 15 | `'*'` |
| 16 | `'extension'` |
| 17 | `')'` |
| 18 | `'{'` |
| 19 | `'\n'` |
| 21 | `'return'` |
| 22 | `'&'` |
| 23 | `'ext'` |
| 24 | `'ension'` |
| 25 | `'_'` |
| 26 | `'runtime'` |
| 27 | `'_'` |
| 28 | `'data'` |
| 29 | `'_'` |
| 30 | `'['` |
| 31 | `'ext'` |
| 32 | `'ension'` |
| 33 | `'->'` |
| 34 | `'id'` |
| 35 | `'()'` |
| 36 | `'].'` |
| 37 | `'property'` |
| 38 | `'_'` |
| 39 | `'bag'` |
| 40 | `';'` |
| 41 | `'\n'` |
| 42 | `'}'` |
| 43 | `'\n'` |
