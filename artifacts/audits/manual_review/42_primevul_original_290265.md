# Review 42: `primevul:original:290265` (cpp)

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
   1 | void ConnectDialog::on_qaFavoriteAdd_triggered() {
   2 | 	ServerItem *si = static_cast<ServerItem *>(qtwServers->currentItem());
   3 | 	if (! si || (si->itType == ServerItem::FavoriteType))
   4 | 		return;
   5 | 
   6 | 	si = new ServerItem(si);
   7 | 	qtwServers->fixupName(si);
   8 | 	qlItems << si;
   9 | 	qtwServers->siFavorite->addServerItem(si);
  10 | 	qtwServers->setCurrentItem(si);
  11 | 	startDns(si);
  12 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `void` | 1:1 |
| 1 | `ConnectDialog` | 1:6 |
| 3 | `on_qaFavoriteAdd_triggered` | 1:21 |
| 7 | `ServerItem` | 2:2 |
| 9 | `si` | 2:14 |
| 11 | `static_cast` | 2:19 |
| 13 | `ServerItem` | 2:31 |
| 17 | `qtwServers` | 2:45 |
| 19 | `currentItem` | 2:57 |
| 24 | `if` | 3:2 |
| 27 | `si` | 3:8 |
| 30 | `si` | 3:15 |
| 32 | `itType` | 3:19 |
| 34 | `ServerItem` | 3:29 |
| 36 | `FavoriteType` | 3:41 |
| 39 | `return` | 4:3 |
| 41 | `si` | 6:2 |
| 43 | `new` | 6:7 |
| 44 | `ServerItem` | 6:11 |
| 46 | `si` | 6:22 |
| 49 | `qtwServers` | 7:2 |
| 51 | `fixupName` | 7:14 |
| 53 | `si` | 7:24 |
| 56 | `qlItems` | 8:2 |
| 58 | `si` | 8:13 |
| 60 | `qtwServers` | 9:2 |
| 62 | `siFavorite` | 9:14 |
| 64 | `addServerItem` | 9:26 |
| 66 | `si` | 9:40 |
| 69 | `qtwServers` | 10:2 |
| 71 | `setCurrentItem` | 10:14 |
| 73 | `si` | 10:29 |
| 76 | `startDns` | 11:2 |
| 78 | `si` | 11:11 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'void'` |
| 2 | `'Connect'` |
| 3 | `'Dialog'` |
| 4 | `'::'` |
| 5 | `'on'` |
| 6 | `'_'` |
| 7 | `'qa'` |
| 8 | `'Favorite'` |
| 9 | `'Add'` |
| 10 | `'_'` |
| 11 | `'tr'` |
| 12 | `'ig'` |
| 13 | `'gered'` |
| 14 | `'()'` |
| 15 | `'{'` |
| 16 | `'\n'` |
| 17 | `'\t'` |
| 18 | `'Server'` |
| 19 | `'Item'` |
| 20 | `'*'` |
| 21 | `'si'` |
| 22 | `'='` |
| 23 | `'static'` |
| 24 | `'_'` |
| 25 | `'cast'` |
| 26 | `'<'` |
| 27 | `'Server'` |
| 28 | `'Item'` |
| 29 | `'*'` |
| 30 | `'>('` |
| 31 | `'q'` |
| 32 | `'tw'` |
| 33 | `'Ser'` |
| 34 | `'vers'` |
| 35 | `'->'` |
| 36 | `'current'` |
| 37 | `'Item'` |
| 38 | `'());'` |
| 39 | `'\n'` |
| 40 | `'\t'` |
| 41 | `'if'` |
| 42 | `'(!'` |
| 43 | `'si'` |
| 44 | `'||'` |
| 45 | `'('` |
| 46 | `'si'` |
| 47 | `'->'` |
| 48 | `'it'` |
| 49 | `'Type'` |
| 50 | `'=='` |
| 51 | `'Server'` |
| 52 | `'Item'` |
| 53 | `'::'` |
| 54 | `'Favorite'` |
| 55 | `'Type'` |
| 56 | `'))'` |
| 57 | `'\n'` |
| 58 | `'\t'` |
| 59 | `'\t'` |
| 60 | `'return'` |
| 61 | `';'` |
| 62 | `'\n\n'` |
| 63 | `'\t'` |
| 64 | `'si'` |
| 65 | `'='` |
| 66 | `'new'` |
| 67 | `'Server'` |
| 68 | `'Item'` |
| 69 | `'('` |
| 70 | `'si'` |
| 71 | `');'` |
| 72 | `'\n'` |
| 73 | `'\t'` |
| 74 | `'q'` |
| 75 | `'tw'` |
| 76 | `'Ser'` |
| 77 | `'vers'` |
| 78 | `'->'` |
| 79 | `'fix'` |
| 80 | `'up'` |
| 81 | `'Name'` |
| 82 | `'('` |
| 83 | `'si'` |
| 84 | `');'` |
| 85 | `'\n'` |
| 86 | `'\t'` |
| 87 | `'ql'` |
| 88 | `'Items'` |
| 89 | `'<<'` |
| 90 | `'si'` |
| 91 | `';'` |
| 92 | `'\n'` |
| 93 | `'\t'` |
| 94 | `'q'` |
| 95 | `'tw'` |
| 96 | `'Ser'` |
| 97 | `'vers'` |
| 98 | `'->'` |
| 99 | `'si'` |
| 100 | `'Favorite'` |
| 101 | `'->'` |
| 102 | `'add'` |
| 103 | `'Server'` |
| 104 | `'Item'` |
| 105 | `'('` |
| 106 | `'si'` |
| 107 | `');'` |
| 108 | `'\n'` |
| 109 | `'\t'` |
| 110 | `'q'` |
| 111 | `'tw'` |
| 112 | `'Ser'` |
| 113 | `'vers'` |
| 114 | `'->'` |
| 115 | `'set'` |
| 116 | `'Current'` |
| 117 | `'Item'` |
| 118 | `'('` |
| 119 | `'si'` |
| 120 | `');'` |
| 121 | `'\n'` |
| 122 | `'\t'` |
| 123 | `'start'` |
| 124 | `'D'` |
| 125 | `'ns'` |
| 126 | `'('` |
| 127 | `'si'` |
| 128 | `');'` |
| 129 | `'\n'` |
| 130 | `'}'` |
