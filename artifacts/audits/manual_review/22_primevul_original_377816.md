# Review 22: `primevul:original:377816` (c)

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
   1 | _Track *_af_track_new (void)
   2 | {
   3 | 	_Track *t = (_Track *) _af_malloc(sizeof (_Track));
   4 | 
   5 | 	t->id = AF_DEFAULT_TRACK;
   6 | 
   7 | 	t->f.compressionParams = NULL;
   8 | 	t->v.compressionParams = NULL;
   9 | 
  10 | 	t->channelMatrix = NULL;
  11 | 
  12 | 	t->markerCount = 0;
  13 | 	t->markers = NULL;
  14 | 
  15 | 	t->hasAESData = false;
  16 | 	memset(t->aesData, 0, 24);
  17 | 
  18 | 	t->totalfframes = 0;
  19 | 	t->nextfframe = 0;
  20 | 	t->frames2ignore = 0;
  21 | 	t->fpos_first_frame = 0;
  22 | 	t->fpos_next_frame = 0;
  23 | 	t->fpos_after_data = 0;
  24 | 	t->totalvframes = 0;
  25 | 	t->nextvframe = 0;
  26 | 	t->data_size = 0;
  27 | 
  28 | 	t->ms = NULL;
  29 | 
  30 | 	return t;
  31 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `_Track` | 1:1 |
| 2 | `_af_track_new` | 1:9 |
| 4 | `void` | 1:24 |
| 7 | `_Track` | 3:2 |
| 9 | `t` | 3:10 |
| 12 | `_Track` | 3:15 |
| 15 | `_af_malloc` | 3:25 |
| 17 | `sizeof` | 3:36 |
| 19 | `_Track` | 3:44 |
| 23 | `t` | 5:2 |
| 25 | `id` | 5:5 |
| 27 | `AF_DEFAULT_TRACK` | 5:10 |
| 29 | `t` | 7:2 |
| 31 | `f` | 7:5 |
| 33 | `compressionParams` | 7:7 |
| 35 | `NULL` | 7:27 |
| 37 | `t` | 8:2 |
| 39 | `v` | 8:5 |
| 41 | `compressionParams` | 8:7 |
| 43 | `NULL` | 8:27 |
| 45 | `t` | 10:2 |
| 47 | `channelMatrix` | 10:5 |
| 49 | `NULL` | 10:21 |
| 51 | `t` | 12:2 |
| 53 | `markerCount` | 12:5 |
| 57 | `t` | 13:2 |
| 59 | `markers` | 13:5 |
| 61 | `NULL` | 13:15 |
| 63 | `t` | 15:2 |
| 65 | `hasAESData` | 15:5 |
| 67 | `false` | 15:18 |
| 69 | `memset` | 16:2 |
| 71 | `t` | 16:9 |
| 73 | `aesData` | 16:12 |
| 80 | `t` | 18:2 |
| 82 | `totalfframes` | 18:5 |
| 86 | `t` | 19:2 |
| 88 | `nextfframe` | 19:5 |
| 92 | `t` | 20:2 |
| 94 | `frames2ignore` | 20:5 |
| 98 | `t` | 21:2 |
| 100 | `fpos_first_frame` | 21:5 |
| 104 | `t` | 22:2 |
| 106 | `fpos_next_frame` | 22:5 |
| 110 | `t` | 23:2 |
| 112 | `fpos_after_data` | 23:5 |
| 116 | `t` | 24:2 |
| 118 | `totalvframes` | 24:5 |
| 122 | `t` | 25:2 |
| 124 | `nextvframe` | 25:5 |
| 128 | `t` | 26:2 |
| 130 | `data_size` | 26:5 |
| 134 | `t` | 28:2 |
| 136 | `ms` | 28:5 |
| 138 | `NULL` | 28:10 |
| 140 | `return` | 30:2 |
| 141 | `t` | 30:9 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'_'` |
| 2 | `'Track'` |
| 3 | `'*'` |
| 4 | `'_'` |
| 5 | `'af'` |
| 6 | `'_'` |
| 7 | `'track'` |
| 8 | `'_'` |
| 9 | `'new'` |
| 10 | `'('` |
| 11 | `'void'` |
| 12 | `')'` |
| 13 | `'\n'` |
| 14 | `'{'` |
| 15 | `'\n'` |
| 16 | `'\t'` |
| 17 | `'_'` |
| 18 | `'Track'` |
| 19 | `'*'` |
| 20 | `'t'` |
| 21 | `'='` |
| 22 | `'(_'` |
| 23 | `'Track'` |
| 24 | `'*)'` |
| 25 | `'_'` |
| 26 | `'af'` |
| 27 | `'_'` |
| 28 | `'m'` |
| 29 | `'alloc'` |
| 30 | `'('` |
| 31 | `'size'` |
| 32 | `'of'` |
| 33 | `'(_'` |
| 34 | `'Track'` |
| 35 | `'));'` |
| 36 | `'\n\n'` |
| 37 | `'\t'` |
| 38 | `'t'` |
| 39 | `'->'` |
| 40 | `'id'` |
| 41 | `'='` |
| 42 | `'AF'` |
| 43 | `'_'` |
| 44 | `'DE'` |
| 45 | `'FAULT'` |
| 46 | `'_'` |
| 47 | `'TR'` |
| 48 | `'ACK'` |
| 49 | `';'` |
| 50 | `'\n\n'` |
| 51 | `'\t'` |
| 52 | `'t'` |
| 53 | `'->'` |
| 54 | `'f'` |
| 55 | `'.'` |
| 56 | `'comp'` |
| 57 | `'ression'` |
| 58 | `'Par'` |
| 59 | `'ams'` |
| 60 | `'='` |
| 61 | `'NULL'` |
| 62 | `';'` |
| 63 | `'\n'` |
| 64 | `'\t'` |
| 65 | `'t'` |
| 66 | `'->'` |
| 67 | `'v'` |
| 68 | `'.'` |
| 69 | `'comp'` |
| 70 | `'ression'` |
| 71 | `'Par'` |
| 72 | `'ams'` |
| 73 | `'='` |
| 74 | `'NULL'` |
| 75 | `';'` |
| 76 | `'\n\n'` |
| 77 | `'\t'` |
| 78 | `'t'` |
| 79 | `'->'` |
| 80 | `'channel'` |
| 81 | `'Matrix'` |
| 82 | `'='` |
| 83 | `'NULL'` |
| 84 | `';'` |
| 85 | `'\n\n'` |
| 86 | `'\t'` |
| 87 | `'t'` |
| 88 | `'->'` |
| 89 | `'mark'` |
| 90 | `'er'` |
| 91 | `'Count'` |
| 92 | `'='` |
| 93 | `'0'` |
| 94 | `';'` |
| 95 | `'\n'` |
| 96 | `'\t'` |
| 97 | `'t'` |
| 98 | `'->'` |
| 99 | `'mark'` |
| 100 | `'ers'` |
| 101 | `'='` |
| 102 | `'NULL'` |
| 103 | `';'` |
| 104 | `'\n\n'` |
| 105 | `'\t'` |
| 106 | `'t'` |
| 107 | `'->'` |
| 108 | `'has'` |
| 109 | `'A'` |
| 110 | `'ES'` |
| 111 | `'Data'` |
| 112 | `'='` |
| 113 | `'false'` |
| 114 | `';'` |
| 115 | `'\n'` |
| 116 | `'\t'` |
| 117 | `'mem'` |
| 118 | `'set'` |
| 119 | `'('` |
| 120 | `'t'` |
| 121 | `'->'` |
| 122 | `'a'` |
| 123 | `'es'` |
| 124 | `'Data'` |
| 125 | `','` |
| 126 | `'0'` |
| 127 | `','` |
| 128 | `'24'` |
| 129 | `');'` |
| 130 | `'\n\n'` |
| 131 | `'\t'` |
| 132 | `'t'` |
| 133 | `'->'` |
| 134 | `'total'` |
| 135 | `'ff'` |
| 136 | `'ram'` |
| 137 | `'es'` |
| 138 | `'='` |
| 139 | `'0'` |
| 140 | `';'` |
| 141 | `'\n'` |
| 142 | `'\t'` |
| 143 | `'t'` |
| 144 | `'->'` |
| 145 | `'next'` |
| 146 | `'ff'` |
| 147 | `'rame'` |
| 148 | `'='` |
| 149 | `'0'` |
| 150 | `';'` |
| 151 | `'\n'` |
| 152 | `'\t'` |
| 153 | `'t'` |
| 154 | `'->'` |
| 155 | `'frames'` |
| 156 | `'2'` |
| 157 | `'ignore'` |
| 158 | `'='` |
| 159 | `'0'` |
| 160 | `';'` |
| 161 | `'\n'` |
| 162 | `'\t'` |
| 163 | `'t'` |
| 164 | `'->'` |
| 165 | `'f'` |
| 166 | `'pos'` |
| 167 | `'_'` |
| 168 | `'first'` |
| 169 | `'_'` |
| 170 | `'frame'` |
| 171 | `'='` |
| 172 | `'0'` |
| 173 | `';'` |
| 174 | `'\n'` |
| 175 | `'\t'` |
| 176 | `'t'` |
| 177 | `'->'` |
| 178 | `'f'` |
| 179 | `'pos'` |
| 180 | `'_'` |
| 181 | `'next'` |
| 182 | `'_'` |
| 183 | `'frame'` |
| 184 | `'='` |
| 185 | `'0'` |
| 186 | `';'` |
| 187 | `'\n'` |
| 188 | `'\t'` |
| 189 | `'t'` |
| 190 | `'->'` |
| 191 | `'f'` |
| 192 | `'pos'` |
| 193 | `'_'` |
| 194 | `'after'` |
| 195 | `'_'` |
| 196 | `'data'` |
| 197 | `'='` |
| 198 | `'0'` |
| 199 | `';'` |
| 200 | `'\n'` |
| 201 | `'\t'` |
| 202 | `'t'` |
| 203 | `'->'` |
| 204 | `'total'` |
| 205 | `'v'` |
| 206 | `'frames'` |
| 207 | `'='` |
| 208 | `'0'` |
| 209 | `';'` |
| 210 | `'\n'` |
| 211 | `'\t'` |
| 212 | `'t'` |
| 213 | `'->'` |
| 214 | `'next'` |
| 215 | `'v'` |
| 216 | `'frame'` |
| 217 | `'='` |
| 218 | `'0'` |
| 219 | `';'` |
| 220 | `'\n'` |
| 221 | `'\t'` |
| 222 | `'t'` |
| 223 | `'->'` |
| 224 | `'data'` |
| 225 | `'_'` |
| 226 | `'size'` |
| 227 | `'='` |
| 228 | `'0'` |
| 229 | `';'` |
| 230 | `'\n\n'` |
| 231 | `'\t'` |
| 232 | `'t'` |
| 233 | `'->'` |
| 234 | `'ms'` |
| 235 | `'='` |
| 236 | `'NULL'` |
| 237 | `';'` |
| 238 | `'\n\n'` |
| 239 | `'\t'` |
| 240 | `'return'` |
| 241 | `'t'` |
| 242 | `';'` |
| 243 | `'\n'` |
| 244 | `'}'` |
