# Review 26: `primevul:original:272745` (c)

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
   1 | bool is_hugetlb_entry_migration(pte_t pte)
   2 | {
   3 | 	swp_entry_t swp;
   4 | 
   5 | 	if (huge_pte_none(pte) || pte_present(pte))
   6 | 		return false;
   7 | 	swp = pte_to_swp_entry(pte);
   8 | 	if (is_migration_entry(swp))
   9 | 		return true;
  10 | 	else
  11 | 		return false;
  12 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `bool` | 1:1 |
| 1 | `is_hugetlb_entry_migration` | 1:6 |
| 3 | `pte_t` | 1:33 |
| 4 | `pte` | 1:39 |
| 7 | `swp_entry_t` | 3:2 |
| 8 | `swp` | 3:14 |
| 10 | `if` | 5:2 |
| 12 | `huge_pte_none` | 5:6 |
| 14 | `pte` | 5:20 |
| 17 | `pte_present` | 5:28 |
| 19 | `pte` | 5:40 |
| 22 | `return` | 6:3 |
| 23 | `false` | 6:10 |
| 25 | `swp` | 7:2 |
| 27 | `pte_to_swp_entry` | 7:8 |
| 29 | `pte` | 7:25 |
| 32 | `if` | 8:2 |
| 34 | `is_migration_entry` | 8:6 |
| 36 | `swp` | 8:25 |
| 39 | `return` | 9:3 |
| 40 | `true` | 9:10 |
| 42 | `else` | 10:2 |
| 43 | `return` | 11:3 |
| 44 | `false` | 11:10 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'bool'` |
| 2 | `'is'` |
| 3 | `'_'` |
| 4 | `'h'` |
| 5 | `'ug'` |
| 6 | `'et'` |
| 7 | `'lb'` |
| 8 | `'_'` |
| 9 | `'entry'` |
| 10 | `'_'` |
| 11 | `'m'` |
| 12 | `'igration'` |
| 13 | `'('` |
| 14 | `'pt'` |
| 15 | `'e'` |
| 16 | `'_'` |
| 17 | `'t'` |
| 18 | `'p'` |
| 19 | `'te'` |
| 20 | `')'` |
| 21 | `'\n'` |
| 22 | `'{'` |
| 23 | `'\n'` |
| 24 | `'\t'` |
| 25 | `'sw'` |
| 26 | `'p'` |
| 27 | `'_'` |
| 28 | `'entry'` |
| 29 | `'_'` |
| 30 | `'t'` |
| 31 | `'sw'` |
| 32 | `'p'` |
| 33 | `';'` |
| 34 | `'\n\n'` |
| 35 | `'\t'` |
| 36 | `'if'` |
| 37 | `'('` |
| 38 | `'huge'` |
| 39 | `'_'` |
| 40 | `'pt'` |
| 41 | `'e'` |
| 42 | `'_'` |
| 43 | `'none'` |
| 44 | `'('` |
| 45 | `'pt'` |
| 46 | `'e'` |
| 47 | `')'` |
| 48 | `'||'` |
| 49 | `'p'` |
| 50 | `'te'` |
| 51 | `'_'` |
| 52 | `'present'` |
| 53 | `'('` |
| 54 | `'pt'` |
| 55 | `'e'` |
| 56 | `'))'` |
| 57 | `'\n'` |
| 58 | `'\t'` |
| 59 | `'\t'` |
| 60 | `'return'` |
| 61 | `'false'` |
| 62 | `';'` |
| 63 | `'\n'` |
| 64 | `'\t'` |
| 65 | `'sw'` |
| 66 | `'p'` |
| 67 | `'='` |
| 68 | `'p'` |
| 69 | `'te'` |
| 70 | `'_'` |
| 71 | `'to'` |
| 72 | `'_'` |
| 73 | `'sw'` |
| 74 | `'p'` |
| 75 | `'_'` |
| 76 | `'entry'` |
| 77 | `'('` |
| 78 | `'pt'` |
| 79 | `'e'` |
| 80 | `');'` |
| 81 | `'\n'` |
| 82 | `'\t'` |
| 83 | `'if'` |
| 84 | `'('` |
| 85 | `'is'` |
| 86 | `'_'` |
| 87 | `'m'` |
| 88 | `'igration'` |
| 89 | `'_'` |
| 90 | `'entry'` |
| 91 | `'('` |
| 92 | `'sw'` |
| 93 | `'p'` |
| 94 | `'))'` |
| 95 | `'\n'` |
| 96 | `'\t'` |
| 97 | `'\t'` |
| 98 | `'return'` |
| 99 | `'true'` |
| 100 | `';'` |
| 101 | `'\n'` |
| 102 | `'\t'` |
| 103 | `'else'` |
| 104 | `'\n'` |
| 105 | `'\t'` |
| 106 | `'\t'` |
| 107 | `'return'` |
| 108 | `'false'` |
| 109 | `';'` |
| 110 | `'\n'` |
| 111 | `'}'` |
