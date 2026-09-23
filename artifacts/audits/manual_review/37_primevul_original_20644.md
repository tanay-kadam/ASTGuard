# Review 37: `primevul:original:20644` (cpp)

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
   1 |   tt_cmap8_char_index( TT_CMap    cmap,
   2 |                        FT_UInt32  char_code )
   3 |   {
   4 |     FT_Byte*   table      = cmap->data;
   5 |     FT_UInt    result     = 0;
   6 |     FT_Byte*   p          = table + 8204;
   7 |     FT_UInt32  num_groups = TT_NEXT_ULONG( p );
   8 |     FT_UInt32  start, end, start_id;
   9 | 
  10 | 
  11 |     for ( ; num_groups > 0; num_groups-- )
  12 |     {
  13 |       start    = TT_NEXT_ULONG( p );
  14 |       end      = TT_NEXT_ULONG( p );
  15 |       start_id = TT_NEXT_ULONG( p );
  16 | 
  17 |       if ( char_code < start )
  18 |         break;
  19 | 
  20 |       if ( char_code <= end )
  21 |       {
  22 |         if ( start_id > 0xFFFFFFFFUL - ( char_code - start ) )
  23 |           return 0;
  24 | 
  25 |         result = (FT_UInt)( start_id + ( char_code - start ) );
  26 |         break;
  27 |       }
  28 |     }
  29 |     return result;
  30 |   }
  31 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `tt_cmap8_char_index` | 1:3 |
