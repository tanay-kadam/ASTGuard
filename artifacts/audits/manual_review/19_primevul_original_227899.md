# Review 19: `primevul:original:227899` (c)

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
   1 | static void S_AL_AllocateStreamChannel(int stream, int entityNum)
   2 | {
   3 |         srcHandle_t cursrc;
   4 |         ALuint alsrc;
   5 |         
   6 | 	if ((stream < 0) || (stream >= MAX_RAW_STREAMS))
   7 | 		return;
   8 | 
   9 |         if(entityNum >= 0)
  10 |         {
  11 |                 // This is a stream that tracks an entity
  12 |         	// Allocate a streamSource at normal priority
  13 |         	cursrc = S_AL_SrcAlloc(SRCPRI_ENTITY, entityNum, 0);
  14 |         	if(cursrc < 0)
  15 | 	        	return;
  16 | 
  17 |         	S_AL_SrcSetup(cursrc, -1, SRCPRI_ENTITY, entityNum, 0, qfalse);
  18 |         	alsrc = S_AL_SrcGet(cursrc);
  19 |         	srcList[cursrc].isTracking = qtrue;
  20 |         	srcList[cursrc].isStream = qtrue;
  21 |         }
  22 |         else
  23 |         {
  24 |                 // Unspatialized stream source
  25 | 
  26 |         	// Allocate a streamSource at high priority
  27 |         	cursrc = S_AL_SrcAlloc(SRCPRI_STREAM, -2, 0);
  28 |         	if(cursrc < 0)
  29 | 	        	return;
  30 | 
  31 |         	alsrc = S_AL_SrcGet(cursrc);
  32 | 
  33 |         	// Lock the streamSource so nobody else can use it, and get the raw streamSource
  34 |         	S_AL_SrcLock(cursrc);
  35 |         
  36 |         	// make sure that after unmuting the S_AL_Gain in S_Update() does not turn
  37 |         	// volume up prematurely for this source
  38 |         	srcList[cursrc].scaleGain = 0.0f;
  39 | 
  40 |         	// Set some streamSource parameters
  41 |         	qalSourcei (alsrc, AL_BUFFER,          0            );
  42 |         	qalSourcei (alsrc, AL_LOOPING,         AL_FALSE     );
  43 |         	qalSource3f(alsrc, AL_POSITION,        0.0, 0.0, 0.0);
  44 |         	qalSource3f(alsrc, AL_VELOCITY,        0.0, 0.0, 0.0);
  45 |         	qalSource3f(alsrc, AL_DIRECTION,       0.0, 0.0, 0.0);
  46 |         	qalSourcef (alsrc, AL_ROLLOFF_FACTOR,  0.0          );
  47 |         	qalSourcei (alsrc, AL_SOURCE_RELATIVE, AL_TRUE      );
  48 |         }
  49 | 
  50 |         streamSourceHandles[stream] = cursrc;
  51 |        	streamSources[stream] = alsrc;
  52 | 
  53 | 	streamNumBuffers[stream] = 0;
  54 | 	streamBufIndex[stream] = 0;
  55 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `void` | 1:8 |
| 2 | `S_AL_AllocateStreamChannel` | 1:13 |
| 4 | `int` | 1:40 |
| 5 | `stream` | 1:44 |
| 7 | `int` | 1:52 |
| 8 | `entityNum` | 1:56 |
| 11 | `srcHandle_t` | 3:9 |
| 12 | `cursrc` | 3:21 |
| 14 | `ALuint` | 4:9 |
| 15 | `alsrc` | 4:16 |
| 17 | `if` | 6:2 |
| 20 | `stream` | 6:7 |
| 26 | `stream` | 6:23 |
| 28 | `MAX_RAW_STREAMS` | 6:33 |
| 31 | `return` | 7:3 |
| 33 | `if` | 9:9 |
| 35 | `entityNum` | 9:12 |
| 40 | `cursrc` | 13:10 |
| 42 | `S_AL_SrcAlloc` | 13:19 |
| 44 | `SRCPRI_ENTITY` | 13:33 |
| 46 | `entityNum` | 13:48 |
| 51 | `if` | 14:10 |
| 53 | `cursrc` | 14:13 |
| 57 | `return` | 15:11 |
| 59 | `S_AL_SrcSetup` | 17:10 |
| 61 | `cursrc` | 17:24 |
| 66 | `SRCPRI_ENTITY` | 17:36 |
| 68 | `entityNum` | 17:51 |
| 72 | `qfalse` | 17:65 |
| 75 | `alsrc` | 18:10 |
| 77 | `S_AL_SrcGet` | 18:18 |
| 79 | `cursrc` | 18:30 |
| 82 | `srcList` | 19:10 |
| 84 | `cursrc` | 19:18 |
| 87 | `isTracking` | 19:26 |
| 89 | `qtrue` | 19:39 |
| 91 | `srcList` | 20:10 |
| 93 | `cursrc` | 20:18 |
| 96 | `isStream` | 20:26 |
| 98 | `qtrue` | 20:37 |
| 101 | `else` | 22:9 |
| 103 | `cursrc` | 27:10 |
| 105 | `S_AL_SrcAlloc` | 27:19 |
| 107 | `SRCPRI_STREAM` | 27:33 |
| 115 | `if` | 28:10 |
| 117 | `cursrc` | 28:13 |
| 121 | `return` | 29:11 |
| 123 | `alsrc` | 31:10 |
| 125 | `S_AL_SrcGet` | 31:18 |
| 127 | `cursrc` | 31:30 |
| 130 | `S_AL_SrcLock` | 34:10 |
| 132 | `cursrc` | 34:23 |
| 135 | `srcList` | 38:10 |
| 137 | `cursrc` | 38:18 |
| 140 | `scaleGain` | 38:26 |
| 144 | `qalSourcei` | 41:10 |
| 146 | `alsrc` | 41:22 |
| 148 | `AL_BUFFER` | 41:29 |
| 153 | `qalSourcei` | 42:10 |
| 155 | `alsrc` | 42:22 |
| 157 | `AL_LOOPING` | 42:29 |
| 159 | `AL_FALSE` | 42:49 |
| 162 | `qalSource3f` | 43:10 |
| 164 | `alsrc` | 43:22 |
| 166 | `AL_POSITION` | 43:29 |
| 175 | `qalSource3f` | 44:10 |
| 177 | `alsrc` | 44:22 |
| 179 | `AL_VELOCITY` | 44:29 |
| 188 | `qalSource3f` | 45:10 |
| 190 | `alsrc` | 45:22 |
| 192 | `AL_DIRECTION` | 45:29 |
| 201 | `qalSourcef` | 46:10 |
| 203 | `alsrc` | 46:22 |
| 205 | `AL_ROLLOFF_FACTOR` | 46:29 |
| 210 | `qalSourcei` | 47:10 |
| 212 | `alsrc` | 47:22 |
| 214 | `AL_SOURCE_RELATIVE` | 47:29 |
| 216 | `AL_TRUE` | 47:49 |
| 220 | `streamSourceHandles` | 50:9 |
| 222 | `stream` | 50:29 |
| 225 | `cursrc` | 50:39 |
| 227 | `streamSources` | 51:9 |
| 229 | `stream` | 51:23 |
| 232 | `alsrc` | 51:33 |
| 234 | `streamNumBuffers` | 53:2 |
| 236 | `stream` | 53:19 |
| 241 | `streamBufIndex` | 54:2 |
| 243 | `stream` | 54:17 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'void'` |
| 3 | `'S'` |
| 4 | `'_'` |
| 5 | `'AL'` |
| 6 | `'_'` |
| 7 | `'All'` |
| 8 | `'ocate'` |
| 9 | `'Stream'` |
| 10 | `'Channel'` |
| 11 | `'('` |
| 12 | `'int'` |
| 13 | `'stream'` |
| 14 | `','` |
| 15 | `'int'` |
| 16 | `'entity'` |
| 17 | `'Num'` |
| 18 | `')'` |
| 19 | `'\n'` |
| 20 | `'{'` |
| 21 | `'\n'` |
| 29 | `'src'` |
| 30 | `'Handle'` |
| 31 | `'_'` |
| 32 | `'t'` |
| 33 | `'cur'` |
| 34 | `'src'` |
| 35 | `';'` |
| 36 | `'\n'` |
| 44 | `'AL'` |
| 45 | `'uint'` |
| 46 | `'al'` |
| 47 | `'src'` |
| 48 | `';'` |
| 49 | `'\n'` |
| 58 | `'\n'` |
| 59 | `'\t'` |
| 60 | `'if'` |
| 61 | `'(('` |
| 62 | `'stream'` |
| 63 | `'<'` |
| 64 | `'0'` |
| 65 | `')'` |
| 66 | `'||'` |
| 67 | `'('` |
| 68 | `'stream'` |
| 69 | `'>='` |
| 70 | `'MAX'` |
| 71 | `'_'` |
| 72 | `'RAW'` |
| 73 | `'_'` |
| 74 | `'ST'` |
| 75 | `'REAM'` |
| 76 | `'S'` |
| 77 | `'))'` |
| 78 | `'\n'` |
| 79 | `'\t'` |
| 80 | `'\t'` |
| 81 | `'return'` |
| 82 | `';'` |
| 83 | `'\n\n'` |
| 91 | `'if'` |
| 92 | `'('` |
| 93 | `'entity'` |
| 94 | `'Num'` |
| 95 | `'>='` |
| 96 | `'0'` |
| 97 | `')'` |
| 98 | `'\n'` |
| 106 | `'{'` |
| 107 | `'\n'` |
| 123 | `'//'` |
| 124 | `'This'` |
| 125 | `'is'` |
| 126 | `'a'` |
| 127 | `'stream'` |
| 128 | `'that'` |
| 129 | `'tracks'` |
| 130 | `'an'` |
| 131 | `'entity'` |
| 132 | `'\n'` |
| 141 | `'\t'` |
| 142 | `'//'` |
| 143 | `'All'` |
| 144 | `'ocate'` |
| 145 | `'a'` |
| 146 | `'stream'` |
| 147 | `'Source'` |
| 148 | `'at'` |
| 149 | `'normal'` |
| 150 | `'priority'` |
| 151 | `'\n'` |
| 160 | `'\t'` |
| 161 | `'c'` |
| 162 | `'urs'` |
| 163 | `'rc'` |
| 164 | `'='` |
| 165 | `'S'` |
| 166 | `'_'` |
| 167 | `'AL'` |
| 168 | `'_'` |
| 169 | `'S'` |
| 170 | `'rc'` |
| 171 | `'All'` |
| 172 | `'oc'` |
| 173 | `'('` |
| 174 | `'S'` |
| 175 | `'RC'` |
| 176 | `'PR'` |
| 177 | `'I'` |
| 178 | `'_'` |
| 179 | `'ENT'` |
| 180 | `'ITY'` |
| 181 | `','` |
| 182 | `'entity'` |
| 183 | `'Num'` |
| 184 | `','` |
| 185 | `'0'` |
| 186 | `');'` |
| 187 | `'\n'` |
| 196 | `'\t'` |
| 197 | `'if'` |
| 198 | `'('` |
| 199 | `'c'` |
| 200 | `'urs'` |
| 201 | `'rc'` |
| 202 | `'<'` |
| 203 | `'0'` |
| 204 | `')'` |
| 205 | `'\n'` |
| 206 | `'\t'` |
| 215 | `'\t'` |
| 216 | `'return'` |
| 217 | `';'` |
| 218 | `'\n\n'` |
| 227 | `'\t'` |
| 228 | `'S'` |
| 229 | `'_'` |
| 230 | `'AL'` |
| 231 | `'_'` |
| 232 | `'S'` |
| 233 | `'rc'` |
| 234 | `'Setup'` |
| 235 | `'('` |
| 236 | `'c'` |
| 237 | `'urs'` |
| 238 | `'rc'` |
| 239 | `','` |
| 240 | `'-'` |
| 241 | `'1'` |
| 242 | `','` |
| 243 | `'S'` |
| 244 | `'RC'` |
| 245 | `'PR'` |
| 246 | `'I'` |
| 247 | `'_'` |
| 248 | `'ENT'` |
| 249 | `'ITY'` |
| 250 | `','` |
| 251 | `'entity'` |
| 252 | `'Num'` |
| 253 | `','` |
| 254 | `'0'` |
| 255 | `','` |
| 256 | `'q'` |
| 257 | `'false'` |
| 258 | `');'` |
| 259 | `'\n'` |
| 268 | `'\t'` |
| 269 | `'als'` |
| 270 | `'rc'` |
| 271 | `'='` |
| 272 | `'S'` |
| 273 | `'_'` |
| 274 | `'AL'` |
| 275 | `'_'` |
| 276 | `'S'` |
| 277 | `'rc'` |
| 278 | `'Get'` |
| 279 | `'('` |
| 280 | `'c'` |
| 281 | `'urs'` |
| 282 | `'rc'` |
| 283 | `');'` |
| 284 | `'\n'` |
| 293 | `'\t'` |
| 294 | `'src'` |
| 295 | `'List'` |
| 296 | `'['` |
| 297 | `'c'` |
| 298 | `'urs'` |
| 299 | `'rc'` |
| 300 | `'].'` |
| 301 | `'is'` |
| 302 | `'Tr'` |
| 303 | `'acking'` |
| 304 | `'='` |
| 305 | `'q'` |
| 306 | `'true'` |
| 307 | `';'` |
| 308 | `'\n'` |
| 317 | `'\t'` |
| 318 | `'src'` |
| 319 | `'List'` |
| 320 | `'['` |
| 321 | `'c'` |
| 322 | `'urs'` |
| 323 | `'rc'` |
| 324 | `'].'` |
| 325 | `'is'` |
| 326 | `'Stream'` |
| 327 | `'='` |
| 328 | `'q'` |
| 329 | `'true'` |
| 330 | `';'` |
| 331 | `'\n'` |
| 339 | `'}'` |
| 340 | `'\n'` |
| 348 | `'else'` |
| 349 | `'\n'` |
| 357 | `'{'` |
| 358 | `'\n'` |
| 374 | `'//'` |
| 375 | `'Un'` |
| 376 | `'sp'` |
| 377 | `'atial'` |
| 378 | `'ized'` |
| 379 | `'stream'` |
| 380 | `'source'` |
| 381 | `'\n\n'` |
| 390 | `'\t'` |
| 391 | `'//'` |
| 392 | `'All'` |
| 393 | `'ocate'` |
| 394 | `'a'` |
| 395 | `'stream'` |
| 396 | `'Source'` |
| 397 | `'at'` |
| 398 | `'high'` |
| 399 | `'priority'` |
| 400 | `'\n'` |
| 409 | `'\t'` |
| 410 | `'c'` |
| 411 | `'urs'` |
| 412 | `'rc'` |
| 413 | `'='` |
| 414 | `'S'` |
| 415 | `'_'` |
| 416 | `'AL'` |
| 417 | `'_'` |
| 418 | `'S'` |
| 419 | `'rc'` |
| 420 | `'All'` |
| 421 | `'oc'` |
| 422 | `'('` |
| 423 | `'S'` |
| 424 | `'RC'` |
| 425 | `'PR'` |
| 426 | `'I'` |
| 427 | `'_'` |
| 428 | `'ST'` |
| 429 | `'REAM'` |
| 430 | `','` |
| 431 | `'-'` |
| 432 | `'2'` |
| 433 | `','` |
| 434 | `'0'` |
| 435 | `');'` |
| 436 | `'\n'` |
| 445 | `'\t'` |
| 446 | `'if'` |
| 447 | `'('` |
| 448 | `'c'` |
| 449 | `'urs'` |
| 450 | `'rc'` |
| 451 | `'<'` |
| 452 | `'0'` |
| 453 | `')'` |
| 454 | `'\n'` |
| 455 | `'\t'` |
| 464 | `'\t'` |
| 465 | `'return'` |
| 466 | `';'` |
| 467 | `'\n\n'` |
| 476 | `'\t'` |
| 477 | `'als'` |
| 478 | `'rc'` |
| 479 | `'='` |
| 480 | `'S'` |
| 481 | `'_'` |
| 482 | `'AL'` |
| 483 | `'_'` |
| 484 | `'S'` |
| 485 | `'rc'` |
| 486 | `'Get'` |
| 487 | `'('` |
| 488 | `'c'` |
| 489 | `'urs'` |
| 490 | `'rc'` |
| 491 | `');'` |
| 492 | `'\n\n'` |
| 501 | `'\t'` |
| 502 | `'//'` |
| 503 | `'Lock'` |
| 504 | `'the'` |
| 505 | `'stream'` |
| 506 | `'Source'` |
| 507 | `'so'` |
| 508 | `'nobody'` |
| 509 | `'else'` |
| 510 | `'can'` |
