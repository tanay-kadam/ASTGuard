# Review 10: `primevul:original:187985` (cpp)

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
   1 | pvscsi_on_command_data(PVSCSIState *s, uint32_t value)
   2 | {
   3 |     size_t bytes_arrived = s->curr_cmd_data_cntr * sizeof(uint32_t);
   4 | 
   5 |     assert(bytes_arrived < sizeof(s->curr_cmd_data));
   6 |     s->curr_cmd_data[s->curr_cmd_data_cntr++] = value;
   7 | 
   8 |     pvscsi_do_command_processing(s);
   9 | }
  10 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `pvscsi_on_command_data` | 1:1 |
| 2 | `PVSCSIState` | 1:24 |
| 4 | `s` | 1:37 |
| 6 | `uint32_t` | 1:40 |
| 7 | `value` | 1:49 |
| 10 | `size_t` | 3:5 |
| 11 | `bytes_arrived` | 3:12 |
| 13 | `s` | 3:28 |
| 15 | `curr_cmd_data_cntr` | 3:31 |
| 17 | `sizeof` | 3:52 |
| 19 | `uint32_t` | 3:59 |
| 22 | `assert` | 5:5 |
| 24 | `bytes_arrived` | 5:12 |
| 26 | `sizeof` | 5:28 |
| 28 | `s` | 5:35 |
| 30 | `curr_cmd_data` | 5:38 |
| 34 | `s` | 6:5 |
| 36 | `curr_cmd_data` | 6:8 |
| 38 | `s` | 6:22 |
| 40 | `curr_cmd_data_cntr` | 6:25 |
| 44 | `value` | 6:49 |
| 46 | `pvscsi_do_command_processing` | 8:5 |
| 48 | `s` | 8:34 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'p'` |
| 2 | `'v'` |
| 3 | `'sc'` |
| 4 | `'si'` |
| 5 | `'_'` |
| 6 | `'on'` |
| 7 | `'_'` |
| 8 | `'command'` |
| 9 | `'_'` |
| 10 | `'data'` |
| 11 | `'('` |
| 12 | `'P'` |
| 13 | `'V'` |
| 14 | `'SC'` |
| 15 | `'SI'` |
| 16 | `'State'` |
| 17 | `'*'` |
| 18 | `'s'` |
| 19 | `','` |
| 20 | `'uint'` |
| 21 | `'32'` |
| 22 | `'_'` |
| 23 | `'t'` |
| 24 | `'value'` |
| 25 | `')'` |
| 26 | `'\n'` |
| 27 | `'{'` |
| 28 | `'\n'` |
| 32 | `'size'` |
| 33 | `'_'` |
| 34 | `'t'` |
| 35 | `'bytes'` |
| 36 | `'_'` |
| 37 | `'ar'` |
| 38 | `'rived'` |
| 39 | `'='` |
| 40 | `'s'` |
| 41 | `'->'` |
| 42 | `'cur'` |
| 43 | `'r'` |
| 44 | `'_'` |
| 45 | `'cmd'` |
| 46 | `'_'` |
| 47 | `'data'` |
| 48 | `'_'` |
| 49 | `'c'` |
| 50 | `'nt'` |
| 51 | `'r'` |
| 52 | `'*'` |
| 53 | `'sizeof'` |
| 54 | `'('` |
| 55 | `'uint'` |
| 56 | `'32'` |
| 57 | `'_'` |
| 58 | `'t'` |
| 59 | `');'` |
| 60 | `'\n\n'` |
| 64 | `'assert'` |
| 65 | `'('` |
| 66 | `'bytes'` |
| 67 | `'_'` |
| 68 | `'ar'` |
| 69 | `'rived'` |
| 70 | `'<'` |
| 71 | `'sizeof'` |
| 72 | `'('` |
| 73 | `'s'` |
| 74 | `'->'` |
| 75 | `'cur'` |
| 76 | `'r'` |
| 77 | `'_'` |
| 78 | `'cmd'` |
| 79 | `'_'` |
| 80 | `'data'` |
| 81 | `'));'` |
| 82 | `'\n'` |
| 86 | `'s'` |
| 87 | `'->'` |
| 88 | `'cur'` |
| 89 | `'r'` |
| 90 | `'_'` |
| 91 | `'cmd'` |
| 92 | `'_'` |
| 93 | `'data'` |
| 94 | `'['` |
| 95 | `'s'` |
| 96 | `'->'` |
| 97 | `'cur'` |
| 98 | `'r'` |
| 99 | `'_'` |
| 100 | `'cmd'` |
| 101 | `'_'` |
| 102 | `'data'` |
| 103 | `'_'` |
| 104 | `'c'` |
| 105 | `'nt'` |
| 106 | `'r'` |
| 107 | `'++'` |
| 108 | `']'` |
| 109 | `'='` |
| 110 | `'value'` |
| 111 | `';'` |
| 112 | `'\n\n'` |
| 116 | `'p'` |
| 117 | `'v'` |
| 118 | `'sc'` |
| 119 | `'si'` |
| 120 | `'_'` |
| 121 | `'do'` |
| 122 | `'_'` |
| 123 | `'command'` |
| 124 | `'_'` |
| 125 | `'processing'` |
| 126 | `'('` |
| 127 | `'s'` |
| 128 | `');'` |
| 129 | `'\n'` |
| 130 | `'}'` |
| 131 | `'\n'` |
