# Review 43: `primevul:original:192428` (cpp)

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
   1 | _zip_dirent_needs_zip64(const zip_dirent_t *de, zip_flags_t flags)
   2 | {
   3 |     if (de->uncomp_size >= ZIP_UINT32_MAX || de->comp_size >= ZIP_UINT32_MAX
   4 | 	|| ((flags & ZIP_FL_CENTRAL) && de->offset >= ZIP_UINT32_MAX))
   5 | 	return true;
   6 | 
   7 |     return false;
   8 | }
   9 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `_zip_dirent_needs_zip64` | 1:1 |
| 2 | `const` | 1:25 |
| 3 | `zip_dirent_t` | 1:31 |
| 5 | `de` | 1:45 |
| 7 | `zip_flags_t` | 1:49 |
| 8 | `flags` | 1:61 |
| 11 | `if` | 3:5 |
| 13 | `de` | 3:9 |
| 15 | `uncomp_size` | 3:13 |
| 17 | `ZIP_UINT32_MAX` | 3:28 |
| 19 | `de` | 3:46 |
| 21 | `comp_size` | 3:50 |
| 23 | `ZIP_UINT32_MAX` | 3:63 |
| 27 | `flags` | 4:7 |
| 29 | `ZIP_FL_CENTRAL` | 4:15 |
| 32 | `de` | 4:34 |
| 34 | `offset` | 4:38 |
| 36 | `ZIP_UINT32_MAX` | 4:48 |
| 39 | `return` | 5:2 |
| 40 | `true` | 5:9 |
| 42 | `return` | 7:5 |
| 43 | `false` | 7:12 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'_'` |
| 2 | `'zip'` |
| 3 | `'_'` |
| 4 | `'d'` |
| 5 | `'ire'` |
| 6 | `'nt'` |
| 7 | `'_'` |
| 8 | `'needs'` |
| 9 | `'_'` |
| 10 | `'zip'` |
| 11 | `'64'` |
| 12 | `'('` |
| 13 | `'const'` |
| 14 | `'zip'` |
| 15 | `'_'` |
| 16 | `'d'` |
| 17 | `'ire'` |
| 18 | `'nt'` |
| 19 | `'_'` |
| 20 | `'t'` |
| 21 | `'*'` |
| 22 | `'de'` |
| 23 | `','` |
| 24 | `'zip'` |
| 25 | `'_'` |
| 26 | `'flags'` |
| 27 | `'_'` |
| 28 | `'t'` |
| 29 | `'flags'` |
| 30 | `')'` |
| 31 | `'\n'` |
| 32 | `'{'` |
| 33 | `'\n'` |
| 37 | `'if'` |
| 38 | `'('` |
| 39 | `'de'` |
| 40 | `'->'` |
| 41 | `'un'` |
| 42 | `'comp'` |
| 43 | `'_'` |
| 44 | `'size'` |
| 45 | `'>='` |
| 46 | `'ZIP'` |
| 47 | `'_'` |
| 48 | `'U'` |
| 49 | `'INT'` |
| 50 | `'32'` |
| 51 | `'_'` |
| 52 | `'MAX'` |
| 53 | `'||'` |
| 54 | `'de'` |
| 55 | `'->'` |
| 56 | `'comp'` |
| 57 | `'_'` |
| 58 | `'size'` |
| 59 | `'>='` |
| 60 | `'ZIP'` |
| 61 | `'_'` |
| 62 | `'U'` |
| 63 | `'INT'` |
| 64 | `'32'` |
| 65 | `'_'` |
| 66 | `'MAX'` |
| 67 | `'\n'` |
| 68 | `'\t'` |
| 69 | `'||'` |
| 70 | `'(('` |
| 71 | `'flags'` |
| 72 | `'&'` |
| 73 | `'ZIP'` |
| 74 | `'_'` |
| 75 | `'FL'` |
| 76 | `'_'` |
| 77 | `'CENT'` |
| 78 | `'RAL'` |
| 79 | `')'` |
| 80 | `'&&'` |
| 81 | `'de'` |
| 82 | `'->'` |
| 83 | `'offset'` |
| 84 | `'>='` |
| 85 | `'ZIP'` |
| 86 | `'_'` |
| 87 | `'U'` |
| 88 | `'INT'` |
| 89 | `'32'` |
| 90 | `'_'` |
| 91 | `'MAX'` |
| 92 | `'))'` |
| 93 | `'\n'` |
| 94 | `'\t'` |
| 95 | `'return'` |
| 96 | `'true'` |
| 97 | `';'` |
| 98 | `'\n\n'` |
| 102 | `'return'` |
| 103 | `'false'` |
| 104 | `';'` |
| 105 | `'\n'` |
| 106 | `'}'` |
| 107 | `'\n'` |
