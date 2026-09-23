# Review 50: `primevul:original:440848` (cpp)

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
   1 | _asn1_get_octet_string (const unsigned char *der, asn1_node node, int *len)
   2 | {
   3 |   int len2, len3, counter, tot_len, indefinite;
   4 | 
   5 |   counter = 0;
   6 | 
   7 |   if (*(der - 1) & ASN1_CLASS_STRUCTURED)
   8 |     {
   9 |       tot_len = 0;
  10 |       indefinite = asn1_get_length_der (der, *len, &len3);
  11 |       if (indefinite < -1)
  12 | 	return ASN1_DER_ERROR;
  13 | 
  14 |       counter += len3;
  15 |       if (indefinite >= 0)
  16 | 	indefinite += len3;
  17 | 
  18 |       while (1)
  19 | 	{
  20 | 	  if (counter > (*len))
  21 | 	    return ASN1_DER_ERROR;
  22 | 
  23 | 	  if (indefinite == -1)
  24 | 	    {
  25 | 	      if ((der[counter] == 0) && (der[counter + 1] == 0))
  26 | 		{
  27 | 		  counter += 2;
  28 | 		  break;
  29 | 		}
  30 | 	    }
  31 | 	  else if (counter >= indefinite)
  32 | 	    break;
  33 | 
  34 | 	  if (der[counter] != ASN1_TAG_OCTET_STRING)
  35 | 	    return ASN1_DER_ERROR;
  36 | 
  37 | 	  counter++;
  38 | 
  39 | 	  len2 = asn1_get_length_der (der + counter, *len - counter, &len3);
  40 | 	  if (len2 <= 0)
  41 | 	    return ASN1_DER_ERROR;
  42 | 
  43 | 	  counter += len3 + len2;
  44 | 	  tot_len += len2;
  45 | 	}
  46 | 
  47 |       /* copy */
  48 |       if (node)
  49 | 	{
  50 | 	  unsigned char temp[ASN1_MAX_LENGTH_SIZE];
  51 | 	  int ret;
  52 | 
  53 | 	  len2 = sizeof (temp);
  54 | 
  55 | 	  asn1_length_der (tot_len, temp, &len2);
  56 | 	  _asn1_set_value (node, temp, len2);
  57 | 
  58 | 	  ret = _asn1_extract_der_octet (node, der, *len);
  59 | 	  if (ret != ASN1_SUCCESS)
  60 | 	    return ret;
  61 | 
  62 | 	}
  63 |     }
  64 |   else
  65 |     {				/* NOT STRUCTURED */
  66 |       len2 = asn1_get_length_der (der, *len, &len3);
  67 |       if (len2 < 0)
  68 | 	return ASN1_DER_ERROR;
  69 | 
  70 |       counter = len3 + len2;
  71 |       if (node)
  72 | 	_asn1_set_value (node, der, counter);
  73 |     }
  74 | 
  75 |   *len = counter;
  76 |   return ASN1_SUCCESS;
  77 | 
  78 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `_asn1_get_octet_string` | 1:1 |
| 2 | `const` | 1:25 |
| 3 | `unsigned` | 1:31 |
| 4 | `char` | 1:40 |
| 6 | `der` | 1:46 |
| 8 | `asn1_node` | 1:51 |
| 9 | `node` | 1:61 |
| 11 | `int` | 1:67 |
| 13 | `len` | 1:72 |
| 16 | `int` | 3:3 |
| 17 | `len2` | 3:7 |
| 19 | `len3` | 3:13 |
| 21 | `counter` | 3:19 |
| 23 | `tot_len` | 3:28 |
| 25 | `indefinite` | 3:37 |
| 27 | `counter` | 5:3 |
| 31 | `if` | 7:3 |
| 35 | `der` | 7:9 |
| 40 | `ASN1_CLASS_STRUCTURED` | 7:20 |
| 43 | `tot_len` | 9:7 |
| 47 | `indefinite` | 10:7 |
| 49 | `asn1_get_length_der` | 10:20 |
| 51 | `der` | 10:41 |
| 54 | `len` | 10:47 |
| 57 | `len3` | 10:53 |
| 60 | `if` | 11:7 |
| 62 | `indefinite` | 11:11 |
| 67 | `return` | 12:2 |
| 68 | `ASN1_DER_ERROR` | 12:9 |
| 70 | `counter` | 14:7 |
| 72 | `len3` | 14:18 |
| 74 | `if` | 15:7 |
| 76 | `indefinite` | 15:11 |
| 80 | `indefinite` | 16:2 |
| 82 | `len3` | 16:16 |
| 84 | `while` | 18:7 |
| 89 | `if` | 20:4 |
| 91 | `counter` | 20:8 |
| 95 | `len` | 20:20 |
| 98 | `return` | 21:6 |
| 99 | `ASN1_DER_ERROR` | 21:13 |
| 101 | `if` | 23:4 |
| 103 | `indefinite` | 23:8 |
| 109 | `if` | 25:8 |
| 112 | `der` | 25:13 |
| 114 | `counter` | 25:17 |
| 121 | `der` | 25:36 |
| 123 | `counter` | 25:40 |
| 132 | `counter` | 27:5 |
| 136 | `break` | 28:5 |
| 140 | `else` | 31:4 |
| 141 | `if` | 31:9 |
| 143 | `counter` | 31:13 |
| 145 | `indefinite` | 31:24 |
| 147 | `break` | 32:6 |
| 149 | `if` | 34:4 |
| 151 | `der` | 34:8 |
| 153 | `counter` | 34:12 |
| 156 | `ASN1_TAG_OCTET_STRING` | 34:24 |
| 158 | `return` | 35:6 |
| 159 | `ASN1_DER_ERROR` | 35:13 |
| 161 | `counter` | 37:4 |
| 164 | `len2` | 39:4 |
| 166 | `asn1_get_length_der` | 39:11 |
| 168 | `der` | 39:32 |
| 170 | `counter` | 39:38 |
| 173 | `len` | 39:48 |
| 175 | `counter` | 39:54 |
| 178 | `len3` | 39:64 |
| 181 | `if` | 40:4 |
| 183 | `len2` | 40:8 |
| 187 | `return` | 41:6 |
| 188 | `ASN1_DER_ERROR` | 41:13 |
| 190 | `counter` | 43:4 |
| 192 | `len3` | 43:15 |
| 194 | `len2` | 43:22 |
| 196 | `tot_len` | 44:4 |
| 198 | `len2` | 44:15 |
| 201 | `if` | 48:7 |
| 203 | `node` | 48:11 |
| 206 | `unsigned` | 50:4 |
| 207 | `char` | 50:13 |
| 208 | `temp` | 50:18 |
| 210 | `ASN1_MAX_LENGTH_SIZE` | 50:23 |
| 213 | `int` | 51:4 |
| 214 | `ret` | 51:8 |
| 216 | `len2` | 53:4 |
| 218 | `sizeof` | 53:11 |
| 220 | `temp` | 53:19 |
| 223 | `asn1_length_der` | 55:4 |
| 225 | `tot_len` | 55:21 |
| 227 | `temp` | 55:30 |
| 230 | `len2` | 55:37 |
| 233 | `_asn1_set_value` | 56:4 |
| 235 | `node` | 56:21 |
| 237 | `temp` | 56:27 |
| 239 | `len2` | 56:33 |
| 242 | `ret` | 58:4 |
| 244 | `_asn1_extract_der_octet` | 58:10 |
| 246 | `node` | 58:35 |
| 248 | `der` | 58:41 |
| 251 | `len` | 58:47 |
| 254 | `if` | 59:4 |
| 256 | `ret` | 59:8 |
| 258 | `ASN1_SUCCESS` | 59:15 |
| 260 | `return` | 60:6 |
| 261 | `ret` | 60:13 |
| 265 | `else` | 64:3 |
| 267 | `len2` | 66:7 |
| 269 | `asn1_get_length_der` | 66:14 |
| 271 | `der` | 66:35 |
| 274 | `len` | 66:41 |
| 277 | `len3` | 66:47 |
| 280 | `if` | 67:7 |
| 282 | `len2` | 67:11 |
| 286 | `return` | 68:2 |
| 287 | `ASN1_DER_ERROR` | 68:9 |
| 289 | `counter` | 70:7 |
| 291 | `len3` | 70:17 |
| 293 | `len2` | 70:24 |
| 295 | `if` | 71:7 |
| 297 | `node` | 71:11 |
| 299 | `_asn1_set_value` | 72:2 |
| 301 | `node` | 72:19 |
| 303 | `der` | 72:25 |
| 305 | `counter` | 72:30 |
| 310 | `len` | 75:4 |
| 312 | `counter` | 75:10 |
| 314 | `return` | 76:3 |
| 315 | `ASN1_SUCCESS` | 76:10 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'_'` |
| 2 | `'as'` |
| 3 | `'n'` |
| 4 | `'1'` |
| 5 | `'_'` |
| 6 | `'get'` |
| 7 | `'_'` |
| 8 | `'oct'` |
| 9 | `'et'` |
| 10 | `'_'` |
| 11 | `'string'` |
| 12 | `'('` |
| 13 | `'const'` |
| 14 | `'unsigned'` |
| 15 | `'char'` |
| 16 | `'*'` |
| 17 | `'der'` |
| 18 | `','` |
| 19 | `'as'` |
| 20 | `'n'` |
| 21 | `'1'` |
| 22 | `'_'` |
| 23 | `'node'` |
| 24 | `'node'` |
| 25 | `','` |
| 26 | `'int'` |
| 27 | `'*'` |
| 28 | `'len'` |
| 29 | `')'` |
| 30 | `'\n'` |
| 31 | `'{'` |
| 32 | `'\n'` |
| 34 | `'int'` |
| 35 | `'len'` |
| 36 | `'2'` |
| 37 | `','` |
| 38 | `'len'` |
| 39 | `'3'` |
| 40 | `','` |
| 41 | `'counter'` |
| 42 | `','` |
| 43 | `'tot'` |
| 44 | `'_'` |
| 45 | `'len'` |
| 46 | `','` |
| 47 | `'indefinite'` |
| 48 | `';'` |
| 49 | `'\n\n'` |
| 51 | `'counter'` |
| 52 | `'='` |
| 53 | `'0'` |
| 54 | `';'` |
| 55 | `'\n\n'` |
| 57 | `'if'` |
| 58 | `'(*'` |
| 59 | `'('` |
| 60 | `'der'` |
| 61 | `'-'` |
| 62 | `'1'` |
| 63 | `')'` |
| 64 | `'&'` |
| 65 | `'AS'` |
| 66 | `'N'` |
| 67 | `'1'` |
| 68 | `'_'` |
| 69 | `'CLASS'` |
| 70 | `'_'` |
| 71 | `'STRUCT'` |
| 72 | `'UR'` |
| 73 | `'ED'` |
| 74 | `')'` |
| 75 | `'\n'` |
| 79 | `'{'` |
| 80 | `'\n'` |
| 86 | `'tot'` |
| 87 | `'_'` |
| 88 | `'len'` |
| 89 | `'='` |
| 90 | `'0'` |
| 91 | `';'` |
| 92 | `'\n'` |
| 98 | `'indefinite'` |
| 99 | `'='` |
| 100 | `'as'` |
| 101 | `'n'` |
| 102 | `'1'` |
| 103 | `'_'` |
| 104 | `'get'` |
| 105 | `'_'` |
| 106 | `'length'` |
| 107 | `'_'` |
| 108 | `'der'` |
| 109 | `'('` |
| 110 | `'der'` |
| 111 | `','` |
| 112 | `'*'` |
| 113 | `'len'` |
| 114 | `','` |
| 115 | `'&'` |
| 116 | `'len'` |
| 117 | `'3'` |
| 118 | `');'` |
| 119 | `'\n'` |
| 125 | `'if'` |
| 126 | `'('` |
| 127 | `'ind'` |
| 128 | `'ef'` |
| 129 | `'inite'` |
| 130 | `'<'` |
| 131 | `'-'` |
| 132 | `'1'` |
| 133 | `')'` |
| 134 | `'\n'` |
| 135 | `'\t'` |
| 136 | `'return'` |
| 137 | `'AS'` |
| 138 | `'N'` |
| 139 | `'1'` |
| 140 | `'_'` |
| 141 | `'DER'` |
| 142 | `'_'` |
| 143 | `'ERROR'` |
| 144 | `';'` |
| 145 | `'\n\n'` |
| 151 | `'counter'` |
| 152 | `'+='` |
| 153 | `'len'` |
| 154 | `'3'` |
| 155 | `';'` |
| 156 | `'\n'` |
| 162 | `'if'` |
| 163 | `'('` |
| 164 | `'ind'` |
| 165 | `'ef'` |
| 166 | `'inite'` |
| 167 | `'>='` |
| 168 | `'0'` |
| 169 | `')'` |
| 170 | `'\n'` |
| 171 | `'\t'` |
| 172 | `'ind'` |
| 173 | `'ef'` |
| 174 | `'inite'` |
| 175 | `'+='` |
| 176 | `'len'` |
| 177 | `'3'` |
| 178 | `';'` |
| 179 | `'\n\n'` |
| 185 | `'while'` |
| 186 | `'('` |
| 187 | `'1'` |
| 188 | `')'` |
| 189 | `'\n'` |
| 190 | `'\t'` |
| 191 | `'{'` |
| 192 | `'\n'` |
| 193 | `'\t'` |
| 195 | `'if'` |
| 196 | `'('` |
| 197 | `'counter'` |
| 198 | `'>'` |
| 199 | `'(*'` |
| 200 | `'len'` |
| 201 | `'))'` |
| 202 | `'\n'` |
| 203 | `'\t'` |
| 207 | `'return'` |
| 208 | `'AS'` |
| 209 | `'N'` |
| 210 | `'1'` |
| 211 | `'_'` |
| 212 | `'DER'` |
| 213 | `'_'` |
| 214 | `'ERROR'` |
| 215 | `';'` |
| 216 | `'\n\n'` |
| 217 | `'\t'` |
| 219 | `'if'` |
| 220 | `'('` |
| 221 | `'ind'` |
| 222 | `'ef'` |
| 223 | `'inite'` |
| 224 | `'=='` |
| 225 | `'-'` |
| 226 | `'1'` |
| 227 | `')'` |
| 228 | `'\n'` |
| 229 | `'\t'` |
| 233 | `'{'` |
| 234 | `'\n'` |
| 235 | `'\t'` |
| 241 | `'if'` |
| 242 | `'(('` |
| 243 | `'der'` |
| 244 | `'['` |
| 245 | `'counter'` |
| 246 | `']'` |
| 247 | `'=='` |
| 248 | `'0'` |
| 249 | `')'` |
| 250 | `'&&'` |
| 251 | `'('` |
| 252 | `'der'` |
| 253 | `'['` |
| 254 | `'counter'` |
| 255 | `'+'` |
| 256 | `'1'` |
| 257 | `']'` |
| 258 | `'=='` |
| 259 | `'0'` |
| 260 | `'))'` |
| 261 | `'\n'` |
| 262 | `'\t'` |
| 263 | `'\t'` |
| 264 | `'{'` |
| 265 | `'\n'` |
| 266 | `'\t'` |
| 267 | `'\t'` |
| 269 | `'counter'` |
| 270 | `'+='` |
| 271 | `'2'` |
| 272 | `';'` |
| 273 | `'\n'` |
| 274 | `'\t'` |
| 275 | `'\t'` |
| 277 | `'break'` |
| 278 | `';'` |
| 279 | `'\n'` |
| 280 | `'\t'` |
| 281 | `'\t'` |
| 282 | `'}'` |
| 283 | `'\n'` |
| 284 | `'\t'` |
| 288 | `'}'` |
| 289 | `'\n'` |
| 290 | `'\t'` |
| 292 | `'else'` |
| 293 | `'if'` |
| 294 | `'('` |
| 295 | `'counter'` |
| 296 | `'>='` |
| 297 | `'indefinite'` |
| 298 | `')'` |
| 299 | `'\n'` |
| 300 | `'\t'` |
| 304 | `'break'` |
| 305 | `';'` |
| 306 | `'\n\n'` |
| 307 | `'\t'` |
| 309 | `'if'` |
| 310 | `'('` |
| 311 | `'der'` |
| 312 | `'['` |
| 313 | `'counter'` |
| 314 | `']'` |
| 315 | `'!='` |
| 316 | `'AS'` |
| 317 | `'N'` |
| 318 | `'1'` |
| 319 | `'_'` |
| 320 | `'TAG'` |
| 321 | `'_'` |
| 322 | `'O'` |
| 323 | `'CT'` |
| 324 | `'ET'` |
| 325 | `'_'` |
| 326 | `'STR'` |
| 327 | `'ING'` |
| 328 | `')'` |
| 329 | `'\n'` |
| 330 | `'\t'` |
| 334 | `'return'` |
| 335 | `'AS'` |
| 336 | `'N'` |
| 337 | `'1'` |
| 338 | `'_'` |
| 339 | `'DER'` |
| 340 | `'_'` |
| 341 | `'ERROR'` |
| 342 | `';'` |
| 343 | `'\n\n'` |
| 344 | `'\t'` |
| 346 | `'counter'` |
| 347 | `'++;'` |
| 348 | `'\n\n'` |
| 349 | `'\t'` |
| 351 | `'len'` |
| 352 | `'2'` |
| 353 | `'='` |
| 354 | `'as'` |
| 355 | `'n'` |
| 356 | `'1'` |
| 357 | `'_'` |
| 358 | `'get'` |
| 359 | `'_'` |
| 360 | `'length'` |
| 361 | `'_'` |
| 362 | `'der'` |
| 363 | `'('` |
| 364 | `'der'` |
| 365 | `'+'` |
| 366 | `'counter'` |
| 367 | `','` |
| 368 | `'*'` |
| 369 | `'len'` |
| 370 | `'-'` |
| 371 | `'counter'` |
| 372 | `','` |
| 373 | `'&'` |
| 374 | `'len'` |
| 375 | `'3'` |
| 376 | `');'` |
| 377 | `'\n'` |
| 378 | `'\t'` |
| 380 | `'if'` |
| 381 | `'('` |
| 382 | `'len'` |
| 383 | `'2'` |
| 384 | `'<='` |
| 385 | `'0'` |
| 386 | `')'` |
| 387 | `'\n'` |
| 388 | `'\t'` |
| 392 | `'return'` |
| 393 | `'AS'` |
| 394 | `'N'` |
| 395 | `'1'` |
| 396 | `'_'` |
| 397 | `'DER'` |
| 398 | `'_'` |
| 399 | `'ERROR'` |
| 400 | `';'` |
| 401 | `'\n\n'` |
| 402 | `'\t'` |
| 404 | `'counter'` |
| 405 | `'+='` |
| 406 | `'len'` |
| 407 | `'3'` |
| 408 | `'+'` |
| 409 | `'len'` |
| 410 | `'2'` |
| 411 | `';'` |
| 412 | `'\n'` |
| 413 | `'\t'` |
| 415 | `'tot'` |
| 416 | `'_'` |
| 417 | `'len'` |
| 418 | `'+='` |
| 419 | `'len'` |
| 420 | `'2'` |
| 421 | `';'` |
| 422 | `'\n'` |
| 423 | `'\t'` |
| 424 | `'}'` |
| 425 | `'\n\n'` |
| 431 | `'/*'` |
| 432 | `'copy'` |
| 433 | `'*/'` |
| 434 | `'\n'` |
| 440 | `'if'` |
| 441 | `'('` |
| 442 | `'node'` |
| 443 | `')'` |
| 444 | `'\n'` |
| 445 | `'\t'` |
| 446 | `'{'` |
| 447 | `'\n'` |
| 448 | `'\t'` |
| 450 | `'unsigned'` |
| 451 | `'char'` |
| 452 | `'temp'` |
| 453 | `'['` |
| 454 | `'AS'` |
| 455 | `'N'` |
| 456 | `'1'` |
| 457 | `'_'` |
| 458 | `'MAX'` |
| 459 | `'_'` |
| 460 | `'L'` |
| 461 | `'ENGTH'` |
| 462 | `'_'` |
| 463 | `'SIZE'` |
| 464 | `'];'` |
| 465 | `'\n'` |
| 466 | `'\t'` |
| 468 | `'int'` |
| 469 | `'ret'` |
| 470 | `';'` |
| 471 | `'\n\n'` |
| 472 | `'\t'` |
| 474 | `'len'` |
| 475 | `'2'` |
| 476 | `'='` |
| 477 | `'sizeof'` |
| 478 | `'('` |
| 479 | `'temp'` |
| 480 | `');'` |
| 481 | `'\n\n'` |
| 482 | `'\t'` |
| 484 | `'as'` |
| 485 | `'n'` |
| 486 | `'1'` |
| 487 | `'_'` |
| 488 | `'length'` |
| 489 | `'_'` |
| 490 | `'der'` |
| 491 | `'('` |
| 492 | `'t'` |
| 493 | `'ot'` |
| 494 | `'_'` |
| 495 | `'len'` |
| 496 | `','` |
| 497 | `'temp'` |
| 498 | `','` |
| 499 | `'&'` |
| 500 | `'len'` |
| 501 | `'2'` |
| 502 | `');'` |
| 503 | `'\n'` |
| 504 | `'\t'` |
| 506 | `'_'` |
| 507 | `'as'` |
| 508 | `'n'` |
| 509 | `'1'` |
| 510 | `'_'` |
