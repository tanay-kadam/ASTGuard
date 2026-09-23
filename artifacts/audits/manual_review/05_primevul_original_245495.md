# Review 05: `primevul:original:245495` (c)

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
   1 | static int klv_read_packet(KLVPacket *klv, AVIOContext *pb)
   2 | {
   3 |     if (!mxf_read_sync(pb, mxf_klv_key, 4))
   4 |         return AVERROR_INVALIDDATA;
   5 |     klv->offset = avio_tell(pb) - 4;
   6 |     memcpy(klv->key, mxf_klv_key, 4);
   7 |     avio_read(pb, klv->key + 4, 12);
   8 |     klv->length = klv_decode_ber_length(pb);
   9 |     return klv->length == -1 ? -1 : 0;
  10 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `int` | 1:8 |
| 2 | `klv_read_packet` | 1:12 |
| 4 | `KLVPacket` | 1:28 |
| 6 | `klv` | 1:39 |
| 8 | `AVIOContext` | 1:44 |
| 10 | `pb` | 1:57 |
| 13 | `if` | 3:5 |
| 16 | `mxf_read_sync` | 3:10 |
| 18 | `pb` | 3:24 |
| 20 | `mxf_klv_key` | 3:28 |
| 25 | `return` | 4:9 |
| 26 | `AVERROR_INVALIDDATA` | 4:16 |
| 28 | `klv` | 5:5 |
| 30 | `offset` | 5:10 |
| 32 | `avio_tell` | 5:19 |
| 34 | `pb` | 5:29 |
| 39 | `memcpy` | 6:5 |
| 41 | `klv` | 6:12 |
| 43 | `key` | 6:17 |
| 45 | `mxf_klv_key` | 6:22 |
| 50 | `avio_read` | 7:5 |
| 52 | `pb` | 7:15 |
| 54 | `klv` | 7:19 |
| 56 | `key` | 7:24 |
| 63 | `klv` | 8:5 |
| 65 | `length` | 8:10 |
| 67 | `klv_decode_ber_length` | 8:19 |
| 69 | `pb` | 8:41 |
| 72 | `return` | 9:5 |
| 73 | `klv` | 9:12 |
| 75 | `length` | 9:17 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'int'` |
| 3 | `'k'` |
| 4 | `'lv'` |
| 5 | `'_'` |
| 6 | `'read'` |
| 7 | `'_'` |
| 8 | `'pack'` |
| 9 | `'et'` |
| 10 | `'('` |
| 11 | `'K'` |
| 12 | `'L'` |
| 13 | `'VP'` |
| 14 | `'acket'` |
| 15 | `'*'` |
| 16 | `'k'` |
| 17 | `'lv'` |
| 18 | `','` |
| 19 | `'AV'` |
| 20 | `'IO'` |
| 21 | `'Context'` |
| 22 | `'*'` |
| 23 | `'pb'` |
| 24 | `')'` |
| 25 | `'\n'` |
| 26 | `'{'` |
| 27 | `'\n'` |
| 31 | `'if'` |
| 32 | `'(!'` |
| 33 | `'m'` |
| 34 | `'xf'` |
| 35 | `'_'` |
| 36 | `'read'` |
| 37 | `'_'` |
| 38 | `'sync'` |
| 39 | `'('` |
| 40 | `'pb'` |
| 41 | `','` |
| 42 | `'m'` |
| 43 | `'xf'` |
| 44 | `'_'` |
| 45 | `'k'` |
| 46 | `'lv'` |
| 47 | `'_'` |
| 48 | `'key'` |
| 49 | `','` |
| 50 | `'4'` |
| 51 | `'))'` |
| 52 | `'\n'` |
| 60 | `'return'` |
| 61 | `'A'` |
| 62 | `'VER'` |
| 63 | `'ROR'` |
| 64 | `'_'` |
| 65 | `'IN'` |
| 66 | `'VAL'` |
| 67 | `'ID'` |
| 68 | `'DATA'` |
| 69 | `';'` |
| 70 | `'\n'` |
| 74 | `'k'` |
| 75 | `'lv'` |
| 76 | `'->'` |
| 77 | `'offset'` |
| 78 | `'='` |
| 79 | `'av'` |
| 80 | `'io'` |
| 81 | `'_'` |
| 82 | `'tell'` |
| 83 | `'('` |
| 84 | `'pb'` |
| 85 | `')'` |
| 86 | `'-'` |
| 87 | `'4'` |
| 88 | `';'` |
| 89 | `'\n'` |
| 93 | `'mem'` |
| 94 | `'c'` |
| 95 | `'py'` |
| 96 | `'('` |
| 97 | `'k'` |
| 98 | `'lv'` |
| 99 | `'->'` |
| 100 | `'key'` |
| 101 | `','` |
| 102 | `'m'` |
| 103 | `'xf'` |
| 104 | `'_'` |
| 105 | `'k'` |
| 106 | `'lv'` |
| 107 | `'_'` |
| 108 | `'key'` |
| 109 | `','` |
| 110 | `'4'` |
| 111 | `');'` |
| 112 | `'\n'` |
| 116 | `'av'` |
| 117 | `'io'` |
| 118 | `'_'` |
| 119 | `'read'` |
| 120 | `'('` |
| 121 | `'pb'` |
| 122 | `','` |
| 123 | `'k'` |
| 124 | `'lv'` |
| 125 | `'->'` |
| 126 | `'key'` |
| 127 | `'+'` |
| 128 | `'4'` |
| 129 | `','` |
| 130 | `'12'` |
| 131 | `');'` |
| 132 | `'\n'` |
| 136 | `'k'` |
| 137 | `'lv'` |
| 138 | `'->'` |
| 139 | `'length'` |
| 140 | `'='` |
| 141 | `'k'` |
| 142 | `'lv'` |
| 143 | `'_'` |
| 144 | `'dec'` |
| 145 | `'ode'` |
| 146 | `'_'` |
| 147 | `'ber'` |
| 148 | `'_'` |
| 149 | `'length'` |
| 150 | `'('` |
| 151 | `'pb'` |
| 152 | `');'` |
| 153 | `'\n'` |
| 157 | `'return'` |
| 158 | `'k'` |
| 159 | `'lv'` |
| 160 | `'->'` |
| 161 | `'length'` |
| 162 | `'=='` |
| 163 | `'-'` |
| 164 | `'1'` |
| 165 | `'?'` |
| 166 | `'-'` |
| 167 | `'1'` |
| 168 | `':'` |
| 169 | `'0'` |
| 170 | `';'` |
| 171 | `'\n'` |
| 172 | `'}'` |
