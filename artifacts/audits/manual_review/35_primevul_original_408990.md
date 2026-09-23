# Review 35: `primevul:original:408990` (c)

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
   1 | static char *ldb_parse_find_wildcard(char *value)
   2 | {
   3 | 	while (*value) {
   4 | 		value = strpbrk(value, "\\*");
   5 | 		if (value == NULL) return NULL;
   6 | 
   7 | 		if (value[0] == '\\') {
   8 | 			if (value[1] == '\0') return NULL;
   9 | 			value += 2;
  10 | 			continue;
  11 | 		}
  12 | 
  13 | 		if (value[0] == '*') return value;
  14 | 	}
  15 | 
  16 | 	return NULL;
  17 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `char` | 1:8 |
| 3 | `ldb_parse_find_wildcard` | 1:14 |
| 5 | `char` | 1:38 |
| 7 | `value` | 1:44 |
| 10 | `while` | 3:2 |
| 13 | `value` | 3:10 |
| 16 | `value` | 4:3 |
| 18 | `strpbrk` | 4:11 |
| 20 | `value` | 4:19 |
| 25 | `if` | 5:3 |
| 27 | `value` | 5:7 |
| 29 | `NULL` | 5:16 |
| 31 | `return` | 5:22 |
| 32 | `NULL` | 5:29 |
| 34 | `if` | 7:3 |
| 36 | `value` | 7:7 |
| 44 | `if` | 8:4 |
| 46 | `value` | 8:8 |
| 53 | `return` | 8:26 |
| 54 | `NULL` | 8:33 |
| 56 | `value` | 9:4 |
| 60 | `continue` | 10:4 |
| 63 | `if` | 13:3 |
| 65 | `value` | 13:7 |
| 72 | `return` | 13:24 |
| 73 | `value` | 13:31 |
| 76 | `return` | 16:2 |
| 77 | `NULL` | 16:9 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'char'` |
| 3 | `'*'` |
| 4 | `'ld'` |
| 5 | `'b'` |
| 6 | `'_'` |
| 7 | `'parse'` |
| 8 | `'_'` |
| 9 | `'find'` |
| 10 | `'_'` |
| 11 | `'wild'` |
| 12 | `'card'` |
| 13 | `'('` |
| 14 | `'char'` |
| 15 | `'*'` |
| 16 | `'value'` |
| 17 | `')'` |
| 18 | `'\n'` |
| 19 | `'{'` |
| 20 | `'\n'` |
| 21 | `'\t'` |
| 22 | `'while'` |
| 23 | `'(*'` |
| 24 | `'value'` |
| 25 | `')'` |
| 26 | `'{'` |
| 27 | `'\n'` |
| 28 | `'\t'` |
| 29 | `'\t'` |
| 30 | `'value'` |
| 31 | `'='` |
| 32 | `'str'` |
| 33 | `'p'` |
| 34 | `'br'` |
| 35 | `'k'` |
| 36 | `'('` |
| 37 | `'value'` |
| 38 | `','` |
| 39 | `'"'` |
| 40 | `'\\\\'` |
| 41 | `'*'` |
| 42 | `'");'` |
| 43 | `'\n'` |
| 44 | `'\t'` |
| 45 | `'\t'` |
| 46 | `'if'` |
| 47 | `'('` |
| 48 | `'value'` |
| 49 | `'=='` |
| 50 | `'NULL'` |
| 51 | `')'` |
| 52 | `'return'` |
| 53 | `'NULL'` |
| 54 | `';'` |
| 55 | `'\n\n'` |
| 56 | `'\t'` |
| 57 | `'\t'` |
| 58 | `'if'` |
| 59 | `'('` |
| 60 | `'value'` |
| 61 | `'['` |
| 62 | `'0'` |
| 63 | `']'` |
| 64 | `'=='` |
| 65 | `"'"` |
| 66 | `'\\\\'` |
| 67 | `"')"` |
| 68 | `'{'` |
| 69 | `'\n'` |
| 70 | `'\t'` |
| 71 | `'\t'` |
| 72 | `'\t'` |
| 73 | `'if'` |
| 74 | `'('` |
| 75 | `'value'` |
| 76 | `'['` |
| 77 | `'1'` |
| 78 | `']'` |
| 79 | `'=='` |
| 80 | `"'"` |
| 81 | `'\\'` |
| 82 | `'0'` |
| 83 | `"')"` |
| 84 | `'return'` |
| 85 | `'NULL'` |
| 86 | `';'` |
| 87 | `'\n'` |
| 88 | `'\t'` |
| 89 | `'\t'` |
| 90 | `'\t'` |
| 91 | `'value'` |
| 92 | `'+='` |
| 93 | `'2'` |
| 94 | `';'` |
| 95 | `'\n'` |
| 96 | `'\t'` |
| 97 | `'\t'` |
| 98 | `'\t'` |
| 99 | `'continue'` |
| 100 | `';'` |
| 101 | `'\n'` |
| 102 | `'\t'` |
| 103 | `'\t'` |
| 104 | `'}'` |
| 105 | `'\n\n'` |
| 106 | `'\t'` |
| 107 | `'\t'` |
| 108 | `'if'` |
| 109 | `'('` |
| 110 | `'value'` |
| 111 | `'['` |
| 112 | `'0'` |
| 113 | `']'` |
| 114 | `'=='` |
| 115 | `"'"` |
| 116 | `'*'` |
| 117 | `"')"` |
| 118 | `'return'` |
| 119 | `'value'` |
| 120 | `';'` |
| 121 | `'\n'` |
| 122 | `'\t'` |
| 123 | `'}'` |
| 124 | `'\n\n'` |
| 125 | `'\t'` |
| 126 | `'return'` |
| 127 | `'NULL'` |
| 128 | `';'` |
| 129 | `'\n'` |
| 130 | `'}'` |
