# Review 04: `primevul:original:166363` (cpp)

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
   1 | ActivateKeyboardGrab(DeviceIntPtr keybd, GrabPtr grab, TimeStamp time,
   2 |                      Bool passive)
   3 | {
   4 |     GrabInfoPtr grabinfo = &keybd->deviceGrab;
   5 |     GrabPtr oldgrab = grabinfo->grab;
   6 |     WindowPtr oldWin;
   7 | 
   8 |     /* slave devices need to float for the duration of the grab. */
   9 |     if (grab->grabtype == XI2 && keybd->enabled &&
  10 |         !(passive & ImplicitGrabMask) && !IsMaster(keybd))
  11 |         DetachFromMaster(keybd);
  12 | 
  13 |     if (!keybd->enabled)
  14 |         oldWin = NULL;
  15 |     else if (grabinfo->grab)
  16 |         oldWin = grabinfo->grab->window;
  17 |     else if (keybd->focus)
  18 |         oldWin = keybd->focus->win;
  19 |     else
  20 |         oldWin = keybd->spriteInfo->sprite->win;
  21 |     if (oldWin == FollowKeyboardWin)
  22 |         oldWin = keybd->focus->win;
  23 |     if (keybd->valuator)
  24 |         keybd->valuator->motionHintWindow = NullWindow;
  25 |     if (oldWin)
  26 |         DoFocusEvents(keybd, oldWin, grab->window, NotifyGrab);
  27 |     if (syncEvents.playingEvents)
  28 |         grabinfo->grabTime = syncEvents.time;
  29 |     else
  30 |         grabinfo->grabTime = time;
  31 |     grabinfo->grab = AllocGrab(grab);
  32 |     grabinfo->fromPassiveGrab = passive;
  33 |     grabinfo->implicitGrab = passive & ImplicitGrabMask;
  34 |     CheckGrabForSyncs(keybd, (Bool) grab->keyboardMode,
  35 |                       (Bool) grab->pointerMode);
  36 |     if (oldgrab)
  37 |         FreeGrab(oldgrab);
  38 | }
  39 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `ActivateKeyboardGrab` | 1:1 |
