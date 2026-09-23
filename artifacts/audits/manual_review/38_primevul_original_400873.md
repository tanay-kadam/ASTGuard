# Review 38: `primevul:original:400873` (c)

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
   1 | static void ttusb_dec_process_urb(struct urb *urb)
   2 | {
   3 | 	struct ttusb_dec *dec = urb->context;
   4 | 
   5 | 	if (!urb->status) {
   6 | 		int i;
   7 | 
   8 | 		for (i = 0; i < FRAMES_PER_ISO_BUF; i++) {
   9 | 			struct usb_iso_packet_descriptor *d;
  10 | 			u8 *b;
  11 | 			int length;
  12 | 			struct urb_frame *frame;
  13 | 
  14 | 			d = &urb->iso_frame_desc[i];
  15 | 			b = urb->transfer_buffer + d->offset;
  16 | 			length = d->actual_length;
  17 | 
  18 | 			if ((frame = kmalloc(sizeof(struct urb_frame),
  19 | 					     GFP_ATOMIC))) {
  20 | 				unsigned long flags;
  21 | 
  22 | 				memcpy(frame->data, b, length);
  23 | 				frame->length = length;
  24 | 
  25 | 				spin_lock_irqsave(&dec->urb_frame_list_lock,
  26 | 						     flags);
  27 | 				list_add_tail(&frame->urb_frame_list,
  28 | 					      &dec->urb_frame_list);
  29 | 				spin_unlock_irqrestore(&dec->urb_frame_list_lock,
  30 | 						       flags);
  31 | 
  32 | 				tasklet_schedule(&dec->urb_tasklet);
  33 | 			}
  34 | 		}
  35 | 	} else {
  36 | 		 /* -ENOENT is expected when unlinking urbs */
  37 | 		if (urb->status != -ENOENT)
  38 | 			dprintk("%s: urb error: %d\n", __func__,
  39 | 				urb->status);
  40 | 	}
  41 | 
  42 | 	if (dec->iso_stream_count)
  43 | 		usb_submit_urb(urb, GFP_ATOMIC);
  44 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `void` | 1:8 |
| 2 | `ttusb_dec_process_urb` | 1:13 |
| 4 | `struct` | 1:35 |
| 5 | `urb` | 1:42 |
| 7 | `urb` | 1:47 |
| 10 | `struct` | 3:2 |
| 11 | `ttusb_dec` | 3:9 |
| 13 | `dec` | 3:20 |
| 15 | `urb` | 3:26 |
| 17 | `context` | 3:31 |
| 19 | `if` | 5:2 |
| 22 | `urb` | 5:7 |
| 24 | `status` | 5:12 |
| 27 | `int` | 6:3 |
| 28 | `i` | 6:7 |
| 30 | `for` | 8:3 |
| 32 | `i` | 8:8 |
| 36 | `i` | 8:15 |
| 38 | `FRAMES_PER_ISO_BUF` | 8:19 |
| 40 | `i` | 8:39 |
| 44 | `struct` | 9:4 |
| 45 | `usb_iso_packet_descriptor` | 9:11 |
| 47 | `d` | 9:38 |
| 49 | `u8` | 10:4 |
| 51 | `b` | 10:8 |
| 53 | `int` | 11:4 |
| 54 | `length` | 11:8 |
| 56 | `struct` | 12:4 |
| 57 | `urb_frame` | 12:11 |
| 59 | `frame` | 12:22 |
| 61 | `d` | 14:4 |
| 64 | `urb` | 14:9 |
| 66 | `iso_frame_desc` | 14:14 |
| 68 | `i` | 14:29 |
| 71 | `b` | 15:4 |
| 73 | `urb` | 15:8 |
| 75 | `transfer_buffer` | 15:13 |
| 77 | `d` | 15:31 |
| 79 | `offset` | 15:34 |
| 81 | `length` | 16:4 |
| 83 | `d` | 16:13 |
| 85 | `actual_length` | 16:16 |
| 87 | `if` | 18:4 |
| 90 | `frame` | 18:9 |
| 92 | `kmalloc` | 18:17 |
| 94 | `sizeof` | 18:25 |
| 96 | `struct` | 18:32 |
| 97 | `urb_frame` | 18:39 |
| 100 | `GFP_ATOMIC` | 19:11 |
| 105 | `unsigned` | 20:5 |
| 106 | `long` | 20:14 |
| 107 | `flags` | 20:19 |
| 109 | `memcpy` | 22:5 |
| 111 | `frame` | 22:12 |
| 113 | `data` | 22:19 |
| 115 | `b` | 22:25 |
| 117 | `length` | 22:28 |
| 120 | `frame` | 23:5 |
| 122 | `length` | 23:12 |
| 124 | `length` | 23:21 |
| 126 | `spin_lock_irqsave` | 25:5 |
| 129 | `dec` | 25:24 |
| 131 | `urb_frame_list_lock` | 25:29 |
| 133 | `flags` | 26:12 |
| 136 | `list_add_tail` | 27:5 |
| 139 | `frame` | 27:20 |
| 141 | `urb_frame_list` | 27:27 |
| 144 | `dec` | 28:13 |
| 146 | `urb_frame_list` | 28:18 |
| 149 | `spin_unlock_irqrestore` | 29:5 |
| 152 | `dec` | 29:29 |
| 154 | `urb_frame_list_lock` | 29:34 |
| 156 | `flags` | 30:14 |
| 159 | `tasklet_schedule` | 32:5 |
| 162 | `dec` | 32:23 |
| 164 | `urb_tasklet` | 32:28 |
| 170 | `else` | 35:4 |
| 172 | `if` | 37:3 |
| 174 | `urb` | 37:7 |
| 176 | `status` | 37:12 |
| 179 | `ENOENT` | 37:23 |
| 181 | `dprintk` | 38:4 |
| 185 | `__func__` | 38:35 |
| 187 | `urb` | 39:5 |
| 189 | `status` | 39:10 |
| 193 | `if` | 42:2 |
| 195 | `dec` | 42:6 |
| 197 | `iso_stream_count` | 42:11 |
| 199 | `usb_submit_urb` | 43:3 |
| 201 | `urb` | 43:18 |
| 203 | `GFP_ATOMIC` | 43:23 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'void'` |
| 3 | `'t'` |
| 4 | `'t'` |
| 5 | `'usb'` |
| 6 | `'_'` |
| 7 | `'dec'` |
| 8 | `'_'` |
| 9 | `'process'` |
| 10 | `'_'` |
| 11 | `'urb'` |
| 12 | `'('` |
| 13 | `'struct'` |
| 14 | `'ur'` |
| 15 | `'b'` |
| 16 | `'*'` |
| 17 | `'urb'` |
| 18 | `')'` |
| 19 | `'\n'` |
| 20 | `'{'` |
| 21 | `'\n'` |
| 22 | `'\t'` |
| 23 | `'struct'` |
| 24 | `'t'` |
| 25 | `'t'` |
| 26 | `'usb'` |
| 27 | `'_'` |
| 28 | `'dec'` |
| 29 | `'*'` |
| 30 | `'dec'` |
| 31 | `'='` |
| 32 | `'ur'` |
| 33 | `'b'` |
| 34 | `'->'` |
| 35 | `'context'` |
| 36 | `';'` |
| 37 | `'\n\n'` |
| 38 | `'\t'` |
| 39 | `'if'` |
| 40 | `'(!'` |
| 41 | `'urb'` |
| 42 | `'->'` |
| 43 | `'status'` |
| 44 | `')'` |
| 45 | `'{'` |
| 46 | `'\n'` |
| 47 | `'\t'` |
| 48 | `'\t'` |
| 49 | `'int'` |
| 50 | `'i'` |
| 51 | `';'` |
| 52 | `'\n\n'` |
| 53 | `'\t'` |
| 54 | `'\t'` |
| 55 | `'for'` |
| 56 | `'('` |
| 57 | `'i'` |
| 58 | `'='` |
| 59 | `'0'` |
| 60 | `';'` |
| 61 | `'i'` |
| 62 | `'<'` |
| 63 | `'FR'` |
| 64 | `'AMES'` |
| 65 | `'_'` |
| 66 | `'PER'` |
| 67 | `'_'` |
| 68 | `'ISO'` |
| 69 | `'_'` |
| 70 | `'BU'` |
| 71 | `'F'` |
| 72 | `';'` |
| 73 | `'i'` |
| 74 | `'++)'` |
| 75 | `'{'` |
| 76 | `'\n'` |
| 77 | `'\t'` |
| 78 | `'\t'` |
| 79 | `'\t'` |
| 80 | `'struct'` |
| 81 | `'usb'` |
| 82 | `'_'` |
| 83 | `'iso'` |
| 84 | `'_'` |
| 85 | `'pack'` |
| 86 | `'et'` |
| 87 | `'_'` |
| 88 | `'desc'` |
| 89 | `'ript'` |
| 90 | `'or'` |
| 91 | `'*'` |
| 92 | `'d'` |
| 93 | `';'` |
| 94 | `'\n'` |
| 95 | `'\t'` |
| 96 | `'\t'` |
| 97 | `'\t'` |
| 98 | `'u'` |
| 99 | `'8'` |
| 100 | `'*'` |
| 101 | `'b'` |
| 102 | `';'` |
| 103 | `'\n'` |
| 104 | `'\t'` |
| 105 | `'\t'` |
| 106 | `'\t'` |
| 107 | `'int'` |
| 108 | `'length'` |
| 109 | `';'` |
| 110 | `'\n'` |
| 111 | `'\t'` |
| 112 | `'\t'` |
| 113 | `'\t'` |
| 114 | `'struct'` |
| 115 | `'ur'` |
| 116 | `'b'` |
| 117 | `'_'` |
| 118 | `'frame'` |
| 119 | `'*'` |
| 120 | `'frame'` |
| 121 | `';'` |
| 122 | `'\n\n'` |
| 123 | `'\t'` |
| 124 | `'\t'` |
| 125 | `'\t'` |
| 126 | `'d'` |
| 127 | `'='` |
| 128 | `'&'` |
| 129 | `'urb'` |
| 130 | `'->'` |
| 131 | `'iso'` |
| 132 | `'_'` |
| 133 | `'frame'` |
| 134 | `'_'` |
| 135 | `'desc'` |
| 136 | `'['` |
| 137 | `'i'` |
| 138 | `'];'` |
| 139 | `'\n'` |
| 140 | `'\t'` |
| 141 | `'\t'` |
| 142 | `'\t'` |
| 143 | `'b'` |
| 144 | `'='` |
| 145 | `'ur'` |
| 146 | `'b'` |
| 147 | `'->'` |
| 148 | `'transfer'` |
| 149 | `'_'` |
| 150 | `'buffer'` |
| 151 | `'+'` |
| 152 | `'d'` |
| 153 | `'->'` |
| 154 | `'offset'` |
| 155 | `';'` |
| 156 | `'\n'` |
| 157 | `'\t'` |
| 158 | `'\t'` |
| 159 | `'\t'` |
| 160 | `'length'` |
| 161 | `'='` |
| 162 | `'d'` |
| 163 | `'->'` |
| 164 | `'actual'` |
| 165 | `'_'` |
| 166 | `'length'` |
| 167 | `';'` |
| 168 | `'\n\n'` |
| 169 | `'\t'` |
| 170 | `'\t'` |
| 171 | `'\t'` |
| 172 | `'if'` |
| 173 | `'(('` |
| 174 | `'frame'` |
| 175 | `'='` |
| 176 | `'km'` |
| 177 | `'alloc'` |
| 178 | `'('` |
| 179 | `'size'` |
| 180 | `'of'` |
| 181 | `'('` |
| 182 | `'struct'` |
| 183 | `'ur'` |
| 184 | `'b'` |
| 185 | `'_'` |
| 186 | `'frame'` |
| 187 | `'),'` |
| 188 | `'\n'` |
| 189 | `'\t'` |
| 190 | `'\t'` |
| 191 | `'\t'` |
| 192 | `'\t'` |
| 193 | `'\t'` |
| 198 | `'G'` |
| 199 | `'FP'` |
| 200 | `'_'` |
| 201 | `'AT'` |
| 202 | `'OM'` |
| 203 | `'IC'` |
| 204 | `')))'` |
| 205 | `'{'` |
| 206 | `'\n'` |
| 207 | `'\t'` |
| 208 | `'\t'` |
| 209 | `'\t'` |
| 210 | `'\t'` |
| 211 | `'unsigned'` |
| 212 | `'long'` |
| 213 | `'flags'` |
| 214 | `';'` |
| 215 | `'\n\n'` |
| 216 | `'\t'` |
| 217 | `'\t'` |
| 218 | `'\t'` |
| 219 | `'\t'` |
| 220 | `'mem'` |
| 221 | `'c'` |
| 222 | `'py'` |
| 223 | `'('` |
| 224 | `'frame'` |
| 225 | `'->'` |
| 226 | `'data'` |
| 227 | `','` |
| 228 | `'b'` |
| 229 | `','` |
| 230 | `'length'` |
| 231 | `');'` |
| 232 | `'\n'` |
| 233 | `'\t'` |
| 234 | `'\t'` |
| 235 | `'\t'` |
| 236 | `'\t'` |
| 237 | `'frame'` |
| 238 | `'->'` |
| 239 | `'length'` |
| 240 | `'='` |
| 241 | `'length'` |
| 242 | `';'` |
| 243 | `'\n\n'` |
| 244 | `'\t'` |
| 245 | `'\t'` |
| 246 | `'\t'` |
| 247 | `'\t'` |
| 248 | `'spin'` |
| 249 | `'_'` |
| 250 | `'lock'` |
| 251 | `'_'` |
| 252 | `'ir'` |
| 253 | `'q'` |
| 254 | `'save'` |
| 255 | `'(&'` |
| 256 | `'dec'` |
| 257 | `'->'` |
| 258 | `'urb'` |
| 259 | `'_'` |
| 260 | `'frame'` |
| 261 | `'_'` |
| 262 | `'list'` |
| 263 | `'_'` |
| 264 | `'lock'` |
| 265 | `','` |
| 266 | `'\n'` |
| 267 | `'\t'` |
| 268 | `'\t'` |
| 269 | `'\t'` |
| 270 | `'\t'` |
| 271 | `'\t'` |
| 272 | `'\t'` |
| 277 | `'flags'` |
| 278 | `');'` |
| 279 | `'\n'` |
| 280 | `'\t'` |
| 281 | `'\t'` |
| 282 | `'\t'` |
| 283 | `'\t'` |
| 284 | `'list'` |
| 285 | `'_'` |
| 286 | `'add'` |
| 287 | `'_'` |
| 288 | `'tail'` |
| 289 | `'(&'` |
| 290 | `'frame'` |
| 291 | `'->'` |
| 292 | `'urb'` |
| 293 | `'_'` |
| 294 | `'frame'` |
| 295 | `'_'` |
| 296 | `'list'` |
| 297 | `','` |
| 298 | `'\n'` |
| 299 | `'\t'` |
| 300 | `'\t'` |
| 301 | `'\t'` |
| 302 | `'\t'` |
| 303 | `'\t'` |
| 309 | `'&'` |
| 310 | `'dec'` |
| 311 | `'->'` |
| 312 | `'urb'` |
| 313 | `'_'` |
| 314 | `'frame'` |
| 315 | `'_'` |
| 316 | `'list'` |
| 317 | `');'` |
| 318 | `'\n'` |
| 319 | `'\t'` |
| 320 | `'\t'` |
| 321 | `'\t'` |
| 322 | `'\t'` |
| 323 | `'spin'` |
| 324 | `'_'` |
| 325 | `'un'` |
| 326 | `'lock'` |
| 327 | `'_'` |
| 328 | `'ir'` |
| 329 | `'q'` |
| 330 | `'rest'` |
| 331 | `'ore'` |
| 332 | `'(&'` |
| 333 | `'dec'` |
| 334 | `'->'` |
| 335 | `'urb'` |
| 336 | `'_'` |
| 337 | `'frame'` |
| 338 | `'_'` |
| 339 | `'list'` |
| 340 | `'_'` |
| 341 | `'lock'` |
| 342 | `','` |
| 343 | `'\n'` |
| 344 | `'\t'` |
| 345 | `'\t'` |
| 346 | `'\t'` |
| 347 | `'\t'` |
| 348 | `'\t'` |
| 349 | `'\t'` |
| 356 | `'flags'` |
| 357 | `');'` |
| 358 | `'\n\n'` |
| 359 | `'\t'` |
| 360 | `'\t'` |
| 361 | `'\t'` |
| 362 | `'\t'` |
| 363 | `'task'` |
| 364 | `'let'` |
| 365 | `'_'` |
| 366 | `'sche'` |
| 367 | `'dule'` |
| 368 | `'(&'` |
| 369 | `'dec'` |
| 370 | `'->'` |
| 371 | `'urb'` |
| 372 | `'_'` |
| 373 | `'task'` |
| 374 | `'let'` |
| 375 | `');'` |
| 376 | `'\n'` |
| 377 | `'\t'` |
| 378 | `'\t'` |
| 379 | `'\t'` |
| 380 | `'}'` |
| 381 | `'\n'` |
| 382 | `'\t'` |
| 383 | `'\t'` |
| 384 | `'}'` |
| 385 | `'\n'` |
| 386 | `'\t'` |
| 387 | `'}'` |
| 388 | `'else'` |
| 389 | `'{'` |
| 390 | `'\n'` |
| 391 | `'\t'` |
| 392 | `'\t'` |
| 393 | `'/*'` |
| 394 | `'-'` |
| 395 | `'EN'` |
| 396 | `'O'` |
| 397 | `'ENT'` |
| 398 | `'is'` |
| 399 | `'expected'` |
| 400 | `'when'` |
| 401 | `'unl'` |
| 402 | `'inking'` |
| 403 | `'ur'` |
| 404 | `'bs'` |
| 405 | `'*/'` |
| 406 | `'\n'` |
| 407 | `'\t'` |
| 408 | `'\t'` |
| 409 | `'if'` |
| 410 | `'('` |
| 411 | `'urb'` |
| 412 | `'->'` |
| 413 | `'status'` |
| 414 | `'!='` |
| 415 | `'-'` |
| 416 | `'EN'` |
| 417 | `'O'` |
| 418 | `'ENT'` |
| 419 | `')'` |
| 420 | `'\n'` |
| 421 | `'\t'` |
| 422 | `'\t'` |
| 423 | `'\t'` |
| 424 | `'d'` |
| 425 | `'print'` |
| 426 | `'k'` |
| 427 | `'("'` |
| 428 | `'%'` |
| 429 | `'s'` |
| 430 | `':'` |
| 431 | `'ur'` |
| 432 | `'b'` |
| 433 | `'error'` |
| 434 | `':'` |
| 435 | `'%'` |
| 436 | `'d'` |
| 437 | `'\\'` |
| 438 | `'n'` |
| 439 | `'",'` |
| 440 | `'__'` |
| 441 | `'func'` |
| 442 | `'__'` |
| 443 | `','` |
| 444 | `'\n'` |
| 445 | `'\t'` |
| 446 | `'\t'` |
| 447 | `'\t'` |
| 448 | `'\t'` |
| 449 | `'urb'` |
| 450 | `'->'` |
| 451 | `'status'` |
| 452 | `');'` |
| 453 | `'\n'` |
| 454 | `'\t'` |
| 455 | `'}'` |
| 456 | `'\n\n'` |
| 457 | `'\t'` |
| 458 | `'if'` |
| 459 | `'('` |
| 460 | `'dec'` |
| 461 | `'->'` |
| 462 | `'iso'` |
| 463 | `'_'` |
| 464 | `'stream'` |
| 465 | `'_'` |
| 466 | `'count'` |
| 467 | `')'` |
| 468 | `'\n'` |
| 469 | `'\t'` |
| 470 | `'\t'` |
| 471 | `'usb'` |
| 472 | `'_'` |
| 473 | `'submit'` |
| 474 | `'_'` |
| 475 | `'urb'` |
| 476 | `'('` |
| 477 | `'urb'` |
| 478 | `','` |
| 479 | `'G'` |
| 480 | `'FP'` |
| 481 | `'_'` |
| 482 | `'AT'` |
| 483 | `'OM'` |
| 484 | `'IC'` |
| 485 | `');'` |
| 486 | `'\n'` |
| 487 | `'}'` |