| 2 | `TT_CMap` | 1:24 |
| 3 | `cmap` | 1:35 |
| 5 | `FT_UInt32` | 2:24 |
| 6 | `char_code` | 2:35 |
| 9 | `FT_Byte` | 4:5 |
| 11 | `table` | 4:16 |
| 13 | `cmap` | 4:29 |
| 15 | `data` | 4:35 |
| 17 | `FT_UInt` | 5:5 |
| 18 | `result` | 5:16 |
| 22 | `FT_Byte` | 6:5 |
| 24 | `p` | 6:16 |
| 26 | `table` | 6:29 |
| 30 | `FT_UInt32` | 7:5 |
| 31 | `num_groups` | 7:16 |
| 33 | `TT_NEXT_ULONG` | 7:29 |
| 35 | `p` | 7:44 |
| 38 | `FT_UInt32` | 8:5 |
| 39 | `start` | 8:16 |
| 41 | `end` | 8:23 |
| 43 | `start_id` | 8:28 |
| 45 | `for` | 11:5 |
| 48 | `num_groups` | 11:13 |
| 52 | `num_groups` | 11:29 |
| 56 | `start` | 13:7 |
| 58 | `TT_NEXT_ULONG` | 13:18 |
| 60 | `p` | 13:33 |
| 63 | `end` | 14:7 |
| 65 | `TT_NEXT_ULONG` | 14:18 |
| 67 | `p` | 14:33 |
| 70 | `start_id` | 15:7 |
| 72 | `TT_NEXT_ULONG` | 15:18 |
| 74 | `p` | 15:33 |
| 77 | `if` | 17:7 |
| 79 | `char_code` | 17:12 |
| 81 | `start` | 17:24 |
| 83 | `break` | 18:9 |
| 85 | `if` | 20:7 |
| 87 | `char_code` | 20:12 |
| 89 | `end` | 20:25 |
| 92 | `if` | 22:9 |
| 94 | `start_id` | 22:14 |
| 97 | `UL` | 22:35 |
| 100 | `char_code` | 22:42 |
| 102 | `start` | 22:54 |
| 105 | `return` | 23:11 |
| 108 | `result` | 25:9 |
| 111 | `FT_UInt` | 25:19 |
| 114 | `start_id` | 25:29 |
| 117 | `char_code` | 25:42 |
| 119 | `start` | 25:54 |
| 123 | `break` | 26:9 |
| 127 | `return` | 29:5 |
| 128 | `result` | 29:12 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 2 | `'t'` |
| 3 | `'t'` |
| 4 | `'_'` |
| 5 | `'c'` |
| 6 | `'map'` |
| 7 | `'8'` |
| 8 | `'_'` |
| 9 | `'char'` |
| 10 | `'_'` |
| 11 | `'index'` |
| 12 | `'('` |
| 13 | `'TT'` |
| 14 | `'_'` |
| 15 | `'C'` |
| 16 | `'Map'` |
| 20 | `'c'` |
| 21 | `'map'` |
| 22 | `','` |
| 23 | `'\n'` |
| 46 | `'FT'` |
| 47 | `'_'` |
| 48 | `'U'` |
| 49 | `'Int'` |
| 50 | `'32'` |
| 52 | `'char'` |
| 53 | `'_'` |
| 54 | `'code'` |
| 55 | `')'` |
| 56 | `'\n'` |
| 58 | `'{'` |
| 59 | `'\n'` |
| 63 | `'FT'` |
| 64 | `'_'` |
| 65 | `'Byte'` |
| 66 | `'*'` |
| 69 | `'table'` |
| 75 | `'='` |
| 76 | `'c'` |
| 77 | `'map'` |
| 78 | `'->'` |
| 79 | `'data'` |
| 80 | `';'` |
| 81 | `'\n'` |
| 85 | `'FT'` |
| 86 | `'_'` |
| 87 | `'U'` |
| 88 | `'Int'` |
| 92 | `'result'` |
| 97 | `'='` |
| 98 | `'0'` |
| 99 | `';'` |
| 100 | `'\n'` |
| 104 | `'FT'` |
| 105 | `'_'` |
| 106 | `'Byte'` |
| 107 | `'*'` |
| 110 | `'p'` |
| 120 | `'='` |
| 121 | `'table'` |
| 122 | `'+'` |
| 123 | `'8'` |
| 124 | `'204'` |
| 125 | `';'` |
| 126 | `'\n'` |
| 130 | `'FT'` |
| 131 | `'_'` |
| 132 | `'U'` |
| 133 | `'Int'` |
| 134 | `'32'` |
| 136 | `'num'` |
| 137 | `'_'` |
| 138 | `'groups'` |
| 139 | `'='` |
| 140 | `'TT'` |
| 141 | `'_'` |
| 142 | `'N'` |
| 143 | `'EXT'` |
| 144 | `'_'` |
| 145 | `'UL'` |
| 146 | `'ONG'` |
| 147 | `'('` |
| 148 | `'p'` |
| 149 | `');'` |
| 150 | `'\n'` |
| 154 | `'FT'` |
| 155 | `'_'` |
| 156 | `'U'` |
| 157 | `'Int'` |
| 158 | `'32'` |
| 160 | `'start'` |
| 161 | `','` |
| 162 | `'end'` |
| 163 | `','` |
| 164 | `'start'` |
| 165 | `'_'` |
| 166 | `'id'` |
| 167 | `';'` |
| 168 | `'\n\n'` |
| 169 | `'\n'` |
| 173 | `'for'` |
| 174 | `'('` |
| 175 | `';'` |
| 176 | `'num'` |
| 177 | `'_'` |
| 178 | `'groups'` |
| 179 | `'>'` |
| 180 | `'0'` |
| 181 | `';'` |
| 182 | `'num'` |
| 183 | `'_'` |
| 184 | `'groups'` |
| 185 | `'--'` |
| 186 | `')'` |
| 187 | `'\n'` |
| 191 | `'{'` |
| 192 | `'\n'` |
| 198 | `'start'` |
| 202 | `'='` |
| 203 | `'TT'` |
| 204 | `'_'` |
| 205 | `'N'` |
| 206 | `'EXT'` |
| 207 | `'_'` |
| 208 | `'UL'` |
| 209 | `'ONG'` |
| 210 | `'('` |
| 211 | `'p'` |
| 212 | `');'` |
| 213 | `'\n'` |
| 219 | `'end'` |
| 225 | `'='` |
| 226 | `'TT'` |
| 227 | `'_'` |
| 228 | `'N'` |
| 229 | `'EXT'` |
| 230 | `'_'` |
| 231 | `'UL'` |
| 232 | `'ONG'` |
| 233 | `'('` |
| 234 | `'p'` |
| 235 | `');'` |
| 236 | `'\n'` |
| 242 | `'start'` |
| 243 | `'_'` |
| 244 | `'id'` |
| 245 | `'='` |
| 246 | `'TT'` |
| 247 | `'_'` |
| 248 | `'N'` |
| 249 | `'EXT'` |
| 250 | `'_'` |
| 251 | `'UL'` |
| 252 | `'ONG'` |
| 253 | `'('` |
| 254 | `'p'` |
| 255 | `');'` |
| 256 | `'\n\n'` |
| 262 | `'if'` |
| 263 | `'('` |
| 264 | `'char'` |
| 265 | `'_'` |
| 266 | `'code'` |
| 267 | `'<'` |
| 268 | `'start'` |
| 269 | `')'` |
| 270 | `'\n'` |
| 278 | `'break'` |
| 279 | `';'` |
| 280 | `'\n\n'` |
| 286 | `'if'` |
| 287 | `'('` |
| 288 | `'char'` |
| 289 | `'_'` |
| 290 | `'code'` |
| 291 | `'<='` |
| 292 | `'end'` |
| 293 | `')'` |
| 294 | `'\n'` |
| 300 | `'{'` |
| 301 | `'\n'` |
| 309 | `'if'` |
| 310 | `'('` |
| 311 | `'start'` |
| 312 | `'_'` |
| 313 | `'id'` |
| 314 | `'>'` |
| 315 | `'0'` |
| 316 | `'x'` |
| 317 | `'FFFF'` |
| 318 | `'FFFF'` |
| 319 | `'UL'` |
| 320 | `'-'` |
| 321 | `'('` |
| 322 | `'char'` |
| 323 | `'_'` |
| 324 | `'code'` |
| 325 | `'-'` |
| 326 | `'start'` |
| 327 | `')'` |
| 328 | `')'` |
| 329 | `'\n'` |
| 339 | `'return'` |
| 340 | `'0'` |
| 341 | `';'` |
| 342 | `'\n\n'` |
| 350 | `'result'` |
| 351 | `'='` |
| 352 | `'('` |
| 353 | `'FT'` |
| 354 | `'_'` |
| 355 | `'U'` |
| 356 | `'Int'` |
| 357 | `')('` |
| 358 | `'start'` |
| 359 | `'_'` |
| 360 | `'id'` |
| 361 | `'+'` |
| 362 | `'('` |
| 363 | `'char'` |
| 364 | `'_'` |
| 365 | `'code'` |
| 366 | `'-'` |
| 367 | `'start'` |
| 368 | `')'` |
| 369 | `');'` |
| 370 | `'\n'` |
| 378 | `'break'` |
| 379 | `';'` |
| 380 | `'\n'` |
| 386 | `'}'` |
| 387 | `'\n'` |
| 391 | `'}'` |
| 392 | `'\n'` |
| 396 | `'return'` |
| 397 | `'result'` |
| 398 | `';'` |
| 399 | `'\n'` |
| 401 | `'}'` |
| 402 | `'\n'` |
