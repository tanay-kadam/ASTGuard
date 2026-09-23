# Review 11: `primevul:original:179889` (cpp)

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
   1 | void RenderViewTest::LoadHTMLWithUrlOverride(const char* html,
   2 |                                              const char* url_override) {
   3 |   GetMainFrame()->LoadHTMLString(std::string(html),
   4 |                                  blink::WebURL(GURL(url_override)));
   5 |   FrameLoadWaiter(view_->GetMainRenderFrame()).Wait();
   6 |   view_->GetWebView()->UpdateAllLifecyclePhases();
   7 | }
   8 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `void` | 1:1 |
| 1 | `RenderViewTest` | 1:6 |
| 3 | `LoadHTMLWithUrlOverride` | 1:22 |
| 5 | `const` | 1:46 |
| 6 | `char` | 1:52 |
| 8 | `html` | 1:58 |
| 10 | `const` | 2:46 |
| 11 | `char` | 2:52 |
| 13 | `url_override` | 2:58 |
| 16 | `GetMainFrame` | 3:3 |
| 20 | `LoadHTMLString` | 3:19 |
| 22 | `std` | 3:34 |
| 24 | `string` | 3:39 |
| 26 | `html` | 3:46 |
| 29 | `blink` | 4:34 |
| 31 | `WebURL` | 4:41 |
| 33 | `GURL` | 4:48 |
| 35 | `url_override` | 4:53 |
| 40 | `FrameLoadWaiter` | 5:3 |
| 42 | `view_` | 5:19 |
| 44 | `GetMainRenderFrame` | 5:26 |
| 49 | `Wait` | 5:48 |
| 53 | `view_` | 6:3 |
| 55 | `GetWebView` | 6:10 |
| 59 | `UpdateAllLifecyclePhases` | 6:24 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'void'` |
| 2 | `'Render'` |
| 3 | `'View'` |
| 4 | `'Test'` |
| 5 | `'::'` |
| 6 | `'Load'` |
| 7 | `'HTML'` |
| 8 | `'With'` |
| 9 | `'Url'` |
| 10 | `'Override'` |
| 11 | `'('` |
| 12 | `'const'` |
| 13 | `'char'` |
| 14 | `'*'` |
| 15 | `'html'` |
| 16 | `','` |
| 17 | `'\n'` |
| 62 | `'const'` |
| 63 | `'char'` |
| 64 | `'*'` |
| 65 | `'url'` |
| 66 | `'_'` |
| 67 | `'over'` |
| 68 | `'ride'` |
| 69 | `')'` |
| 70 | `'{'` |
| 71 | `'\n'` |
| 73 | `'Get'` |
| 74 | `'Main'` |
| 75 | `'Frame'` |
| 76 | `'()'` |
| 77 | `'->'` |
| 78 | `'Load'` |
| 79 | `'HTML'` |
| 80 | `'String'` |
| 81 | `'('` |
| 82 | `'std'` |
| 83 | `'::'` |
| 84 | `'string'` |
| 85 | `'('` |
| 86 | `'html'` |
| 87 | `'),'` |
| 88 | `'\n'` |
| 121 | `'blink'` |
| 122 | `'::'` |
| 123 | `'Web'` |
| 124 | `'URL'` |
| 125 | `'('` |
| 126 | `'G'` |
| 127 | `'URL'` |
| 128 | `'('` |
| 129 | `'url'` |
| 130 | `'_'` |
| 131 | `'over'` |
| 132 | `'ride'` |
| 133 | `'))'` |
| 134 | `');'` |
| 135 | `'\n'` |
| 137 | `'Frame'` |
| 138 | `'Load'` |
| 139 | `'Wa'` |
| 140 | `'iter'` |
| 141 | `'('` |
| 142 | `'view'` |
| 143 | `'_'` |
| 144 | `'->'` |
| 145 | `'Get'` |
| 146 | `'Main'` |
| 147 | `'Render'` |
| 148 | `'Frame'` |
| 149 | `'()'` |
| 150 | `').'` |
| 151 | `'Wait'` |
| 152 | `'();'` |
| 153 | `'\n'` |
| 155 | `'view'` |
| 156 | `'_'` |
| 157 | `'->'` |
| 158 | `'Get'` |
| 159 | `'Web'` |
| 160 | `'View'` |
| 161 | `'()'` |
| 162 | `'->'` |
| 163 | `'Update'` |
| 164 | `'All'` |
| 165 | `'L'` |
| 166 | `'if'` |
| 167 | `'ecycle'` |
| 168 | `'Ph'` |
| 169 | `'ases'` |
| 170 | `'();'` |
| 171 | `'\n'` |
| 172 | `'}'` |
| 173 | `'\n'` |
