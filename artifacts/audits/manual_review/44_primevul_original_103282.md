# Review 44: `primevul:original:103282` (cpp)

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
   1 | void OmniboxViewWin::OnLButtonUp(UINT keys, const CPoint& point) {
   2 |   ScopedFreeze freeze(this, GetTextObjectModel());
   3 |   DefWindowProc(WM_LBUTTONUP, keys,
   4 |                 MAKELPARAM(ClipXCoordToVisibleText(point.x, false), point.y));
   5 | 
   6 |   SelectAllIfNecessary(kLeft, point);
   7 | 
   8 |   tracking_click_[kLeft] = false;
   9 | 
  10 |   possible_drag_ = false;
  11 | }
  12 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `void` | 1:1 |
| 1 | `OmniboxViewWin` | 1:6 |
| 3 | `OnLButtonUp` | 1:22 |
| 5 | `UINT` | 1:34 |
| 6 | `keys` | 1:39 |
| 8 | `const` | 1:45 |
| 9 | `CPoint` | 1:51 |
| 11 | `point` | 1:59 |
| 14 | `ScopedFreeze` | 2:3 |
| 15 | `freeze` | 2:16 |
| 17 | `this` | 2:23 |
| 19 | `GetTextObjectModel` | 2:29 |
| 24 | `DefWindowProc` | 3:3 |
| 26 | `WM_LBUTTONUP` | 3:17 |
| 28 | `keys` | 3:31 |
| 30 | `MAKELPARAM` | 4:17 |
| 32 | `ClipXCoordToVisibleText` | 4:28 |
| 34 | `point` | 4:52 |
| 36 | `x` | 4:58 |
| 38 | `false` | 4:61 |
| 41 | `point` | 4:69 |
| 43 | `y` | 4:75 |
| 47 | `SelectAllIfNecessary` | 6:3 |
| 49 | `kLeft` | 6:24 |
| 51 | `point` | 6:31 |
| 54 | `tracking_click_` | 8:3 |
| 56 | `kLeft` | 8:19 |
| 59 | `false` | 8:28 |
| 61 | `possible_drag_` | 10:3 |
| 63 | `false` | 10:20 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'void'` |
| 2 | `'Omn'` |
| 3 | `'ib'` |
| 4 | `'ox'` |
| 5 | `'View'` |
| 6 | `'Win'` |
| 7 | `'::'` |
| 8 | `'On'` |
| 9 | `'L'` |
| 10 | `'Button'` |
| 11 | `'Up'` |
| 12 | `'('` |
| 13 | `'U'` |
| 14 | `'INT'` |
| 15 | `'keys'` |
| 16 | `','` |
| 17 | `'const'` |
| 18 | `'C'` |
| 19 | `'Point'` |
| 20 | `'&'` |
| 21 | `'point'` |
| 22 | `')'` |
| 23 | `'{'` |
| 24 | `'\n'` |
| 26 | `'Sc'` |
| 27 | `'oped'` |
| 28 | `'Free'` |
| 29 | `'ze'` |
| 30 | `'freeze'` |
| 31 | `'('` |
| 32 | `'this'` |
| 33 | `','` |
| 34 | `'Get'` |
| 35 | `'Text'` |
| 36 | `'Object'` |
| 37 | `'Model'` |
| 38 | `'());'` |
| 39 | `'\n'` |
| 41 | `'Def'` |
| 42 | `'Window'` |
| 43 | `'Pro'` |
| 44 | `'c'` |
| 45 | `'('` |
| 46 | `'WM'` |
| 47 | `'_'` |
| 48 | `'LB'` |
| 49 | `'UT'` |
| 50 | `'TON'` |
| 51 | `'UP'` |
| 52 | `','` |
| 53 | `'keys'` |
| 54 | `','` |
| 55 | `'\n'` |
| 71 | `'MA'` |
| 72 | `'K'` |
| 73 | `'EL'` |
| 74 | `'PAR'` |
| 75 | `'AM'` |
| 76 | `'('` |
| 77 | `'Cl'` |
| 78 | `'ip'` |
| 79 | `'X'` |
| 80 | `'Co'` |
| 81 | `'ord'` |
| 82 | `'To'` |
| 83 | `'V'` |
| 84 | `'isible'` |
| 85 | `'Text'` |
| 86 | `'('` |
| 87 | `'point'` |
| 88 | `'.'` |
| 89 | `'x'` |
| 90 | `','` |
| 91 | `'false'` |
| 92 | `'),'` |
| 93 | `'point'` |
| 94 | `'.'` |
| 95 | `'y'` |
| 96 | `'));'` |
| 97 | `'\n\n'` |
| 99 | `'Select'` |
| 100 | `'All'` |
| 101 | `'If'` |
| 102 | `'N'` |
| 103 | `'ec'` |
| 104 | `'ess'` |
| 105 | `'ary'` |
| 106 | `'('` |
| 107 | `'k'` |
| 108 | `'Left'` |
| 109 | `','` |
| 110 | `'point'` |
| 111 | `');'` |
| 112 | `'\n\n'` |
| 114 | `'tracking'` |
| 115 | `'_'` |
| 116 | `'click'` |
| 117 | `'_'` |
| 118 | `'['` |
| 119 | `'k'` |
| 120 | `'Left'` |
| 121 | `']'` |
| 122 | `'='` |
| 123 | `'false'` |
| 124 | `';'` |
| 125 | `'\n\n'` |
| 127 | `'possible'` |
| 128 | `'_'` |
| 129 | `'dr'` |
| 130 | `'ag'` |
| 131 | `'_'` |
| 132 | `'='` |
| 133 | `'false'` |
| 134 | `';'` |
| 135 | `'\n'` |
| 136 | `'}'` |
| 137 | `'\n'` |
