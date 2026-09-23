# Review 20: `primevul:original:297071` (c)

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
   1 | bool manager_unit_inactive_or_pending(Manager *m, const char *name) {
   2 |         Unit *u;
   3 | 
   4 |         assert(m);
   5 |         assert(name);
   6 | 
   7 |         /* Returns true if the unit is inactive or going down */
   8 |         u = manager_get_unit(m, name);
   9 |         if (!u)
  10 |                 return true;
  11 | 
  12 |         return unit_inactive_or_pending(u);
  13 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `bool` | 1:1 |
| 1 | `manager_unit_inactive_or_pending` | 1:6 |
| 3 | `Manager` | 1:39 |
| 5 | `m` | 1:48 |
| 7 | `const` | 1:51 |
| 8 | `char` | 1:57 |
| 10 | `name` | 1:63 |
| 13 | `Unit` | 2:9 |
| 15 | `u` | 2:15 |
| 17 | `assert` | 4:9 |
| 19 | `m` | 4:16 |
| 22 | `assert` | 5:9 |
| 24 | `name` | 5:16 |
| 27 | `u` | 8:9 |
| 29 | `manager_get_unit` | 8:13 |
| 31 | `m` | 8:30 |
| 33 | `name` | 8:33 |
| 36 | `if` | 9:9 |
| 39 | `u` | 9:14 |
| 41 | `return` | 10:17 |
| 42 | `true` | 10:24 |
| 44 | `return` | 12:9 |
| 45 | `unit_inactive_or_pending` | 12:16 |
| 47 | `u` | 12:41 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'bool'` |
| 2 | `'manager'` |
| 3 | `'_'` |
| 4 | `'unit'` |
| 5 | `'_'` |
| 6 | `'in'` |
| 7 | `'active'` |
| 8 | `'_'` |
| 9 | `'or'` |
| 10 | `'_'` |
| 11 | `'p'` |
| 12 | `'ending'` |
| 13 | `'('` |
| 14 | `'Manager'` |
| 15 | `'*'` |
| 16 | `'m'` |
| 17 | `','` |
| 18 | `'const'` |
| 19 | `'char'` |
| 20 | `'*'` |
| 21 | `'name'` |
| 22 | `')'` |
| 23 | `'{'` |
| 24 | `'\n'` |
| 32 | `'Unit'` |
| 33 | `'*'` |
| 34 | `'u'` |
| 35 | `';'` |
| 36 | `'\n\n'` |
| 44 | `'assert'` |
| 45 | `'('` |
| 46 | `'m'` |
| 47 | `');'` |
| 48 | `'\n'` |
| 56 | `'assert'` |
| 57 | `'('` |
| 58 | `'name'` |
| 59 | `');'` |
| 60 | `'\n\n'` |
| 68 | `'/*'` |
| 69 | `'Returns'` |
| 70 | `'true'` |
| 71 | `'if'` |
| 72 | `'the'` |
| 73 | `'unit'` |
| 74 | `'is'` |
| 75 | `'inactive'` |
| 76 | `'or'` |
| 77 | `'going'` |
| 78 | `'down'` |
| 79 | `'*/'` |
| 80 | `'\n'` |
| 88 | `'u'` |
| 89 | `'='` |
| 90 | `'manager'` |
| 91 | `'_'` |
| 92 | `'get'` |
| 93 | `'_'` |
| 94 | `'unit'` |
| 95 | `'('` |
| 96 | `'m'` |
| 97 | `','` |
| 98 | `'name'` |
| 99 | `');'` |
| 100 | `'\n'` |
| 108 | `'if'` |
| 109 | `'(!'` |
| 110 | `'u'` |
| 111 | `')'` |
| 112 | `'\n'` |
| 128 | `'return'` |
| 129 | `'true'` |
| 130 | `';'` |
| 131 | `'\n\n'` |
| 139 | `'return'` |
| 140 | `'unit'` |
| 141 | `'_'` |
| 142 | `'in'` |
| 143 | `'active'` |
| 144 | `'_'` |
| 145 | `'or'` |
| 146 | `'_'` |
| 147 | `'p'` |
| 148 | `'ending'` |
| 149 | `'('` |
| 150 | `'u'` |
| 151 | `');'` |
| 152 | `'\n'` |
| 153 | `'}'` |