| 2 | `DeviceIntPtr` | 1:22 |
| 3 | `keybd` | 1:35 |
| 5 | `GrabPtr` | 1:42 |
| 6 | `grab` | 1:50 |
| 8 | `TimeStamp` | 1:56 |
| 9 | `time` | 1:66 |
| 11 | `Bool` | 2:22 |
| 12 | `passive` | 2:27 |
| 15 | `GrabInfoPtr` | 4:5 |
| 16 | `grabinfo` | 4:17 |
| 19 | `keybd` | 4:29 |
| 21 | `deviceGrab` | 4:36 |
| 23 | `GrabPtr` | 5:5 |
| 24 | `oldgrab` | 5:13 |
| 26 | `grabinfo` | 5:23 |
| 28 | `grab` | 5:33 |
| 30 | `WindowPtr` | 6:5 |
| 31 | `oldWin` | 6:15 |
| 33 | `if` | 9:5 |
| 35 | `grab` | 9:9 |
| 37 | `grabtype` | 9:15 |
| 39 | `XI2` | 9:27 |
| 41 | `keybd` | 9:34 |
| 43 | `enabled` | 9:41 |
| 47 | `passive` | 10:11 |
| 49 | `ImplicitGrabMask` | 10:21 |
| 53 | `IsMaster` | 10:43 |
| 55 | `keybd` | 10:52 |
| 58 | `DetachFromMaster` | 11:9 |
| 60 | `keybd` | 11:26 |
| 63 | `if` | 13:5 |
| 66 | `keybd` | 13:10 |
| 68 | `enabled` | 13:17 |
| 70 | `oldWin` | 14:9 |
| 72 | `NULL` | 14:18 |
| 74 | `else` | 15:5 |
| 75 | `if` | 15:10 |
| 77 | `grabinfo` | 15:14 |
| 79 | `grab` | 15:24 |
| 81 | `oldWin` | 16:9 |
| 83 | `grabinfo` | 16:18 |
| 85 | `grab` | 16:28 |
| 87 | `window` | 16:34 |
| 89 | `else` | 17:5 |
| 90 | `if` | 17:10 |
| 92 | `keybd` | 17:14 |
| 94 | `focus` | 17:21 |
| 96 | `oldWin` | 18:9 |
| 98 | `keybd` | 18:18 |
| 100 | `focus` | 18:25 |
| 102 | `win` | 18:32 |
| 104 | `else` | 19:5 |
| 105 | `oldWin` | 20:9 |
| 107 | `keybd` | 20:18 |
| 109 | `spriteInfo` | 20:25 |
| 111 | `sprite` | 20:37 |
| 113 | `win` | 20:45 |
| 115 | `if` | 21:5 |
| 117 | `oldWin` | 21:9 |
| 119 | `FollowKeyboardWin` | 21:19 |
| 121 | `oldWin` | 22:9 |
| 123 | `keybd` | 22:18 |
| 125 | `focus` | 22:25 |
| 127 | `win` | 22:32 |
| 129 | `if` | 23:5 |
| 131 | `keybd` | 23:9 |
| 133 | `valuator` | 23:16 |
| 135 | `keybd` | 24:9 |
| 137 | `valuator` | 24:16 |
| 139 | `motionHintWindow` | 24:26 |
| 141 | `NullWindow` | 24:45 |
| 143 | `if` | 25:5 |
| 145 | `oldWin` | 25:9 |
| 147 | `DoFocusEvents` | 26:9 |
| 149 | `keybd` | 26:23 |
| 151 | `oldWin` | 26:30 |
| 153 | `grab` | 26:38 |
| 155 | `window` | 26:44 |
| 157 | `NotifyGrab` | 26:52 |
| 160 | `if` | 27:5 |
| 162 | `syncEvents` | 27:9 |
| 164 | `playingEvents` | 27:20 |
| 166 | `grabinfo` | 28:9 |
| 168 | `grabTime` | 28:19 |
| 170 | `syncEvents` | 28:30 |
| 172 | `time` | 28:41 |
| 174 | `else` | 29:5 |
| 175 | `grabinfo` | 30:9 |
| 177 | `grabTime` | 30:19 |
| 179 | `time` | 30:30 |
| 181 | `grabinfo` | 31:5 |
| 183 | `grab` | 31:15 |
| 185 | `AllocGrab` | 31:22 |
| 187 | `grab` | 31:32 |
| 190 | `grabinfo` | 32:5 |
| 192 | `fromPassiveGrab` | 32:15 |
| 194 | `passive` | 32:33 |
| 196 | `grabinfo` | 33:5 |
| 198 | `implicitGrab` | 33:15 |
| 200 | `passive` | 33:30 |
| 202 | `ImplicitGrabMask` | 33:40 |
| 204 | `CheckGrabForSyncs` | 34:5 |
| 206 | `keybd` | 34:23 |
| 209 | `Bool` | 34:31 |
| 211 | `grab` | 34:37 |
| 213 | `keyboardMode` | 34:43 |
| 216 | `Bool` | 35:24 |
| 218 | `grab` | 35:30 |
| 220 | `pointerMode` | 35:36 |
| 223 | `if` | 36:5 |
| 225 | `oldgrab` | 36:9 |
| 227 | `FreeGrab` | 37:9 |
| 229 | `oldgrab` | 37:18 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'Activ'` |
| 2 | `'ate'` |
| 3 | `'Key'` |
| 4 | `'board'` |
| 5 | `'Grab'` |
| 6 | `'('` |
| 7 | `'Device'` |
| 8 | `'Int'` |
| 9 | `'Ptr'` |
| 10 | `'key'` |
| 11 | `'bd'` |
| 12 | `','` |
| 13 | `'Grab'` |
| 14 | `'Ptr'` |
| 15 | `'grab'` |
| 16 | `','` |
| 17 | `'Time'` |
| 18 | `'St'` |
| 19 | `'amp'` |
| 20 | `'time'` |
| 21 | `','` |
| 22 | `'\n'` |
| 43 | `'B'` |
| 44 | `'ool'` |
| 45 | `'passive'` |
| 46 | `')'` |
| 47 | `'\n'` |
| 48 | `'{'` |
| 49 | `'\n'` |
| 53 | `'Grab'` |
| 54 | `'Info'` |
| 55 | `'Ptr'` |
| 56 | `'grab'` |
| 57 | `'info'` |
| 58 | `'='` |
| 59 | `'&'` |
| 60 | `'key'` |
| 61 | `'bd'` |
| 62 | `'->'` |
| 63 | `'device'` |
| 64 | `'Grab'` |
| 65 | `';'` |
| 66 | `'\n'` |
| 70 | `'Grab'` |
| 71 | `'Ptr'` |
| 72 | `'old'` |
| 73 | `'grab'` |
| 74 | `'='` |
| 75 | `'grab'` |
| 76 | `'info'` |
| 77 | `'->'` |
| 78 | `'grab'` |
| 79 | `';'` |
| 80 | `'\n'` |
| 84 | `'Window'` |
| 85 | `'Ptr'` |
| 86 | `'old'` |
| 87 | `'Win'` |
| 88 | `';'` |
| 89 | `'\n\n'` |
| 93 | `'/*'` |
| 94 | `'slave'` |
| 95 | `'devices'` |
| 96 | `'need'` |
| 97 | `'to'` |
| 98 | `'float'` |
| 99 | `'for'` |
| 100 | `'the'` |
| 101 | `'duration'` |
| 102 | `'of'` |
| 103 | `'the'` |
| 104 | `'grab'` |
| 105 | `'.'` |
| 106 | `'*/'` |
| 107 | `'\n'` |
| 111 | `'if'` |
| 112 | `'('` |
| 113 | `'grab'` |
| 114 | `'->'` |
| 115 | `'grab'` |
| 116 | `'type'` |
| 117 | `'=='` |
| 118 | `'XI'` |
| 119 | `'2'` |
| 120 | `'&&'` |
| 121 | `'key'` |
| 122 | `'bd'` |
| 123 | `'->'` |
| 124 | `'enabled'` |
| 125 | `'&&'` |
| 126 | `'\n'` |
| 134 | `'!'` |
| 135 | `'('` |
| 136 | `'pass'` |
| 137 | `'ive'` |
| 138 | `'&'` |
| 139 | `'Impl'` |
| 140 | `'icit'` |
| 141 | `'Grab'` |
| 142 | `'Mask'` |
| 143 | `')'` |
| 144 | `'&&'` |
| 145 | `'!'` |
| 146 | `'Is'` |
| 147 | `'Master'` |
| 148 | `'('` |
| 149 | `'key'` |
| 150 | `'bd'` |
| 151 | `'))'` |
| 152 | `'\n'` |
| 160 | `'Det'` |
| 161 | `'ach'` |
| 162 | `'From'` |
| 163 | `'Master'` |
| 164 | `'('` |
| 165 | `'key'` |
| 166 | `'bd'` |
| 167 | `');'` |
| 168 | `'\n\n'` |
| 172 | `'if'` |
| 173 | `'(!'` |
| 174 | `'key'` |
| 175 | `'bd'` |
| 176 | `'->'` |
| 177 | `'enabled'` |
| 178 | `')'` |
| 179 | `'\n'` |
| 187 | `'old'` |
| 188 | `'Win'` |
| 189 | `'='` |
| 190 | `'NULL'` |
| 191 | `';'` |
| 192 | `'\n'` |
| 196 | `'else'` |
| 197 | `'if'` |
| 198 | `'('` |
| 199 | `'gr'` |
| 200 | `'abin'` |
| 201 | `'fo'` |
| 202 | `'->'` |
| 203 | `'grab'` |
| 204 | `')'` |
| 205 | `'\n'` |
| 213 | `'old'` |
| 214 | `'Win'` |
| 215 | `'='` |
| 216 | `'grab'` |
| 217 | `'info'` |
| 218 | `'->'` |
| 219 | `'grab'` |
| 220 | `'->'` |
| 221 | `'window'` |
| 222 | `';'` |
| 223 | `'\n'` |
| 227 | `'else'` |
| 228 | `'if'` |
| 229 | `'('` |
| 230 | `'key'` |
| 231 | `'bd'` |
| 232 | `'->'` |
| 233 | `'focus'` |
| 234 | `')'` |
| 235 | `'\n'` |
| 243 | `'old'` |
| 244 | `'Win'` |
| 245 | `'='` |
| 246 | `'key'` |
| 247 | `'bd'` |
| 248 | `'->'` |
| 249 | `'focus'` |
| 250 | `'->'` |
| 251 | `'win'` |
| 252 | `';'` |
| 253 | `'\n'` |
| 257 | `'else'` |
| 258 | `'\n'` |
| 266 | `'old'` |
| 267 | `'Win'` |
| 268 | `'='` |
| 269 | `'key'` |
| 270 | `'bd'` |
| 271 | `'->'` |
| 272 | `'spr'` |
| 273 | `'ite'` |
| 274 | `'Info'` |
| 275 | `'->'` |
| 276 | `'spr'` |
| 277 | `'ite'` |
| 278 | `'->'` |
| 279 | `'win'` |
| 280 | `';'` |
| 281 | `'\n'` |
| 285 | `'if'` |
| 286 | `'('` |
| 287 | `'old'` |
| 288 | `'Win'` |
| 289 | `'=='` |
| 290 | `'Follow'` |
| 291 | `'Key'` |
| 292 | `'board'` |
| 293 | `'Win'` |
| 294 | `')'` |
| 295 | `'\n'` |
| 303 | `'old'` |
| 304 | `'Win'` |
| 305 | `'='` |
| 306 | `'key'` |
| 307 | `'bd'` |
| 308 | `'->'` |
| 309 | `'focus'` |
| 310 | `'->'` |
| 311 | `'win'` |
| 312 | `';'` |
| 313 | `'\n'` |
| 317 | `'if'` |
| 318 | `'('` |
| 319 | `'key'` |
| 320 | `'bd'` |
| 321 | `'->'` |
| 322 | `'val'` |
| 323 | `'u'` |
| 324 | `'ator'` |
| 325 | `')'` |
| 326 | `'\n'` |
| 334 | `'key'` |
| 335 | `'bd'` |
| 336 | `'->'` |
| 337 | `'val'` |
| 338 | `'u'` |
| 339 | `'ator'` |
| 340 | `'->'` |
| 341 | `'motion'` |
| 342 | `'H'` |
| 343 | `'int'` |
| 344 | `'Window'` |
| 345 | `'='` |
| 346 | `'Null'` |
| 347 | `'Window'` |
| 348 | `';'` |
| 349 | `'\n'` |
| 353 | `'if'` |
| 354 | `'('` |
| 355 | `'old'` |
| 356 | `'Win'` |
| 357 | `')'` |
| 358 | `'\n'` |
| 366 | `'Do'` |
| 367 | `'Focus'` |
| 368 | `'Events'` |
| 369 | `'('` |
| 370 | `'key'` |
| 371 | `'bd'` |
| 372 | `','` |
| 373 | `'old'` |
| 374 | `'Win'` |
| 375 | `','` |
| 376 | `'grab'` |
| 377 | `'->'` |
| 378 | `'window'` |
| 379 | `','` |
| 380 | `'Not'` |
| 381 | `'ify'` |
| 382 | `'Grab'` |
| 383 | `');'` |
| 384 | `'\n'` |
| 388 | `'if'` |
| 389 | `'('` |
| 390 | `'sync'` |
| 391 | `'Events'` |
| 392 | `'.'` |
| 393 | `'playing'` |
| 394 | `'Events'` |
| 395 | `')'` |
| 396 | `'\n'` |
| 404 | `'grab'` |
| 405 | `'info'` |
| 406 | `'->'` |
| 407 | `'grab'` |
| 408 | `'Time'` |
| 409 | `'='` |
| 410 | `'sync'` |
| 411 | `'Events'` |
| 412 | `'.'` |
| 413 | `'time'` |
| 414 | `';'` |
| 415 | `'\n'` |
| 419 | `'else'` |
| 420 | `'\n'` |
| 428 | `'grab'` |
| 429 | `'info'` |
| 430 | `'->'` |
| 431 | `'grab'` |
| 432 | `'Time'` |
| 433 | `'='` |
| 434 | `'time'` |
| 435 | `';'` |
| 436 | `'\n'` |
| 440 | `'grab'` |
| 441 | `'info'` |
| 442 | `'->'` |
| 443 | `'grab'` |
| 444 | `'='` |
| 445 | `'All'` |
| 446 | `'oc'` |
| 447 | `'Grab'` |
| 448 | `'('` |
| 449 | `'grab'` |
| 450 | `');'` |
| 451 | `'\n'` |
| 455 | `'grab'` |
| 456 | `'info'` |
| 457 | `'->'` |
| 458 | `'from'` |
| 459 | `'Pass'` |
| 460 | `'ive'` |
| 461 | `'Grab'` |
| 462 | `'='` |
| 463 | `'passive'` |
| 464 | `';'` |
| 465 | `'\n'` |
| 469 | `'grab'` |
| 470 | `'info'` |
| 471 | `'->'` |
| 472 | `'impl'` |
| 473 | `'icit'` |
| 474 | `'Grab'` |
| 475 | `'='` |
| 476 | `'passive'` |
| 477 | `'&'` |
| 478 | `'Impl'` |
| 479 | `'icit'` |
| 480 | `'Grab'` |
| 481 | `'Mask'` |
| 482 | `';'` |
| 483 | `'\n'` |
| 487 | `'Check'` |
| 488 | `'Grab'` |
| 489 | `'For'` |
| 490 | `'Syn'` |
| 491 | `'cs'` |
| 492 | `'('` |
| 493 | `'key'` |
| 494 | `'bd'` |
| 495 | `','` |
| 496 | `'('` |
| 497 | `'B'` |
| 498 | `'ool'` |
| 499 | `')'` |
| 500 | `'grab'` |
| 501 | `'->'` |
| 502 | `'key'` |
| 503 | `'board'` |
| 504 | `'Mode'` |
| 505 | `','` |
| 506 | `'\n'` |
