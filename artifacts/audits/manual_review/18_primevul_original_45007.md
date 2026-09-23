# Review 18: `primevul:original:45007` (cpp)

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
   1 | xdr_gpol_arg(XDR *xdrs, gpol_arg *objp)
   2 | {
   3 | 	if (!xdr_ui_4(xdrs, &objp->api_version)) {
   4 | 		return (FALSE);
   5 | 	}
   6 | 	if (!xdr_nullstring(xdrs, &objp->name)) {
   7 | 		return (FALSE);
   8 | 	}
   9 | 	return (TRUE);
  10 | }
  11 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `xdr_gpol_arg` | 1:1 |
| 2 | `XDR` | 1:14 |
| 4 | `xdrs` | 1:19 |
| 6 | `gpol_arg` | 1:25 |
| 8 | `objp` | 1:35 |
| 11 | `if` | 3:2 |
| 14 | `xdr_ui_4` | 3:7 |
| 16 | `xdrs` | 3:16 |
| 19 | `objp` | 3:23 |
| 21 | `api_version` | 3:29 |
| 25 | `return` | 4:3 |
| 27 | `FALSE` | 4:11 |
| 31 | `if` | 6:2 |
| 34 | `xdr_nullstring` | 6:7 |
| 36 | `xdrs` | 6:22 |
| 39 | `objp` | 6:29 |
| 41 | `name` | 6:35 |
| 45 | `return` | 7:3 |
| 47 | `FALSE` | 7:11 |
| 51 | `return` | 9:2 |
| 53 | `TRUE` | 9:10 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'x'` |
| 2 | `'dr'` |
| 3 | `'_'` |
| 4 | `'g'` |
| 5 | `'pol'` |
| 6 | `'_'` |
| 7 | `'arg'` |
| 8 | `'('` |
| 9 | `'X'` |
| 10 | `'DR'` |
| 11 | `'*'` |
| 12 | `'xd'` |
| 13 | `'rs'` |
| 14 | `','` |
| 15 | `'g'` |
| 16 | `'pol'` |
| 17 | `'_'` |
| 18 | `'arg'` |
| 19 | `'*'` |
| 20 | `'obj'` |
| 21 | `'p'` |
| 22 | `')'` |
| 23 | `'\n'` |
| 24 | `'{'` |
| 25 | `'\n'` |
| 26 | `'\t'` |
| 27 | `'if'` |
| 28 | `'(!'` |
| 29 | `'x'` |
| 30 | `'dr'` |
| 31 | `'_'` |
| 32 | `'ui'` |
| 33 | `'_'` |
| 34 | `'4'` |
| 35 | `'('` |
| 36 | `'xd'` |
| 37 | `'rs'` |
| 38 | `','` |
| 39 | `'&'` |
| 40 | `'obj'` |
| 41 | `'p'` |
| 42 | `'->'` |
| 43 | `'api'` |
| 44 | `'_'` |
| 45 | `'version'` |
| 46 | `'))'` |
| 47 | `'{'` |
| 48 | `'\n'` |
| 49 | `'\t'` |
| 50 | `'\t'` |
| 51 | `'return'` |
| 52 | `'('` |
| 53 | `'F'` |
| 54 | `'ALSE'` |
| 55 | `');'` |
| 56 | `'\n'` |
| 57 | `'\t'` |
| 58 | `'}'` |
| 59 | `'\n'` |
| 60 | `'\t'` |
| 61 | `'if'` |
| 62 | `'(!'` |
| 63 | `'x'` |
| 64 | `'dr'` |
| 65 | `'_'` |
| 66 | `'null'` |
| 67 | `'string'` |
| 68 | `'('` |
| 69 | `'xd'` |
| 70 | `'rs'` |
| 71 | `','` |
| 72 | `'&'` |
| 73 | `'obj'` |
| 74 | `'p'` |
| 75 | `'->'` |
| 76 | `'name'` |
| 77 | `'))'` |
| 78 | `'{'` |
| 79 | `'\n'` |
| 80 | `'\t'` |
| 81 | `'\t'` |
| 82 | `'return'` |
| 83 | `'('` |
| 84 | `'F'` |
| 85 | `'ALSE'` |
| 86 | `');'` |
| 87 | `'\n'` |
| 88 | `'\t'` |
| 89 | `'}'` |
| 90 | `'\n'` |
| 91 | `'\t'` |
| 92 | `'return'` |
| 93 | `'('` |
| 94 | `'TR'` |
| 95 | `'UE'` |
| 96 | `');'` |
| 97 | `'\n'` |
| 98 | `'}'` |
| 99 | `'\n'` |
