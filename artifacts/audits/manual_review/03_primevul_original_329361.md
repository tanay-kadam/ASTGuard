# Review 03: `primevul:original:329361` (c)

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
   1 | void manager_recheck_journal(Manager *m) {
   2 |         Unit *u;
   3 | 
   4 |         assert(m);
   5 | 
   6 |         if (m->running_as != SYSTEMD_SYSTEM)
   7 |                 return;
   8 | 
   9 |         u = manager_get_unit(m, SPECIAL_JOURNALD_SOCKET);
  10 |         if (u && SOCKET(u)->state != SOCKET_RUNNING) {
  11 |                 log_close_journal();
  12 |                 return;
  13 |         }
  14 | 
  15 |         u = manager_get_unit(m, SPECIAL_JOURNALD_SERVICE);
  16 |         if (u && SERVICE(u)->state != SERVICE_RUNNING) {
  17 |                 log_close_journal();
  18 |                 return;
  19 |         }
  20 | 
  21 |         /* Hmm, OK, so the socket is fully up and the service is up
  22 |          * too, then let's make use of the thing. */
  23 |         log_open();
  24 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `void` | 1:1 |
| 1 | `manager_recheck_journal` | 1:6 |
| 3 | `Manager` | 1:30 |
| 5 | `m` | 1:39 |
| 8 | `Unit` | 2:9 |
| 10 | `u` | 2:15 |
| 12 | `assert` | 4:9 |
| 14 | `m` | 4:16 |
| 17 | `if` | 6:9 |
| 19 | `m` | 6:13 |
| 21 | `running_as` | 6:16 |
| 23 | `SYSTEMD_SYSTEM` | 6:30 |
| 25 | `return` | 7:17 |
| 27 | `u` | 9:9 |
| 29 | `manager_get_unit` | 9:13 |
| 31 | `m` | 9:30 |
| 33 | `SPECIAL_JOURNALD_SOCKET` | 9:33 |
| 36 | `if` | 10:9 |
| 38 | `u` | 10:13 |
| 40 | `SOCKET` | 10:18 |
| 42 | `u` | 10:25 |
| 45 | `state` | 10:29 |
| 47 | `SOCKET_RUNNING` | 10:38 |
| 50 | `log_close_journal` | 11:17 |
| 54 | `return` | 12:17 |
| 57 | `u` | 15:9 |
| 59 | `manager_get_unit` | 15:13 |
| 61 | `m` | 15:30 |
| 63 | `SPECIAL_JOURNALD_SERVICE` | 15:33 |
| 66 | `if` | 16:9 |
| 68 | `u` | 16:13 |
| 70 | `SERVICE` | 16:18 |
| 72 | `u` | 16:26 |
| 75 | `state` | 16:30 |
| 77 | `SERVICE_RUNNING` | 16:39 |
| 80 | `log_close_journal` | 17:17 |
| 84 | `return` | 18:17 |
| 87 | `log_open` | 23:9 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'void'` |
| 2 | `'manager'` |
| 3 | `'_'` |
| 4 | `'re'` |
| 5 | `'check'` |
| 6 | `'_'` |
| 7 | `'journal'` |
| 8 | `'('` |
| 9 | `'Manager'` |
| 10 | `'*'` |
| 11 | `'m'` |
| 12 | `')'` |
| 13 | `'{'` |
| 14 | `'\n'` |
| 22 | `'Unit'` |
| 23 | `'*'` |
| 24 | `'u'` |
| 25 | `';'` |
| 26 | `'\n\n'` |
| 34 | `'assert'` |
| 35 | `'('` |
| 36 | `'m'` |
| 37 | `');'` |
| 38 | `'\n\n'` |
| 46 | `'if'` |
| 47 | `'('` |
| 48 | `'m'` |
| 49 | `'->'` |
| 50 | `'running'` |
| 51 | `'_'` |
| 52 | `'as'` |
| 53 | `'!='` |
| 54 | `'SYSTEM'` |
| 55 | `'D'` |
| 56 | `'_'` |
| 57 | `'SY'` |
| 58 | `'STEM'` |
| 59 | `')'` |
| 60 | `'\n'` |
| 76 | `'return'` |
| 77 | `';'` |
| 78 | `'\n\n'` |
| 86 | `'u'` |
| 87 | `'='` |
| 88 | `'manager'` |
| 89 | `'_'` |
| 90 | `'get'` |
| 91 | `'_'` |
| 92 | `'unit'` |
| 93 | `'('` |
| 94 | `'m'` |
| 95 | `','` |
| 96 | `'SPECIAL'` |
| 97 | `'_'` |
| 98 | `'J'` |
| 99 | `'OUR'` |
| 100 | `'N'` |
| 101 | `'ALD'` |
| 102 | `'_'` |
| 103 | `'S'` |
| 104 | `'OCK'` |
| 105 | `'ET'` |
| 106 | `');'` |
| 107 | `'\n'` |
| 115 | `'if'` |
| 116 | `'('` |
| 117 | `'u'` |
| 118 | `'&&'` |
| 119 | `'S'` |
| 120 | `'OCK'` |
| 121 | `'ET'` |
| 122 | `'('` |
| 123 | `'u'` |
| 124 | `')'` |
| 125 | `'->'` |
| 126 | `'state'` |
| 127 | `'!='` |
| 128 | `'S'` |
| 129 | `'OCK'` |
| 130 | `'ET'` |
| 131 | `'_'` |
| 132 | `'R'` |
| 133 | `'UN'` |
| 134 | `'NING'` |
| 135 | `')'` |
| 136 | `'{'` |
| 137 | `'\n'` |
| 153 | `'log'` |
| 154 | `'_'` |
| 155 | `'close'` |
| 156 | `'_'` |
| 157 | `'journal'` |
| 158 | `'();'` |
| 159 | `'\n'` |
| 175 | `'return'` |
| 176 | `';'` |
| 177 | `'\n'` |
| 185 | `'}'` |
| 186 | `'\n\n'` |
| 194 | `'u'` |
| 195 | `'='` |
| 196 | `'manager'` |
| 197 | `'_'` |
| 198 | `'get'` |
| 199 | `'_'` |
| 200 | `'unit'` |
| 201 | `'('` |
| 202 | `'m'` |
| 203 | `','` |
| 204 | `'SPECIAL'` |
| 205 | `'_'` |
| 206 | `'J'` |
| 207 | `'OUR'` |
| 208 | `'N'` |
| 209 | `'ALD'` |
| 210 | `'_'` |
| 211 | `'SER'` |
| 212 | `'VICE'` |
| 213 | `');'` |
| 214 | `'\n'` |
| 222 | `'if'` |
| 223 | `'('` |
| 224 | `'u'` |
| 225 | `'&&'` |
| 226 | `'SERVICE'` |
| 227 | `'('` |
| 228 | `'u'` |
| 229 | `')'` |
| 230 | `'->'` |
| 231 | `'state'` |
| 232 | `'!='` |
| 233 | `'SERVICE'` |
| 234 | `'_'` |
| 235 | `'R'` |
| 236 | `'UN'` |
| 237 | `'NING'` |
| 238 | `')'` |
| 239 | `'{'` |
| 240 | `'\n'` |
| 256 | `'log'` |
| 257 | `'_'` |
| 258 | `'close'` |
| 259 | `'_'` |
| 260 | `'journal'` |
| 261 | `'();'` |
| 262 | `'\n'` |
| 278 | `'return'` |
| 279 | `';'` |
| 280 | `'\n'` |
| 288 | `'}'` |
| 289 | `'\n\n'` |
| 297 | `'/*'` |
| 298 | `'Hmm'` |
| 299 | `','` |
| 300 | `'OK'` |
| 301 | `','` |
| 302 | `'so'` |
| 303 | `'the'` |
| 304 | `'socket'` |
| 305 | `'is'` |
| 306 | `'fully'` |
| 307 | `'up'` |
| 308 | `'and'` |
| 309 | `'the'` |
| 310 | `'service'` |
| 311 | `'is'` |
| 312 | `'up'` |
| 313 | `'\n'` |
| 322 | `'*'` |
| 323 | `'too'` |
| 324 | `','` |
| 325 | `'then'` |
| 326 | `'let'` |
| 327 | `"'s"` |
| 328 | `'make'` |
| 329 | `'use'` |
| 330 | `'of'` |
| 331 | `'the'` |
| 332 | `'thing'` |
| 333 | `'.'` |
| 334 | `'*/'` |
| 335 | `'\n'` |
| 343 | `'log'` |
| 344 | `'_'` |
| 345 | `'open'` |
| 346 | `'();'` |
| 347 | `'\n'` |
| 348 | `'}'` |
