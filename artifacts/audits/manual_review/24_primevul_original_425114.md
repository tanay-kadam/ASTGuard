# Review 24: `primevul:original:425114` (cpp)

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
   1 | bool ValidateSHARK()
   2 | {
   3 | 	std::cout << "\nSHARK validation suite running...\n\n";
   4 | 	bool pass1 = true, pass2 = true;
   5 | 
   6 | 	SHARKEncryption enc;  // 128-bit only
   7 | 	pass1 = SHARKEncryption::KEYLENGTH ==  16 && pass1;
   8 | 	pass1 = enc.StaticGetValidKeyLength(8) == 16 && pass1;
   9 | 	pass1 = enc.StaticGetValidKeyLength(15) == 16 && pass1;
  10 | 	pass1 = enc.StaticGetValidKeyLength(16) == 16 && pass1;
  11 | 	pass1 = enc.StaticGetValidKeyLength(17) == 16 && pass1;
  12 | 	pass1 = enc.StaticGetValidKeyLength(32) == 16 && pass1;
  13 | 
  14 | 	SHARKDecryption dec;  // 128-bit only
  15 | 	pass2 = SHARKDecryption::KEYLENGTH ==  16 && pass2;
  16 | 	pass2 = dec.StaticGetValidKeyLength(8) == 16 && pass2;
  17 | 	pass2 = dec.StaticGetValidKeyLength(15) == 16 && pass2;
  18 | 	pass2 = dec.StaticGetValidKeyLength(16) == 16 && pass2;
  19 | 	pass2 = dec.StaticGetValidKeyLength(17) == 16 && pass2;
  20 | 	pass2 = dec.StaticGetValidKeyLength(32) == 16 && pass2;
  21 | 	std::cout << (pass1 && pass2 ? "passed:" : "FAILED:") << "  Algorithm key lengths\n";
  22 | 
  23 | 	FileSource valdata(CRYPTOPP_DATA_DIR "TestData/sharkval.dat", true, new HexDecoder);
  24 | 	return BlockTransformationTest(FixedRoundsCipherFactory<SHARKEncryption, SHARKDecryption>(), valdata) && pass1 && pass2;
  25 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `bool` | 1:1 |
| 1 | `ValidateSHARK` | 1:6 |
| 5 | `std` | 3:2 |
| 7 | `cout` | 3:7 |
| 11 | `bool` | 4:2 |
| 12 | `pass1` | 4:7 |
| 14 | `true` | 4:15 |
| 16 | `pass2` | 4:21 |
| 18 | `true` | 4:29 |
| 20 | `SHARKEncryption` | 6:2 |
| 21 | `enc` | 6:18 |
| 23 | `pass1` | 7:2 |
| 25 | `SHARKEncryption` | 7:10 |
| 27 | `KEYLENGTH` | 7:27 |
| 31 | `pass1` | 7:47 |
| 33 | `pass1` | 8:2 |
| 35 | `enc` | 8:10 |
| 37 | `StaticGetValidKeyLength` | 8:14 |
| 44 | `pass1` | 8:50 |
| 46 | `pass1` | 9:2 |
| 48 | `enc` | 9:10 |
| 50 | `StaticGetValidKeyLength` | 9:14 |
| 57 | `pass1` | 9:51 |
| 59 | `pass1` | 10:2 |
| 61 | `enc` | 10:10 |
| 63 | `StaticGetValidKeyLength` | 10:14 |
| 70 | `pass1` | 10:51 |
| 72 | `pass1` | 11:2 |
| 74 | `enc` | 11:10 |
| 76 | `StaticGetValidKeyLength` | 11:14 |
| 83 | `pass1` | 11:51 |
| 85 | `pass1` | 12:2 |
| 87 | `enc` | 12:10 |
| 89 | `StaticGetValidKeyLength` | 12:14 |
| 96 | `pass1` | 12:51 |
| 98 | `SHARKDecryption` | 14:2 |
| 99 | `dec` | 14:18 |
| 101 | `pass2` | 15:2 |
| 103 | `SHARKDecryption` | 15:10 |
| 105 | `KEYLENGTH` | 15:27 |
| 109 | `pass2` | 15:47 |
| 111 | `pass2` | 16:2 |
| 113 | `dec` | 16:10 |
| 115 | `StaticGetValidKeyLength` | 16:14 |
| 122 | `pass2` | 16:50 |
| 124 | `pass2` | 17:2 |
| 126 | `dec` | 17:10 |
| 128 | `StaticGetValidKeyLength` | 17:14 |
| 135 | `pass2` | 17:51 |
| 137 | `pass2` | 18:2 |
| 139 | `dec` | 18:10 |
| 141 | `StaticGetValidKeyLength` | 18:14 |
| 148 | `pass2` | 18:51 |
| 150 | `pass2` | 19:2 |
| 152 | `dec` | 19:10 |
| 154 | `StaticGetValidKeyLength` | 19:14 |
| 161 | `pass2` | 19:51 |
| 163 | `pass2` | 20:2 |
| 165 | `dec` | 20:10 |
| 167 | `StaticGetValidKeyLength` | 20:14 |
| 174 | `pass2` | 20:51 |
| 176 | `std` | 21:2 |
| 178 | `cout` | 21:7 |
| 181 | `pass1` | 21:16 |
| 183 | `pass2` | 21:25 |
| 192 | `FileSource` | 23:2 |
| 193 | `valdata` | 23:13 |
| 195 | `CRYPTOPP_DATA_DIR` | 23:21 |
| 198 | `true` | 23:64 |
| 200 | `new` | 23:70 |
| 201 | `HexDecoder` | 23:74 |
| 204 | `return` | 24:2 |
| 205 | `BlockTransformationTest` | 24:9 |
| 207 | `FixedRoundsCipherFactory` | 24:33 |
| 209 | `SHARKEncryption` | 24:58 |
| 211 | `SHARKDecryption` | 24:75 |
| 216 | `valdata` | 24:95 |
| 219 | `pass1` | 24:107 |
| 221 | `pass2` | 24:116 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'bool'` |
| 2 | `'Val'` |
| 3 | `'idate'` |
| 4 | `'SH'` |
| 5 | `'ARK'` |
| 6 | `'()'` |
| 7 | `'\n'` |
| 8 | `'{'` |
| 9 | `'\n'` |
| 10 | `'\t'` |
| 11 | `'std'` |
| 12 | `'::'` |
| 13 | `'c'` |
| 14 | `'out'` |
| 15 | `'<<'` |
| 16 | `'"\\'` |
| 17 | `'n'` |
| 18 | `'SH'` |
| 19 | `'ARK'` |
| 20 | `'validation'` |
| 21 | `'suite'` |
| 22 | `'running'` |
| 23 | `'...'` |
| 24 | `'\\'` |
| 25 | `'n'` |
| 26 | `'\\'` |
| 27 | `'n'` |
| 28 | `'";'` |
| 29 | `'\n'` |
| 30 | `'\t'` |
| 31 | `'bool'` |
| 32 | `'pass'` |
| 33 | `'1'` |
| 34 | `'='` |
| 35 | `'true'` |
| 36 | `','` |
| 37 | `'pass'` |
| 38 | `'2'` |
| 39 | `'='` |
| 40 | `'true'` |
| 41 | `';'` |
| 42 | `'\n\n'` |
| 43 | `'\t'` |
| 44 | `'SH'` |
| 45 | `'ARK'` |
| 46 | `'Enc'` |
| 47 | `'ryption'` |
| 48 | `'enc'` |
| 49 | `';'` |
| 51 | `'//'` |
| 52 | `'128'` |
| 53 | `'-'` |
| 54 | `'bit'` |
| 55 | `'only'` |
| 56 | `'\n'` |
| 57 | `'\t'` |
| 58 | `'pass'` |
| 59 | `'1'` |
| 60 | `'='` |
| 61 | `'SH'` |
| 62 | `'ARK'` |
| 63 | `'Enc'` |
| 64 | `'ryption'` |
| 65 | `'::'` |
| 66 | `'KEY'` |
| 67 | `'L'` |
| 68 | `'ENGTH'` |
| 69 | `'=='` |
| 71 | `'16'` |
| 72 | `'&&'` |
| 73 | `'pass'` |
| 74 | `'1'` |
| 75 | `';'` |
| 76 | `'\n'` |
| 77 | `'\t'` |
| 78 | `'pass'` |
| 79 | `'1'` |
| 80 | `'='` |
| 81 | `'enc'` |
| 82 | `'.'` |
| 83 | `'Static'` |
| 84 | `'Get'` |
| 85 | `'Valid'` |
| 86 | `'Key'` |
| 87 | `'Length'` |
| 88 | `'('` |
| 89 | `'8'` |
| 90 | `')'` |
| 91 | `'=='` |
| 92 | `'16'` |
| 93 | `'&&'` |
| 94 | `'pass'` |
| 95 | `'1'` |
| 96 | `';'` |
| 97 | `'\n'` |
| 98 | `'\t'` |
| 99 | `'pass'` |
| 100 | `'1'` |
| 101 | `'='` |
| 102 | `'enc'` |
| 103 | `'.'` |
| 104 | `'Static'` |
| 105 | `'Get'` |
| 106 | `'Valid'` |
| 107 | `'Key'` |
| 108 | `'Length'` |
| 109 | `'('` |
| 110 | `'15'` |
| 111 | `')'` |
| 112 | `'=='` |
| 113 | `'16'` |
| 114 | `'&&'` |
| 115 | `'pass'` |
| 116 | `'1'` |
| 117 | `';'` |
| 118 | `'\n'` |
| 119 | `'\t'` |
| 120 | `'pass'` |
| 121 | `'1'` |
| 122 | `'='` |
| 123 | `'enc'` |
| 124 | `'.'` |
| 125 | `'Static'` |
| 126 | `'Get'` |
| 127 | `'Valid'` |
| 128 | `'Key'` |
| 129 | `'Length'` |
| 130 | `'('` |
| 131 | `'16'` |
| 132 | `')'` |
| 133 | `'=='` |
| 134 | `'16'` |
| 135 | `'&&'` |
| 136 | `'pass'` |
| 137 | `'1'` |
| 138 | `';'` |
| 139 | `'\n'` |
| 140 | `'\t'` |
| 141 | `'pass'` |
| 142 | `'1'` |
| 143 | `'='` |
| 144 | `'enc'` |
| 145 | `'.'` |
| 146 | `'Static'` |
| 147 | `'Get'` |
| 148 | `'Valid'` |
| 149 | `'Key'` |
| 150 | `'Length'` |
| 151 | `'('` |
| 152 | `'17'` |
| 153 | `')'` |
| 154 | `'=='` |
| 155 | `'16'` |
| 156 | `'&&'` |
| 157 | `'pass'` |
| 158 | `'1'` |
| 159 | `';'` |
| 160 | `'\n'` |
| 161 | `'\t'` |
| 162 | `'pass'` |
| 163 | `'1'` |
| 164 | `'='` |
| 165 | `'enc'` |
| 166 | `'.'` |
| 167 | `'Static'` |
| 168 | `'Get'` |
| 169 | `'Valid'` |
| 170 | `'Key'` |
| 171 | `'Length'` |
| 172 | `'('` |
| 173 | `'32'` |
| 174 | `')'` |
| 175 | `'=='` |
| 176 | `'16'` |
| 177 | `'&&'` |
| 178 | `'pass'` |
| 179 | `'1'` |
| 180 | `';'` |
| 181 | `'\n\n'` |
| 182 | `'\t'` |
| 183 | `'SH'` |
| 184 | `'ARK'` |
| 185 | `'Dec'` |
| 186 | `'ryption'` |
| 187 | `'dec'` |
| 188 | `';'` |
| 190 | `'//'` |
| 191 | `'128'` |
| 192 | `'-'` |
| 193 | `'bit'` |
| 194 | `'only'` |
| 195 | `'\n'` |
| 196 | `'\t'` |
| 197 | `'pass'` |
| 198 | `'2'` |
| 199 | `'='` |
| 200 | `'SH'` |
| 201 | `'ARK'` |
| 202 | `'Dec'` |
| 203 | `'ryption'` |
| 204 | `'::'` |
| 205 | `'KEY'` |
| 206 | `'L'` |
| 207 | `'ENGTH'` |
| 208 | `'=='` |
| 210 | `'16'` |
| 211 | `'&&'` |
| 212 | `'pass'` |
| 213 | `'2'` |
| 214 | `';'` |
| 215 | `'\n'` |
| 216 | `'\t'` |
| 217 | `'pass'` |
| 218 | `'2'` |
| 219 | `'='` |
| 220 | `'dec'` |
| 221 | `'.'` |
| 222 | `'Static'` |
| 223 | `'Get'` |
| 224 | `'Valid'` |
| 225 | `'Key'` |
| 226 | `'Length'` |
| 227 | `'('` |
| 228 | `'8'` |
| 229 | `')'` |
| 230 | `'=='` |
| 231 | `'16'` |
| 232 | `'&&'` |
| 233 | `'pass'` |
| 234 | `'2'` |
| 235 | `';'` |
| 236 | `'\n'` |
| 237 | `'\t'` |
| 238 | `'pass'` |
| 239 | `'2'` |
| 240 | `'='` |
| 241 | `'dec'` |
| 242 | `'.'` |
| 243 | `'Static'` |
| 244 | `'Get'` |
| 245 | `'Valid'` |
| 246 | `'Key'` |
| 247 | `'Length'` |
| 248 | `'('` |
| 249 | `'15'` |
| 250 | `')'` |
| 251 | `'=='` |
| 252 | `'16'` |
| 253 | `'&&'` |
| 254 | `'pass'` |
| 255 | `'2'` |
| 256 | `';'` |
| 257 | `'\n'` |
| 258 | `'\t'` |
| 259 | `'pass'` |
| 260 | `'2'` |
| 261 | `'='` |
| 262 | `'dec'` |
| 263 | `'.'` |
| 264 | `'Static'` |
| 265 | `'Get'` |
| 266 | `'Valid'` |
| 267 | `'Key'` |
| 268 | `'Length'` |
| 269 | `'('` |
| 270 | `'16'` |
| 271 | `')'` |
| 272 | `'=='` |
| 273 | `'16'` |
| 274 | `'&&'` |
| 275 | `'pass'` |
| 276 | `'2'` |
| 277 | `';'` |
| 278 | `'\n'` |
| 279 | `'\t'` |
| 280 | `'pass'` |
| 281 | `'2'` |
| 282 | `'='` |
| 283 | `'dec'` |
| 284 | `'.'` |
| 285 | `'Static'` |
| 286 | `'Get'` |
| 287 | `'Valid'` |
| 288 | `'Key'` |
| 289 | `'Length'` |
| 290 | `'('` |
| 291 | `'17'` |
| 292 | `')'` |
| 293 | `'=='` |
| 294 | `'16'` |
| 295 | `'&&'` |
| 296 | `'pass'` |
| 297 | `'2'` |
| 298 | `';'` |
| 299 | `'\n'` |
| 300 | `'\t'` |
| 301 | `'pass'` |
| 302 | `'2'` |
| 303 | `'='` |
| 304 | `'dec'` |
| 305 | `'.'` |
| 306 | `'Static'` |
| 307 | `'Get'` |
| 308 | `'Valid'` |
| 309 | `'Key'` |
| 310 | `'Length'` |
| 311 | `'('` |
| 312 | `'32'` |
| 313 | `')'` |
| 314 | `'=='` |
| 315 | `'16'` |
| 316 | `'&&'` |
| 317 | `'pass'` |
| 318 | `'2'` |
| 319 | `';'` |
| 320 | `'\n'` |
| 321 | `'\t'` |
| 322 | `'std'` |
| 323 | `'::'` |
| 324 | `'c'` |
| 325 | `'out'` |
| 326 | `'<<'` |
| 327 | `'('` |
| 328 | `'pass'` |
| 329 | `'1'` |
| 330 | `'&&'` |
| 331 | `'pass'` |
| 332 | `'2'` |
| 333 | `'?'` |
| 334 | `'"'` |
| 335 | `'pass'` |
| 336 | `'ed'` |
| 337 | `':"'` |
| 338 | `':'` |
| 339 | `'"'` |
| 340 | `'FA'` |
| 341 | `'IL'` |
| 342 | `'ED'` |
| 343 | `':'` |
| 344 | `'")'` |
| 345 | `'<<'` |
| 346 | `'"'` |
| 348 | `'Al'` |
| 349 | `'gorithm'` |
| 350 | `'key'` |
| 351 | `'lengths'` |
| 352 | `'\\'` |
| 353 | `'n'` |
| 354 | `'";'` |
| 355 | `'\n\n'` |
| 356 | `'\t'` |
| 357 | `'File'` |
| 358 | `'Source'` |
| 359 | `'val'` |
| 360 | `'data'` |
| 361 | `'('` |
| 362 | `'CR'` |
| 363 | `'Y'` |
| 364 | `'PT'` |
| 365 | `'OP'` |
| 366 | `'P'` |
| 367 | `'_'` |
| 368 | `'DATA'` |
| 369 | `'_'` |
| 370 | `'DIR'` |
| 371 | `'"'` |
| 372 | `'Test'` |
| 373 | `'Data'` |
| 374 | `'/'` |
| 375 | `'sh'` |
| 376 | `'ark'` |
| 377 | `'val'` |
| 378 | `'.'` |
| 379 | `'dat'` |
| 380 | `'",'` |
| 381 | `'true'` |
| 382 | `','` |
| 383 | `'new'` |
| 384 | `'Hex'` |
| 385 | `'Dec'` |
| 386 | `'oder'` |
| 387 | `');'` |
| 388 | `'\n'` |
| 389 | `'\t'` |
| 390 | `'return'` |
| 391 | `'Block'` |
| 392 | `'Trans'` |
| 393 | `'formation'` |
| 394 | `'Test'` |
| 395 | `'('` |
| 396 | `'Fixed'` |
| 397 | `'R'` |
| 398 | `'ounds'` |
| 399 | `'C'` |
| 400 | `'ipher'` |
| 401 | `'Factory'` |
| 402 | `'<'` |
| 403 | `'SH'` |
| 404 | `'ARK'` |
| 405 | `'Enc'` |
| 406 | `'ryption'` |
| 407 | `','` |
| 408 | `'SH'` |
| 409 | `'ARK'` |
| 410 | `'Dec'` |
| 411 | `'ryption'` |
| 412 | `'>'` |
| 413 | `'(),'` |
| 414 | `'val'` |
| 415 | `'data'` |
| 416 | `')'` |
| 417 | `'&&'` |
| 418 | `'pass'` |
| 419 | `'1'` |
| 420 | `'&&'` |
| 421 | `'pass'` |
| 422 | `'2'` |
| 423 | `';'` |
| 424 | `'\n'` |
| 425 | `'}'` |
| 426 | `'\r'` |
