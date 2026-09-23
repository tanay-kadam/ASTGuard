# Review 13: `primevul:original:226566` (c)

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
   1 |   void requestInit() override {
   2 |     m_locale = String(uloc_getDefault(), CopyString);
   3 |     m_errcode.clearError();
   4 |     UErrorCode error = U_ZERO_ERROR;
   5 |     m_ucoll = ucol_open(m_locale.data(), &error);
   6 |     if (U_FAILURE(error)) {
   7 |       m_errcode.setError(error);
   8 |     }
   9 |     assert(m_ucoll);
  10 |   }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `void` | 1:3 |
| 1 | `requestInit` | 1:8 |
| 4 | `override` | 1:22 |
| 6 | `m_locale` | 2:5 |
| 8 | `String` | 2:16 |
| 10 | `uloc_getDefault` | 2:23 |
| 14 | `CopyString` | 2:42 |
| 17 | `m_errcode` | 3:5 |
| 19 | `clearError` | 3:15 |
| 23 | `UErrorCode` | 4:5 |
| 24 | `error` | 4:16 |
| 26 | `U_ZERO_ERROR` | 4:24 |
| 28 | `m_ucoll` | 5:5 |
| 30 | `ucol_open` | 5:15 |
| 32 | `m_locale` | 5:25 |
| 34 | `data` | 5:34 |
| 39 | `error` | 5:43 |
| 42 | `if` | 6:5 |
| 44 | `U_FAILURE` | 6:9 |
| 46 | `error` | 6:19 |
| 50 | `m_errcode` | 7:7 |
| 52 | `setError` | 7:17 |
| 54 | `error` | 7:26 |
| 58 | `assert` | 9:5 |
| 60 | `m_ucoll` | 9:12 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 2 | `'void'` |
| 3 | `'request'` |
| 4 | `'Init'` |
| 5 | `'()'` |
| 6 | `'override'` |
| 7 | `'{'` |
| 8 | `'\n'` |
| 12 | `'m'` |
| 13 | `'_'` |
| 14 | `'loc'` |
| 15 | `'ale'` |
| 16 | `'='` |
| 17 | `'String'` |
| 18 | `'('` |
| 19 | `'ul'` |
| 20 | `'oc'` |
| 21 | `'_'` |
| 22 | `'get'` |
| 23 | `'Default'` |
| 24 | `'(),'` |
| 25 | `'Copy'` |
| 26 | `'String'` |
| 27 | `');'` |
| 28 | `'\n'` |
| 32 | `'m'` |
| 33 | `'_'` |
| 34 | `'er'` |
| 35 | `'rc'` |
| 36 | `'ode'` |
| 37 | `'.'` |
| 38 | `'clear'` |
| 39 | `'Error'` |
| 40 | `'();'` |
| 41 | `'\n'` |
| 45 | `'U'` |
| 46 | `'Error'` |
| 47 | `'Code'` |
| 48 | `'error'` |
| 49 | `'='` |
| 50 | `'U'` |
| 51 | `'_'` |
| 52 | `'Z'` |
| 53 | `'ERO'` |
| 54 | `'_'` |
| 55 | `'ERROR'` |
| 56 | `';'` |
| 57 | `'\n'` |
| 61 | `'m'` |
| 62 | `'_'` |
| 63 | `'uc'` |
| 64 | `'oll'` |
| 65 | `'='` |
| 66 | `'u'` |
| 67 | `'col'` |
| 68 | `'_'` |
| 69 | `'open'` |
| 70 | `'('` |
| 71 | `'m'` |
| 72 | `'_'` |
| 73 | `'loc'` |
| 74 | `'ale'` |
| 75 | `'.'` |
| 76 | `'data'` |
| 77 | `'(),'` |
| 78 | `'&'` |
| 79 | `'error'` |
| 80 | `');'` |
| 81 | `'\n'` |
| 85 | `'if'` |
| 86 | `'('` |
| 87 | `'U'` |
| 88 | `'_'` |
| 89 | `'FA'` |
| 90 | `'IL'` |
| 91 | `'URE'` |
| 92 | `'('` |
| 93 | `'error'` |
| 94 | `'))'` |
| 95 | `'{'` |
| 96 | `'\n'` |
| 102 | `'m'` |
| 103 | `'_'` |
| 104 | `'er'` |
| 105 | `'rc'` |
| 106 | `'ode'` |
| 107 | `'.'` |
| 108 | `'set'` |
| 109 | `'Error'` |
| 110 | `'('` |
| 111 | `'error'` |
| 112 | `');'` |
| 113 | `'\n'` |
| 117 | `'}'` |
| 118 | `'\n'` |
| 122 | `'assert'` |
| 123 | `'('` |
| 124 | `'m'` |
| 125 | `'_'` |
| 126 | `'uc'` |
| 127 | `'oll'` |
| 128 | `');'` |
| 129 | `'\n'` |
| 131 | `'}'` |
