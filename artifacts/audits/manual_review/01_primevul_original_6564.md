# Review 01: `primevul:original:6564` (cpp)

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
   1 | ServiceWorkerContainer* NavigatorServiceWorker::serviceWorker(Navigator& navigator, ExceptionState& exceptionState)
   2 |  {
   3 |      return NavigatorServiceWorker::from(navigator).serviceWorker(exceptionState);
   4 |  }
   5 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `ServiceWorkerContainer` | 1:1 |
| 2 | `NavigatorServiceWorker` | 1:25 |
| 4 | `serviceWorker` | 1:49 |
| 6 | `Navigator` | 1:63 |
| 8 | `navigator` | 1:74 |
| 10 | `ExceptionState` | 1:85 |
| 12 | `exceptionState` | 1:101 |
| 15 | `return` | 3:6 |
| 16 | `NavigatorServiceWorker` | 3:13 |
| 18 | `from` | 3:37 |
| 20 | `navigator` | 3:42 |
| 23 | `serviceWorker` | 3:53 |
| 25 | `exceptionState` | 3:67 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'Service'` |
| 2 | `'Work'` |
| 3 | `'er'` |
| 4 | `'Container'` |
| 5 | `'*'` |
| 6 | `'Nav'` |
| 7 | `'igator'` |
| 8 | `'Service'` |
| 9 | `'Work'` |
| 10 | `'er'` |
| 11 | `'::'` |
| 12 | `'service'` |
| 13 | `'Work'` |
| 14 | `'er'` |
| 15 | `'('` |
| 16 | `'Nav'` |
| 17 | `'igator'` |
| 18 | `'&'` |
| 19 | `'navig'` |
| 20 | `'ator'` |
| 21 | `','` |
| 22 | `'Exception'` |
| 23 | `'State'` |
| 24 | `'&'` |
| 25 | `'exception'` |
| 26 | `'State'` |
| 27 | `')'` |
| 28 | `'\n'` |
| 29 | `'{'` |
| 30 | `'\n'` |
| 35 | `'return'` |
| 36 | `'Nav'` |
| 37 | `'igator'` |
| 38 | `'Service'` |
| 39 | `'Work'` |
| 40 | `'er'` |
| 41 | `'::'` |
| 42 | `'from'` |
| 43 | `'('` |
| 44 | `'nav'` |
| 45 | `'igator'` |
| 46 | `').'` |
| 47 | `'service'` |
| 48 | `'Work'` |
| 49 | `'er'` |
| 50 | `'('` |
| 51 | `'ex'` |
| 52 | `'ception'` |
| 53 | `'State'` |
| 54 | `');'` |
| 55 | `'\n'` |
| 56 | `'}'` |
| 57 | `'\n'` |
