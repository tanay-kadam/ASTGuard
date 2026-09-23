# Review 28: `primevul:original:187343` (c)

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
   1 | static char *sapi_fcgi_read_cookies(TSRMLS_D)
   2 | {
   3 | 	fcgi_request *request = (fcgi_request*) SG(server_context);
   4 | 
   5 | 	return FCGI_GETENV(request, "HTTP_COOKIE");
   6 | }
   7 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `char` | 1:8 |
| 3 | `sapi_fcgi_read_cookies` | 1:14 |
| 5 | `TSRMLS_D` | 1:37 |
| 8 | `fcgi_request` | 3:2 |
| 10 | `request` | 3:16 |
| 13 | `fcgi_request` | 3:27 |
| 16 | `SG` | 3:42 |
| 18 | `server_context` | 3:45 |
| 21 | `return` | 5:2 |
| 22 | `FCGI_GETENV` | 5:9 |
| 24 | `request` | 5:21 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'char'` |
| 3 | `'*'` |
| 4 | `'s'` |
| 5 | `'api'` |
| 6 | `'_'` |
| 7 | `'fc'` |
| 8 | `'gi'` |
| 9 | `'_'` |
| 10 | `'read'` |
| 11 | `'_'` |
| 12 | `'cook'` |
| 13 | `'ies'` |
| 14 | `'('` |
| 15 | `'TS'` |
| 16 | `'R'` |
| 17 | `'ML'` |
| 18 | `'S'` |
| 19 | `'_'` |
| 20 | `'D'` |
| 21 | `')'` |
| 22 | `'\n'` |
| 23 | `'{'` |
| 24 | `'\n'` |
| 25 | `'\t'` |
| 26 | `'fc'` |
| 27 | `'gi'` |
| 28 | `'_'` |
| 29 | `'request'` |
| 30 | `'*'` |
| 31 | `'request'` |
| 32 | `'='` |
| 33 | `'('` |
| 34 | `'fc'` |
| 35 | `'gi'` |
| 36 | `'_'` |
| 37 | `'request'` |
| 38 | `'*)'` |
| 39 | `'SG'` |
| 40 | `'('` |
| 41 | `'server'` |
| 42 | `'_'` |
| 43 | `'context'` |
| 44 | `');'` |
| 45 | `'\n\n'` |
| 46 | `'\t'` |
| 47 | `'return'` |
| 48 | `'FC'` |
| 49 | `'GI'` |
| 50 | `'_'` |
| 51 | `'GET'` |
| 52 | `'EN'` |
| 53 | `'V'` |
| 54 | `'('` |
| 55 | `'request'` |
| 56 | `','` |
| 57 | `'"'` |
| 58 | `'HTTP'` |
| 59 | `'_'` |
| 60 | `'C'` |
| 61 | `'OOK'` |
| 62 | `'IE'` |
| 63 | `'");'` |
| 64 | `'\n'` |
| 65 | `'}'` |
| 66 | `'\n'` |
