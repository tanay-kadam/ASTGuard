# Review 23: `primevul:original:491240` (c)

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
   1 | static int wireless_seq_show(struct seq_file *seq, void *v)
   2 | {
   3 | 	if (v == SEQ_START_TOKEN)
   4 | 		seq_printf(seq, "Inter-| sta-|   Quality        |   Discarded "
   5 | 				"packets               | Missed | WE\n"
   6 | 				" face | tus | link level noise |  nwid  "
   7 | 				"crypt   frag  retry   misc | beacon | %d\n",
   8 | 			   WIRELESS_EXT);
   9 | 	else
  10 | 		wireless_seq_printf_stats(seq, v);
  11 | 	return 0;
  12 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `int` | 1:8 |
| 2 | `wireless_seq_show` | 1:12 |
| 4 | `struct` | 1:30 |
| 5 | `seq_file` | 1:37 |
| 7 | `seq` | 1:47 |
| 9 | `void` | 1:52 |
| 11 | `v` | 1:58 |
| 14 | `if` | 3:2 |
| 16 | `v` | 3:6 |
| 18 | `SEQ_START_TOKEN` | 3:11 |
| 20 | `seq_printf` | 4:3 |
| 22 | `seq` | 4:14 |
| 29 | `WIRELESS_EXT` | 8:7 |
| 32 | `else` | 9:2 |
| 33 | `wireless_seq_printf_stats` | 10:3 |
| 35 | `seq` | 10:29 |
| 37 | `v` | 10:34 |
| 40 | `return` | 11:2 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'int'` |
| 3 | `'wireless'` |
| 4 | `'_'` |
| 5 | `'seq'` |
| 6 | `'_'` |
| 7 | `'show'` |
| 8 | `'('` |
| 9 | `'struct'` |
| 10 | `'seq'` |
| 11 | `'_'` |
| 12 | `'file'` |
| 13 | `'*'` |
| 14 | `'seq'` |
| 15 | `','` |
| 16 | `'void'` |
| 17 | `'*'` |
| 18 | `'v'` |
| 19 | `')'` |
| 20 | `'\n'` |
| 21 | `'{'` |
| 22 | `'\n'` |
| 23 | `'\t'` |
| 24 | `'if'` |
| 25 | `'('` |
| 26 | `'v'` |
| 27 | `'=='` |
| 28 | `'SE'` |
| 29 | `'Q'` |
| 30 | `'_'` |
| 31 | `'ST'` |
| 32 | `'ART'` |
| 33 | `'_'` |
| 34 | `'TO'` |
| 35 | `'KEN'` |
| 36 | `')'` |
| 37 | `'\n'` |
| 38 | `'\t'` |
| 39 | `'\t'` |
| 40 | `'seq'` |
| 41 | `'_'` |
| 42 | `'printf'` |
| 43 | `'('` |
| 44 | `'seq'` |
| 45 | `','` |
| 46 | `'"'` |
| 47 | `'Inter'` |
| 48 | `'-|'` |
| 49 | `'st'` |
| 50 | `'a'` |
| 51 | `'-|'` |
| 54 | `'Quality'` |
| 62 | `'|'` |
| 65 | `'Disc'` |
| 66 | `'arded'` |
| 67 | `'"'` |
| 68 | `'\n'` |
| 69 | `'\t'` |
| 70 | `'\t'` |
| 71 | `'\t'` |
| 72 | `'\t'` |
| 73 | `'"'` |
| 74 | `'pack'` |
| 75 | `'ets'` |
| 90 | `'|'` |
| 91 | `'Miss'` |
| 92 | `'ed'` |
| 93 | `'|'` |
| 94 | `'WE'` |
| 95 | `'\\'` |
| 96 | `'n'` |
| 97 | `'"'` |
| 98 | `'\n'` |
| 99 | `'\t'` |
| 100 | `'\t'` |
| 101 | `'\t'` |
| 102 | `'\t'` |
| 103 | `'"'` |
| 104 | `'face'` |
| 105 | `'|'` |
| 106 | `'t'` |
| 107 | `'us'` |
| 108 | `'|'` |
| 109 | `'link'` |
| 110 | `'level'` |
| 111 | `'noise'` |
| 112 | `'|'` |
| 114 | `'n'` |
| 115 | `'wid'` |
| 117 | `'"'` |
| 118 | `'\n'` |
| 119 | `'\t'` |
| 120 | `'\t'` |
| 121 | `'\t'` |
| 122 | `'\t'` |
| 123 | `'"'` |
| 124 | `'crypt'` |
| 127 | `'frag'` |
| 129 | `'ret'` |
| 130 | `'ry'` |
| 133 | `'misc'` |
| 134 | `'|'` |
| 135 | `'beacon'` |
| 136 | `'|'` |
| 137 | `'%'` |
| 138 | `'d'` |
| 139 | `'\\'` |
| 140 | `'n'` |
| 141 | `'",'` |
| 142 | `'\n'` |
| 143 | `'\t'` |
| 144 | `'\t'` |
| 145 | `'\t'` |
| 148 | `'WI'` |
| 149 | `'REL'` |
| 150 | `'ESS'` |
| 151 | `'_'` |
| 152 | `'EXT'` |
| 153 | `');'` |
| 154 | `'\n'` |
| 155 | `'\t'` |
| 156 | `'else'` |
| 157 | `'\n'` |
| 158 | `'\t'` |
| 159 | `'\t'` |
| 160 | `'wire'` |
| 161 | `'less'` |
| 162 | `'_'` |
| 163 | `'seq'` |
| 164 | `'_'` |
| 165 | `'printf'` |
| 166 | `'_'` |
| 167 | `'stats'` |
| 168 | `'('` |
| 169 | `'seq'` |
| 170 | `','` |
| 171 | `'v'` |
| 172 | `');'` |
| 173 | `'\n'` |
| 174 | `'\t'` |
| 175 | `'return'` |
| 176 | `'0'` |
| 177 | `';'` |
| 178 | `'\n'` |
| 179 | `'}'` |
