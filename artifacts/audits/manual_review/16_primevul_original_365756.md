# Review 16: `primevul:original:365756` (c)

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
   1 | static int generate_rms_keys(gnutls_session_t session)
   2 | {
   3 | 	int ret;
   4 | 
   5 | 	ret = _tls13_derive_secret(session, RMS_MASTER_LABEL, sizeof(RMS_MASTER_LABEL)-1,
   6 | 				   session->internals.handshake_hash_buffer.data,
   7 | 				   session->internals.handshake_hash_buffer_client_finished_len,
   8 | 				   session->key.proto.tls13.temp_secret,
   9 | 				   session->key.proto.tls13.ap_rms);
  10 | 	if (ret < 0)
  11 | 		return gnutls_assert_val(ret);
  12 | 
  13 | 	return 0;
  14 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `int` | 1:8 |
| 2 | `generate_rms_keys` | 1:12 |
| 4 | `gnutls_session_t` | 1:30 |
| 5 | `session` | 1:47 |
| 8 | `int` | 3:2 |
| 9 | `ret` | 3:6 |
| 11 | `ret` | 5:2 |
| 13 | `_tls13_derive_secret` | 5:8 |
| 15 | `session` | 5:29 |
| 17 | `RMS_MASTER_LABEL` | 5:38 |
| 19 | `sizeof` | 5:56 |
| 21 | `RMS_MASTER_LABEL` | 5:63 |
| 26 | `session` | 6:8 |
| 28 | `internals` | 6:17 |
| 30 | `handshake_hash_buffer` | 6:27 |
| 32 | `data` | 6:49 |
| 34 | `session` | 7:8 |
| 36 | `internals` | 7:17 |
| 38 | `handshake_hash_buffer_client_finished_len` | 7:27 |
| 40 | `session` | 8:8 |
| 42 | `key` | 8:17 |
| 44 | `proto` | 8:21 |
| 46 | `tls13` | 8:27 |
| 48 | `temp_secret` | 8:33 |
| 50 | `session` | 9:8 |
| 52 | `key` | 9:17 |
| 54 | `proto` | 9:21 |
| 56 | `tls13` | 9:27 |
| 58 | `ap_rms` | 9:33 |
| 61 | `if` | 10:2 |
| 63 | `ret` | 10:6 |
| 67 | `return` | 11:3 |
| 68 | `gnutls_assert_val` | 11:10 |
| 70 | `ret` | 11:28 |
| 73 | `return` | 13:2 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'int'` |
| 3 | `'generate'` |
| 4 | `'_'` |
| 5 | `'r'` |
| 6 | `'ms'` |
| 7 | `'_'` |
| 8 | `'keys'` |
| 9 | `'('` |
| 10 | `'gn'` |
| 11 | `'ut'` |
| 12 | `'ls'` |
| 13 | `'_'` |
| 14 | `'session'` |
| 15 | `'_'` |
| 16 | `'t'` |
| 17 | `'session'` |
| 18 | `')'` |
| 19 | `'\n'` |
| 20 | `'{'` |
| 21 | `'\n'` |
| 22 | `'\t'` |
| 23 | `'int'` |
| 24 | `'ret'` |
| 25 | `';'` |
| 26 | `'\n\n'` |
| 27 | `'\t'` |
| 28 | `'ret'` |
| 29 | `'='` |
| 30 | `'_'` |
| 31 | `'t'` |
| 32 | `'ls'` |
| 33 | `'13'` |
| 34 | `'_'` |
| 35 | `'der'` |
| 36 | `'ive'` |
| 37 | `'_'` |
| 38 | `'secret'` |
| 39 | `'('` |
| 40 | `'session'` |
| 41 | `','` |
| 42 | `'R'` |
| 43 | `'MS'` |
| 44 | `'_'` |
| 45 | `'MAS'` |
| 46 | `'TER'` |
| 47 | `'_'` |
| 48 | `'LAB'` |
| 49 | `'EL'` |
| 50 | `','` |
| 51 | `'sizeof'` |
| 52 | `'('` |
| 53 | `'R'` |
| 54 | `'MS'` |
| 55 | `'_'` |
| 56 | `'MAS'` |
| 57 | `'TER'` |
| 58 | `'_'` |
| 59 | `'LAB'` |
| 60 | `'EL'` |
| 61 | `')-'` |
| 62 | `'1'` |
| 63 | `','` |
| 64 | `'\n'` |
| 65 | `'\t'` |
| 66 | `'\t'` |
| 67 | `'\t'` |
| 68 | `'\t'` |
| 71 | `'session'` |
| 72 | `'->'` |
| 73 | `'intern'` |
| 74 | `'als'` |
| 75 | `'.'` |
| 76 | `'hand'` |
| 77 | `'shake'` |
| 78 | `'_'` |
| 79 | `'hash'` |
| 80 | `'_'` |
| 81 | `'buffer'` |
| 82 | `'.'` |
| 83 | `'data'` |
| 84 | `','` |
| 85 | `'\n'` |
| 86 | `'\t'` |
| 87 | `'\t'` |
| 88 | `'\t'` |
| 89 | `'\t'` |
| 92 | `'session'` |
| 93 | `'->'` |
| 94 | `'intern'` |
| 95 | `'als'` |
| 96 | `'.'` |
| 97 | `'hand'` |
| 98 | `'shake'` |
| 99 | `'_'` |
| 100 | `'hash'` |
| 101 | `'_'` |
| 102 | `'buffer'` |
| 103 | `'_'` |
| 104 | `'client'` |
| 105 | `'_'` |
| 106 | `'finished'` |
| 107 | `'_'` |
| 108 | `'len'` |
| 109 | `','` |
| 110 | `'\n'` |
| 111 | `'\t'` |
| 112 | `'\t'` |
| 113 | `'\t'` |
| 114 | `'\t'` |
| 117 | `'session'` |
| 118 | `'->'` |
| 119 | `'key'` |
| 120 | `'.'` |
| 121 | `'pro'` |
| 122 | `'to'` |
| 123 | `'.'` |
| 124 | `'t'` |
| 125 | `'ls'` |
| 126 | `'13'` |
| 127 | `'.'` |
| 128 | `'temp'` |
| 129 | `'_'` |
| 130 | `'secret'` |
| 131 | `','` |
| 132 | `'\n'` |
| 133 | `'\t'` |
| 134 | `'\t'` |
| 135 | `'\t'` |
| 136 | `'\t'` |
| 139 | `'session'` |
| 140 | `'->'` |
| 141 | `'key'` |
| 142 | `'.'` |
| 143 | `'pro'` |
| 144 | `'to'` |
| 145 | `'.'` |
| 146 | `'t'` |
| 147 | `'ls'` |
| 148 | `'13'` |
| 149 | `'.'` |
| 150 | `'ap'` |
| 151 | `'_'` |
| 152 | `'r'` |
| 153 | `'ms'` |
| 154 | `');'` |
| 155 | `'\n'` |
| 156 | `'\t'` |
| 157 | `'if'` |
| 158 | `'('` |
| 159 | `'ret'` |
| 160 | `'<'` |
| 161 | `'0'` |
| 162 | `')'` |
| 163 | `'\n'` |
| 164 | `'\t'` |
| 165 | `'\t'` |
| 166 | `'return'` |
| 167 | `'g'` |
| 168 | `'nut'` |
| 169 | `'ls'` |
| 170 | `'_'` |
| 171 | `'assert'` |
| 172 | `'_'` |
| 173 | `'val'` |
| 174 | `'('` |
| 175 | `'ret'` |
| 176 | `');'` |
| 177 | `'\n\n'` |
| 178 | `'\t'` |
| 179 | `'return'` |
| 180 | `'0'` |
| 181 | `';'` |
| 182 | `'\n'` |
| 183 | `'}'` |
