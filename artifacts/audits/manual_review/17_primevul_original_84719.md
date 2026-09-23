# Review 17: `primevul:original:84719` (c)

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
   1 | static long tun_get_vnet_be(struct tun_struct *tun, int __user *argp)
   2 | {
   3 | 	int be = !!(tun->flags & TUN_VNET_BE);
   4 | 
   5 | 	if (put_user(be, argp))
   6 | 		return -EFAULT;
   7 | 
   8 | 	return 0;
   9 | }
  10 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `long` | 1:8 |
| 2 | `tun_get_vnet_be` | 1:13 |
| 4 | `struct` | 1:29 |
| 5 | `tun_struct` | 1:36 |
| 7 | `tun` | 1:48 |
| 9 | `int` | 1:53 |
| 10 | `__user` | 1:57 |
| 12 | `argp` | 1:65 |
| 15 | `int` | 3:2 |
| 16 | `be` | 3:6 |
| 21 | `tun` | 3:14 |
| 23 | `flags` | 3:19 |
| 25 | `TUN_VNET_BE` | 3:27 |
| 28 | `if` | 5:2 |
| 30 | `put_user` | 5:6 |
| 32 | `be` | 5:15 |
| 34 | `argp` | 5:19 |
| 37 | `return` | 6:3 |
| 39 | `EFAULT` | 6:11 |
| 41 | `return` | 8:2 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'long'` |
| 3 | `'tun'` |
| 4 | `'_'` |
| 5 | `'get'` |
| 6 | `'_'` |
| 7 | `'v'` |
| 8 | `'net'` |
| 9 | `'_'` |
| 10 | `'be'` |
| 11 | `'('` |
| 12 | `'struct'` |
| 13 | `'tun'` |
| 14 | `'_'` |
| 15 | `'struct'` |
| 16 | `'*'` |
| 17 | `'tun'` |
| 18 | `','` |
| 19 | `'int'` |
| 20 | `'__'` |
| 21 | `'user'` |
| 22 | `'*'` |
| 23 | `'arg'` |
| 24 | `'p'` |
| 25 | `')'` |
| 26 | `'\n'` |
| 27 | `'{'` |
| 28 | `'\n'` |
| 29 | `'\t'` |
| 30 | `'int'` |
| 31 | `'be'` |
| 32 | `'='` |
| 33 | `'!!'` |
| 34 | `'('` |
| 35 | `'tun'` |
| 36 | `'->'` |
| 37 | `'flags'` |
| 38 | `'&'` |
| 39 | `'T'` |
| 40 | `'UN'` |
| 41 | `'_'` |
| 42 | `'V'` |
| 43 | `'NET'` |
| 44 | `'_'` |
| 45 | `'BE'` |
| 46 | `');'` |
| 47 | `'\n\n'` |
| 48 | `'\t'` |
| 49 | `'if'` |
| 50 | `'('` |
| 51 | `'put'` |
| 52 | `'_'` |
| 53 | `'user'` |
| 54 | `'('` |
| 55 | `'be'` |
| 56 | `','` |
| 57 | `'arg'` |
| 58 | `'p'` |
| 59 | `'))'` |
| 60 | `'\n'` |
| 61 | `'\t'` |
| 62 | `'\t'` |
| 63 | `'return'` |
| 64 | `'-'` |
| 65 | `'E'` |
| 66 | `'FAULT'` |
| 67 | `';'` |
| 68 | `'\n\n'` |
| 69 | `'\t'` |
| 70 | `'return'` |
| 71 | `'0'` |
| 72 | `';'` |
| 73 | `'\n'` |
| 74 | `'}'` |
| 75 | `'\n'` |
