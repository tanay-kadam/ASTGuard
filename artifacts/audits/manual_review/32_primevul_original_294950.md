# Review 32: `primevul:original:294950` (c)

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
   1 | static void kvm_get_preset_lpj(void)
   2 | {
   3 | 	unsigned long khz;
   4 | 	u64 lpj;
   5 | 
   6 | 	khz = kvm_get_tsc_khz();
   7 | 
   8 | 	lpj = ((u64)khz * 1000);
   9 | 	do_div(lpj, HZ);
  10 | 	preset_lpj = lpj;
  11 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `void` | 1:8 |
| 2 | `kvm_get_preset_lpj` | 1:13 |
| 4 | `void` | 1:32 |
| 7 | `unsigned` | 3:2 |
| 8 | `long` | 3:11 |
| 9 | `khz` | 3:16 |
| 11 | `u64` | 4:2 |
| 12 | `lpj` | 4:6 |
| 14 | `khz` | 6:2 |
| 16 | `kvm_get_tsc_khz` | 6:8 |
| 20 | `lpj` | 8:2 |
| 24 | `u64` | 8:10 |
| 26 | `khz` | 8:14 |
| 31 | `do_div` | 9:2 |
| 33 | `lpj` | 9:9 |
| 35 | `HZ` | 9:14 |
| 38 | `preset_lpj` | 10:2 |
| 40 | `lpj` | 10:15 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'void'` |
| 3 | `'k'` |
| 4 | `'vm'` |
| 5 | `'_'` |
| 6 | `'get'` |
| 7 | `'_'` |
| 8 | `'pres'` |
| 9 | `'et'` |
| 10 | `'_'` |
| 11 | `'lp'` |
| 12 | `'j'` |
| 13 | `'('` |
| 14 | `'void'` |
| 15 | `')'` |
| 16 | `'\n'` |
| 17 | `'{'` |
| 18 | `'\n'` |
| 19 | `'\t'` |
| 20 | `'unsigned'` |
| 21 | `'long'` |
| 22 | `'k'` |
| 23 | `'hz'` |
| 24 | `';'` |
| 25 | `'\n'` |
| 26 | `'\t'` |
| 27 | `'u'` |
| 28 | `'64'` |
| 29 | `'l'` |
| 30 | `'p'` |
| 31 | `'j'` |
| 32 | `';'` |
| 33 | `'\n\n'` |
| 34 | `'\t'` |
| 35 | `'kh'` |
| 36 | `'z'` |
| 37 | `'='` |
| 38 | `'k'` |
| 39 | `'vm'` |
| 40 | `'_'` |
| 41 | `'get'` |
| 42 | `'_'` |
| 43 | `'ts'` |
| 44 | `'c'` |
| 45 | `'_'` |
| 46 | `'kh'` |
| 47 | `'z'` |
| 48 | `'();'` |
| 49 | `'\n\n'` |
| 50 | `'\t'` |
| 51 | `'lp'` |
| 52 | `'j'` |
| 53 | `'='` |
| 54 | `'(('` |
| 55 | `'u'` |
| 56 | `'64'` |
| 57 | `')'` |
| 58 | `'kh'` |
| 59 | `'z'` |
| 60 | `'*'` |
| 61 | `'1000'` |
| 62 | `');'` |
| 63 | `'\n'` |
| 64 | `'\t'` |
| 65 | `'do'` |
| 66 | `'_'` |
| 67 | `'div'` |
| 68 | `'('` |
| 69 | `'lp'` |
| 70 | `'j'` |
| 71 | `','` |
| 72 | `'H'` |
| 73 | `'Z'` |
| 74 | `');'` |
| 75 | `'\n'` |
| 76 | `'\t'` |
| 77 | `'pres'` |
| 78 | `'et'` |
| 79 | `'_'` |
| 80 | `'lp'` |
| 81 | `'j'` |
| 82 | `'='` |
| 83 | `'l'` |
| 84 | `'p'` |
| 85 | `'j'` |
| 86 | `';'` |
| 87 | `'\n'` |
| 88 | `'}'` |
