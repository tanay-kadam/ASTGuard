# Review 31: `primevul:original:242462` (cpp)

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
   1 |     md_decode_utf16le_before__(MD_CTX* ctx, OFF off)
   2 |     {
   3 |         if(off > 2 && IS_UTF16_SURROGATE_HI(CH(off-2)) && IS_UTF16_SURROGATE_LO(CH(off-1)))
   4 |             return UTF16_DECODE_SURROGATE(CH(off-2), CH(off-1));
   5 | 
   6 |         return CH(off);
   7 |     }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `md_decode_utf16le_before__` | 1:5 |
| 2 | `MD_CTX` | 1:32 |
| 4 | `ctx` | 1:40 |
| 6 | `OFF` | 1:45 |
| 7 | `off` | 1:49 |
| 10 | `if` | 3:9 |
| 12 | `off` | 3:12 |
| 16 | `IS_UTF16_SURROGATE_HI` | 3:23 |
| 18 | `CH` | 3:45 |
| 20 | `off` | 3:48 |
| 26 | `IS_UTF16_SURROGATE_LO` | 3:59 |
| 28 | `CH` | 3:81 |
| 30 | `off` | 3:84 |
| 36 | `return` | 4:13 |
| 37 | `UTF16_DECODE_SURROGATE` | 4:20 |
| 39 | `CH` | 4:43 |
| 41 | `off` | 4:46 |
| 46 | `CH` | 4:54 |
| 48 | `off` | 4:57 |
| 54 | `return` | 6:9 |
| 55 | `CH` | 6:16 |
| 57 | `off` | 6:19 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 4 | `'md'` |
| 5 | `'_'` |
| 6 | `'dec'` |
| 7 | `'ode'` |
| 8 | `'_'` |
| 9 | `'utf'` |
| 10 | `'16'` |
| 11 | `'le'` |
| 12 | `'_'` |
| 13 | `'before'` |
| 14 | `'__'` |
| 15 | `'('` |
| 16 | `'MD'` |
| 17 | `'_'` |
| 18 | `'CT'` |
| 19 | `'X'` |
| 20 | `'*'` |
| 21 | `'c'` |
| 22 | `'tx'` |
| 23 | `','` |
| 24 | `'OFF'` |
| 25 | `'off'` |
| 26 | `')'` |
| 27 | `'\n'` |
| 31 | `'{'` |
| 32 | `'\n'` |
| 40 | `'if'` |
| 41 | `'('` |
| 42 | `'off'` |
| 43 | `'>'` |
| 44 | `'2'` |
| 45 | `'&&'` |
| 46 | `'IS'` |
| 47 | `'_'` |
| 48 | `'UTF'` |
| 49 | `'16'` |
| 50 | `'_'` |
| 51 | `'S'` |
| 52 | `'URR'` |
| 53 | `'OG'` |
| 54 | `'ATE'` |
| 55 | `'_'` |
| 56 | `'HI'` |
| 57 | `'('` |
| 58 | `'CH'` |
| 59 | `'('` |
| 60 | `'off'` |
| 61 | `'-'` |
| 62 | `'2'` |
| 63 | `'))'` |
| 64 | `'&&'` |
| 65 | `'IS'` |
| 66 | `'_'` |
| 67 | `'UTF'` |
| 68 | `'16'` |
| 69 | `'_'` |
| 70 | `'S'` |
| 71 | `'URR'` |
| 72 | `'OG'` |
| 73 | `'ATE'` |
| 74 | `'_'` |
| 75 | `'LO'` |
| 76 | `'('` |
| 77 | `'CH'` |
| 78 | `'('` |
| 79 | `'off'` |
| 80 | `'-'` |
| 81 | `'1'` |
| 82 | `')))'` |
| 83 | `'\n'` |
| 95 | `'return'` |
| 96 | `'UTF'` |
| 97 | `'16'` |
| 98 | `'_'` |
| 99 | `'DEC'` |
| 100 | `'ODE'` |
| 101 | `'_'` |
| 102 | `'S'` |
| 103 | `'URR'` |
| 104 | `'OG'` |
| 105 | `'ATE'` |
| 106 | `'('` |
| 107 | `'CH'` |
| 108 | `'('` |
| 109 | `'off'` |
| 110 | `'-'` |
| 111 | `'2'` |
| 112 | `'),'` |
| 113 | `'CH'` |
| 114 | `'('` |
| 115 | `'off'` |
| 116 | `'-'` |
| 117 | `'1'` |
| 118 | `'));'` |
| 119 | `'\n\n'` |
| 127 | `'return'` |
| 128 | `'CH'` |
| 129 | `'('` |
| 130 | `'off'` |
| 131 | `');'` |
| 132 | `'\n'` |
| 136 | `'}'` |
