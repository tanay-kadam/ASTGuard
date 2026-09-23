# Review 21: `primevul:original:520244` (c)

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
   1 | int jsiPopArgs(Jsi_OpCodes *argCodes, int i)
   2 | {
   3 |     int m=i-1, n = (uintptr_t)argCodes->codes[i].data, cnt = 0;
   4 |     if (argCodes->codes[i].op == OP_OBJECT)
   5 |         n *= 2;
   6 |     for (; m>=0 && cnt<n; m--, cnt++) {
   7 |         int op = argCodes->codes[m].op;
   8 |         if (op == OP_ARRAY || op == OP_OBJECT)
   9 |             m = jsiPopArgs(argCodes, m);
  10 |     }
  11 |     return m+1;
  12 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `int` | 1:1 |
| 1 | `jsiPopArgs` | 1:5 |
| 3 | `Jsi_OpCodes` | 1:16 |
| 5 | `argCodes` | 1:29 |
| 7 | `int` | 1:39 |
| 8 | `i` | 1:43 |
| 11 | `int` | 3:5 |
| 12 | `m` | 3:9 |
| 14 | `i` | 3:11 |
| 18 | `n` | 3:16 |
| 21 | `uintptr_t` | 3:21 |
| 23 | `argCodes` | 3:31 |
| 25 | `codes` | 3:41 |
| 27 | `i` | 3:47 |
| 30 | `data` | 3:50 |
| 32 | `cnt` | 3:56 |
| 36 | `if` | 4:5 |
| 38 | `argCodes` | 4:9 |
| 40 | `codes` | 4:19 |
| 42 | `i` | 4:25 |
| 45 | `op` | 4:28 |
| 47 | `OP_OBJECT` | 4:34 |
| 49 | `n` | 5:9 |
| 53 | `for` | 6:5 |
| 56 | `m` | 6:12 |
| 60 | `cnt` | 6:20 |
| 62 | `n` | 6:24 |
| 64 | `m` | 6:27 |
| 67 | `cnt` | 6:32 |
| 71 | `int` | 7:9 |
| 72 | `op` | 7:13 |
| 74 | `argCodes` | 7:18 |
| 76 | `codes` | 7:28 |
| 78 | `m` | 7:34 |
| 81 | `op` | 7:37 |
| 83 | `if` | 8:9 |
| 85 | `op` | 8:13 |
| 87 | `OP_ARRAY` | 8:19 |
| 89 | `op` | 8:31 |
| 91 | `OP_OBJECT` | 8:37 |
| 93 | `m` | 9:13 |
| 95 | `jsiPopArgs` | 9:17 |
| 97 | `argCodes` | 9:28 |
| 99 | `m` | 9:38 |
| 103 | `return` | 11:5 |
| 104 | `m` | 11:12 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'int'` |
| 2 | `'j'` |
| 3 | `'si'` |
| 4 | `'Pop'` |
| 5 | `'Args'` |
| 6 | `'('` |
| 7 | `'J'` |
| 8 | `'si'` |
| 9 | `'_'` |
| 10 | `'Op'` |
| 11 | `'C'` |
| 12 | `'odes'` |
| 13 | `'*'` |
| 14 | `'arg'` |
| 15 | `'C'` |
| 16 | `'odes'` |
| 17 | `','` |
| 18 | `'int'` |
| 19 | `'i'` |
| 20 | `')'` |
| 21 | `'\n'` |
| 22 | `'{'` |
| 23 | `'\n'` |
| 27 | `'int'` |
| 28 | `'m'` |
| 29 | `'='` |
| 30 | `'i'` |
| 31 | `'-'` |
| 32 | `'1'` |
| 33 | `','` |
| 34 | `'n'` |
| 35 | `'='` |
| 36 | `'('` |
| 37 | `'uint'` |
| 38 | `'ptr'` |
| 39 | `'_'` |
| 40 | `'t'` |
| 41 | `')'` |
| 42 | `'arg'` |
| 43 | `'C'` |
| 44 | `'odes'` |
| 45 | `'->'` |
| 46 | `'codes'` |
| 47 | `'['` |
| 48 | `'i'` |
| 49 | `'].'` |
| 50 | `'data'` |
| 51 | `','` |
| 52 | `'c'` |
| 53 | `'nt'` |
| 54 | `'='` |
| 55 | `'0'` |
| 56 | `';'` |
| 57 | `'\n'` |
| 61 | `'if'` |
| 62 | `'('` |
| 63 | `'arg'` |
| 64 | `'C'` |
| 65 | `'odes'` |
| 66 | `'->'` |
| 67 | `'codes'` |
| 68 | `'['` |
| 69 | `'i'` |
| 70 | `'].'` |
| 71 | `'op'` |
| 72 | `'=='` |
| 73 | `'OP'` |
| 74 | `'_'` |
| 75 | `'OB'` |
| 76 | `'JECT'` |
| 77 | `')'` |
| 78 | `'\n'` |
| 86 | `'n'` |
| 87 | `'*'` |
| 88 | `'='` |
| 89 | `'2'` |
| 90 | `';'` |
| 91 | `'\n'` |
| 95 | `'for'` |
| 96 | `'('` |
| 97 | `';'` |
| 98 | `'m'` |
| 99 | `'>'` |
| 100 | `'='` |
| 101 | `'0'` |
| 102 | `'&&'` |
| 103 | `'c'` |
| 104 | `'nt'` |
| 105 | `'<'` |
| 106 | `'n'` |
| 107 | `';'` |
| 108 | `'m'` |
| 109 | `'--'` |
| 110 | `','` |
| 111 | `'c'` |
| 112 | `'nt'` |
| 113 | `'++)'` |
| 114 | `'{'` |
| 115 | `'\n'` |
| 123 | `'int'` |
| 124 | `'op'` |
| 125 | `'='` |
| 126 | `'arg'` |
| 127 | `'C'` |
| 128 | `'odes'` |
| 129 | `'->'` |
| 130 | `'codes'` |
| 131 | `'['` |
| 132 | `'m'` |
| 133 | `'].'` |
| 134 | `'op'` |
| 135 | `';'` |
| 136 | `'\n'` |
| 144 | `'if'` |
| 145 | `'('` |
| 146 | `'op'` |
| 147 | `'=='` |
| 148 | `'OP'` |
| 149 | `'_'` |
| 150 | `'AR'` |
| 151 | `'RAY'` |
| 152 | `'||'` |
| 153 | `'op'` |
| 154 | `'=='` |
| 155 | `'OP'` |
| 156 | `'_'` |
| 157 | `'OB'` |
| 158 | `'JECT'` |
| 159 | `')'` |
| 160 | `'\n'` |
| 172 | `'m'` |
| 173 | `'='` |
| 174 | `'j'` |
| 175 | `'si'` |
| 176 | `'Pop'` |
| 177 | `'Args'` |
| 178 | `'('` |
| 179 | `'arg'` |
| 180 | `'C'` |
| 181 | `'odes'` |
| 182 | `','` |
| 183 | `'m'` |
| 184 | `');'` |
| 185 | `'\n'` |
| 189 | `'}'` |
| 190 | `'\n'` |
| 194 | `'return'` |
| 195 | `'m'` |
| 196 | `'+'` |
| 197 | `'1'` |
| 198 | `';'` |
| 199 | `'\n'` |
| 200 | `'}'` |
