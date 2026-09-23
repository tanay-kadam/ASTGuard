# Review 46: `primevul:original:392011` (cpp)

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
   1 | g_file_real_delete_async (GFile               *file,
   2 |                           int                  io_priority,
   3 |                           GCancellable        *cancellable,
   4 |                           GAsyncReadyCallback  callback,
   5 |                           gpointer             user_data)
   6 | {
   7 |   GTask *task;
   8 | 
   9 |   task = g_task_new (file, cancellable, callback, user_data);
  10 |   g_task_set_source_tag (task, g_file_real_delete_async);
  11 |   g_task_set_priority (task, io_priority);
  12 |   g_task_run_in_thread (task, delete_async_thread);
  13 |   g_object_unref (task);
  14 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `g_file_real_delete_async` | 1:1 |
| 2 | `GFile` | 1:27 |
| 4 | `file` | 1:48 |
| 6 | `int` | 2:27 |
| 7 | `io_priority` | 2:48 |
| 9 | `GCancellable` | 3:27 |
| 11 | `cancellable` | 3:48 |
| 13 | `GAsyncReadyCallback` | 4:27 |
| 14 | `callback` | 4:48 |
| 16 | `gpointer` | 5:27 |
| 17 | `user_data` | 5:48 |
| 20 | `GTask` | 7:3 |
| 22 | `task` | 7:10 |
| 24 | `task` | 9:3 |
| 26 | `g_task_new` | 9:10 |
| 28 | `file` | 9:22 |
| 30 | `cancellable` | 9:28 |
| 32 | `callback` | 9:41 |
| 34 | `user_data` | 9:51 |
| 37 | `g_task_set_source_tag` | 10:3 |
| 39 | `task` | 10:26 |
| 41 | `g_file_real_delete_async` | 10:32 |
| 44 | `g_task_set_priority` | 11:3 |
| 46 | `task` | 11:24 |
| 48 | `io_priority` | 11:30 |
| 51 | `g_task_run_in_thread` | 12:3 |
| 53 | `task` | 12:25 |
| 55 | `delete_async_thread` | 12:31 |
| 58 | `g_object_unref` | 13:3 |
| 60 | `task` | 13:19 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'g'` |
| 2 | `'_'` |
| 3 | `'file'` |
| 4 | `'_'` |
| 5 | `'real'` |
| 6 | `'_'` |
| 7 | `'delete'` |
| 8 | `'_'` |
| 9 | `'as'` |
| 10 | `'ync'` |
| 11 | `'('` |
| 12 | `'G'` |
| 13 | `'File'` |
| 28 | `'*'` |
| 29 | `'file'` |
| 30 | `','` |
| 31 | `'\n'` |
| 57 | `'int'` |
| 75 | `'io'` |
| 76 | `'_'` |
| 77 | `'priority'` |
| 78 | `','` |
| 79 | `'\n'` |
| 105 | `'GC'` |
| 106 | `'ance'` |
| 107 | `'ll'` |
| 108 | `'able'` |
| 116 | `'*'` |
| 117 | `'c'` |
| 118 | `'ance'` |
| 119 | `'ll'` |
| 120 | `'able'` |
| 121 | `','` |
| 122 | `'\n'` |
| 148 | `'G'` |
| 149 | `'Async'` |
| 150 | `'Ready'` |
| 151 | `'Callback'` |
| 153 | `'callback'` |
| 154 | `','` |
| 155 | `'\n'` |
| 181 | `'g'` |
| 182 | `'pointer'` |
| 195 | `'user'` |
| 196 | `'_'` |
| 197 | `'data'` |
| 198 | `')'` |
| 199 | `'\n'` |
| 200 | `'{'` |
| 201 | `'\n'` |
| 203 | `'GT'` |
| 204 | `'ask'` |
| 205 | `'*'` |
| 206 | `'task'` |
| 207 | `';'` |
| 208 | `'\n\n'` |
| 210 | `'task'` |
| 211 | `'='` |
| 212 | `'g'` |
| 213 | `'_'` |
| 214 | `'task'` |
| 215 | `'_'` |
| 216 | `'new'` |
| 217 | `'('` |
| 218 | `'file'` |
| 219 | `','` |
| 220 | `'cancell'` |
| 221 | `'able'` |
| 222 | `','` |
| 223 | `'callback'` |
| 224 | `','` |
| 225 | `'user'` |
| 226 | `'_'` |
| 227 | `'data'` |
| 228 | `');'` |
| 229 | `'\n'` |
| 231 | `'g'` |
| 232 | `'_'` |
| 233 | `'task'` |
| 234 | `'_'` |
| 235 | `'set'` |
| 236 | `'_'` |
| 237 | `'source'` |
| 238 | `'_'` |
| 239 | `'tag'` |
| 240 | `'('` |
| 241 | `'task'` |
| 242 | `','` |
| 243 | `'g'` |
| 244 | `'_'` |
| 245 | `'file'` |
| 246 | `'_'` |
| 247 | `'real'` |
| 248 | `'_'` |
| 249 | `'delete'` |
| 250 | `'_'` |
| 251 | `'as'` |
| 252 | `'ync'` |
| 253 | `');'` |
| 254 | `'\n'` |
| 256 | `'g'` |
| 257 | `'_'` |
| 258 | `'task'` |
| 259 | `'_'` |
| 260 | `'set'` |
| 261 | `'_'` |
| 262 | `'priority'` |
| 263 | `'('` |
| 264 | `'task'` |
| 265 | `','` |
| 266 | `'io'` |
| 267 | `'_'` |
| 268 | `'priority'` |
| 269 | `');'` |
| 270 | `'\n'` |
| 272 | `'g'` |
| 273 | `'_'` |
| 274 | `'task'` |
| 275 | `'_'` |
| 276 | `'run'` |
| 277 | `'_'` |
| 278 | `'in'` |
| 279 | `'_'` |
| 280 | `'thread'` |
| 281 | `'('` |
| 282 | `'task'` |
| 283 | `','` |
| 284 | `'delete'` |
| 285 | `'_'` |
| 286 | `'as'` |
| 287 | `'ync'` |
| 288 | `'_'` |
| 289 | `'thread'` |
| 290 | `');'` |
| 291 | `'\n'` |
| 293 | `'g'` |
| 294 | `'_'` |
| 295 | `'object'` |
| 296 | `'_'` |
| 297 | `'un'` |
| 298 | `'ref'` |
| 299 | `'('` |
| 300 | `'task'` |
| 301 | `');'` |
| 302 | `'\n'` |
| 303 | `'}'` |
