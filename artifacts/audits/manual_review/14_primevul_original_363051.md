# Review 14: `primevul:original:363051` (c)

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
   1 | int unit_acquire_invocation_id(Unit *u) {
   2 |         sd_id128_t id;
   3 |         int r;
   4 | 
   5 |         assert(u);
   6 | 
   7 |         r = sd_id128_randomize(&id);
   8 |         if (r < 0)
   9 |                 return log_unit_error_errno(u, r, "Failed to generate invocation ID for unit: %m");
  10 | 
  11 |         r = unit_set_invocation_id(u, id);
  12 |         if (r < 0)
  13 |                 return log_unit_error_errno(u, r, "Failed to set invocation ID for unit: %m");
  14 | 
  15 |         unit_add_to_dbus_queue(u);
  16 |         return 0;
  17 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `int` | 1:1 |
| 1 | `unit_acquire_invocation_id` | 1:5 |
| 3 | `Unit` | 1:32 |
| 5 | `u` | 1:38 |
| 8 | `sd_id128_t` | 2:9 |
| 9 | `id` | 2:20 |
| 11 | `int` | 3:9 |
| 12 | `r` | 3:13 |
| 14 | `assert` | 5:9 |
| 16 | `u` | 5:16 |
| 19 | `r` | 7:9 |
| 21 | `sd_id128_randomize` | 7:13 |
| 24 | `id` | 7:33 |
| 27 | `if` | 8:9 |
| 29 | `r` | 8:13 |
| 33 | `return` | 9:17 |
| 34 | `log_unit_error_errno` | 9:24 |
| 36 | `u` | 9:45 |
| 38 | `r` | 9:48 |
| 43 | `r` | 11:9 |
| 45 | `unit_set_invocation_id` | 11:13 |
| 47 | `u` | 11:36 |
| 49 | `id` | 11:39 |
| 52 | `if` | 12:9 |
| 54 | `r` | 12:13 |
| 58 | `return` | 13:17 |
| 59 | `log_unit_error_errno` | 13:24 |
| 61 | `u` | 13:45 |
| 63 | `r` | 13:48 |
| 68 | `unit_add_to_dbus_queue` | 15:9 |
| 70 | `u` | 15:32 |
| 73 | `return` | 16:9 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'int'` |
| 2 | `'unit'` |
| 3 | `'_'` |
| 4 | `'ac'` |
| 5 | `'quire'` |
| 6 | `'_'` |
| 7 | `'inv'` |
| 8 | `'ocation'` |
| 9 | `'_'` |
| 10 | `'id'` |
| 11 | `'('` |
| 12 | `'Unit'` |
| 13 | `'*'` |
| 14 | `'u'` |
| 15 | `')'` |
| 16 | `'{'` |
| 17 | `'\n'` |
| 25 | `'sd'` |
| 26 | `'_'` |
| 27 | `'id'` |
| 28 | `'128'` |
| 29 | `'_'` |
| 30 | `'t'` |
| 31 | `'id'` |
| 32 | `';'` |
| 33 | `'\n'` |
| 41 | `'int'` |
| 42 | `'r'` |
| 43 | `';'` |
| 44 | `'\n\n'` |
| 52 | `'assert'` |
| 53 | `'('` |
| 54 | `'u'` |
| 55 | `');'` |
| 56 | `'\n\n'` |
| 64 | `'r'` |
| 65 | `'='` |
| 66 | `'sd'` |
| 67 | `'_'` |
| 68 | `'id'` |
| 69 | `'128'` |
| 70 | `'_'` |
| 71 | `'random'` |
| 72 | `'ize'` |
| 73 | `'(&'` |
| 74 | `'id'` |
| 75 | `');'` |
| 76 | `'\n'` |
| 84 | `'if'` |
| 85 | `'('` |
| 86 | `'r'` |
| 87 | `'<'` |
| 88 | `'0'` |
| 89 | `')'` |
| 90 | `'\n'` |
| 106 | `'return'` |
| 107 | `'log'` |
| 108 | `'_'` |
| 109 | `'unit'` |
| 110 | `'_'` |
| 111 | `'error'` |
| 112 | `'_'` |
| 113 | `'err'` |
| 114 | `'no'` |
| 115 | `'('` |
| 116 | `'u'` |
| 117 | `','` |
| 118 | `'r'` |
| 119 | `','` |
| 120 | `'"'` |
| 121 | `'F'` |
| 122 | `'ailed'` |
| 123 | `'to'` |
| 124 | `'generate'` |
| 125 | `'invocation'` |
| 126 | `'ID'` |
| 127 | `'for'` |
| 128 | `'unit'` |
| 129 | `':'` |
| 130 | `'%'` |
| 131 | `'m'` |
| 132 | `'");'` |
| 133 | `'\n\n'` |
| 141 | `'r'` |
| 142 | `'='` |
| 143 | `'unit'` |
| 144 | `'_'` |
| 145 | `'set'` |
| 146 | `'_'` |
| 147 | `'inv'` |
| 148 | `'ocation'` |
| 149 | `'_'` |
| 150 | `'id'` |
| 151 | `'('` |
| 152 | `'u'` |
| 153 | `','` |
| 154 | `'id'` |
| 155 | `');'` |
| 156 | `'\n'` |
| 164 | `'if'` |
| 165 | `'('` |
| 166 | `'r'` |
| 167 | `'<'` |
| 168 | `'0'` |
| 169 | `')'` |
| 170 | `'\n'` |
| 186 | `'return'` |
| 187 | `'log'` |
| 188 | `'_'` |
| 189 | `'unit'` |
| 190 | `'_'` |
| 191 | `'error'` |
| 192 | `'_'` |
| 193 | `'err'` |
| 194 | `'no'` |
| 195 | `'('` |
| 196 | `'u'` |
| 197 | `','` |
| 198 | `'r'` |
| 199 | `','` |
| 200 | `'"'` |
| 201 | `'F'` |
| 202 | `'ailed'` |
| 203 | `'to'` |
| 204 | `'set'` |
| 205 | `'invocation'` |
| 206 | `'ID'` |
| 207 | `'for'` |
| 208 | `'unit'` |
| 209 | `':'` |
| 210 | `'%'` |
| 211 | `'m'` |
| 212 | `'");'` |
| 213 | `'\n\n'` |
| 221 | `'unit'` |
| 222 | `'_'` |
| 223 | `'add'` |
| 224 | `'_'` |
| 225 | `'to'` |
| 226 | `'_'` |
| 227 | `'db'` |
| 228 | `'us'` |
| 229 | `'_'` |
| 230 | `'queue'` |
| 231 | `'('` |
| 232 | `'u'` |
| 233 | `');'` |
| 234 | `'\n'` |
| 242 | `'return'` |
| 243 | `'0'` |
| 244 | `';'` |
| 245 | `'\n'` |
| 246 | `'}'` |
