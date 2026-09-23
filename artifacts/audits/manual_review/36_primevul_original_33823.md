# Review 36: `primevul:original:33823` (c)

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
   1 | static int tg3_abort_hw(struct tg3 *tp, int silent)
   2 | {
   3 | 	int i, err;
   4 | 
   5 | 	tg3_disable_ints(tp);
   6 | 
   7 | 	tp->rx_mode &= ~RX_MODE_ENABLE;
   8 | 	tw32_f(MAC_RX_MODE, tp->rx_mode);
   9 | 	udelay(10);
  10 | 
  11 | 	err  = tg3_stop_block(tp, RCVBDI_MODE, RCVBDI_MODE_ENABLE, silent);
  12 | 	err |= tg3_stop_block(tp, RCVLPC_MODE, RCVLPC_MODE_ENABLE, silent);
  13 | 	err |= tg3_stop_block(tp, RCVLSC_MODE, RCVLSC_MODE_ENABLE, silent);
  14 | 	err |= tg3_stop_block(tp, RCVDBDI_MODE, RCVDBDI_MODE_ENABLE, silent);
  15 | 	err |= tg3_stop_block(tp, RCVDCC_MODE, RCVDCC_MODE_ENABLE, silent);
  16 | 	err |= tg3_stop_block(tp, RCVCC_MODE, RCVCC_MODE_ENABLE, silent);
  17 | 
  18 | 	err |= tg3_stop_block(tp, SNDBDS_MODE, SNDBDS_MODE_ENABLE, silent);
  19 | 	err |= tg3_stop_block(tp, SNDBDI_MODE, SNDBDI_MODE_ENABLE, silent);
  20 | 	err |= tg3_stop_block(tp, SNDDATAI_MODE, SNDDATAI_MODE_ENABLE, silent);
  21 | 	err |= tg3_stop_block(tp, RDMAC_MODE, RDMAC_MODE_ENABLE, silent);
  22 | 	err |= tg3_stop_block(tp, SNDDATAC_MODE, SNDDATAC_MODE_ENABLE, silent);
  23 | 	err |= tg3_stop_block(tp, DMAC_MODE, DMAC_MODE_ENABLE, silent);
  24 | 	err |= tg3_stop_block(tp, SNDBDC_MODE, SNDBDC_MODE_ENABLE, silent);
  25 | 
  26 | 	tp->mac_mode &= ~MAC_MODE_TDE_ENABLE;
  27 | 	tw32_f(MAC_MODE, tp->mac_mode);
  28 | 	udelay(40);
  29 | 
  30 | 	tp->tx_mode &= ~TX_MODE_ENABLE;
  31 | 	tw32_f(MAC_TX_MODE, tp->tx_mode);
  32 | 
  33 | 	for (i = 0; i < MAX_WAIT_CNT; i++) {
  34 | 		udelay(100);
  35 | 		if (!(tr32(MAC_TX_MODE) & TX_MODE_ENABLE))
  36 | 			break;
  37 | 	}
  38 | 	if (i >= MAX_WAIT_CNT) {
  39 | 		dev_err(&tp->pdev->dev,
  40 | 			"%s timed out, TX_MODE_ENABLE will not clear "
  41 | 			"MAC_TX_MODE=%08x\n", __func__, tr32(MAC_TX_MODE));
  42 | 		err |= -ENODEV;
  43 | 	}
  44 | 
  45 | 	err |= tg3_stop_block(tp, HOSTCC_MODE, HOSTCC_MODE_ENABLE, silent);
  46 | 	err |= tg3_stop_block(tp, WDMAC_MODE, WDMAC_MODE_ENABLE, silent);
  47 | 	err |= tg3_stop_block(tp, MBFREE_MODE, MBFREE_MODE_ENABLE, silent);
  48 | 
  49 | 	tw32(FTQ_RESET, 0xffffffff);
  50 | 	tw32(FTQ_RESET, 0x00000000);
  51 | 
  52 | 	err |= tg3_stop_block(tp, BUFMGR_MODE, BUFMGR_MODE_ENABLE, silent);
  53 | 	err |= tg3_stop_block(tp, MEMARB_MODE, MEMARB_MODE_ENABLE, silent);
  54 | 
  55 | 	for (i = 0; i < tp->irq_cnt; i++) {
  56 | 		struct tg3_napi *tnapi = &tp->napi[i];
  57 | 		if (tnapi->hw_status)
  58 | 			memset(tnapi->hw_status, 0, TG3_HW_STATUS_SIZE);
  59 | 	}
  60 | 
  61 | 	return err;
  62 | }
  63 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `int` | 1:8 |
| 2 | `tg3_abort_hw` | 1:12 |
| 4 | `struct` | 1:25 |
| 5 | `tg3` | 1:32 |
| 7 | `tp` | 1:37 |
| 9 | `int` | 1:41 |
| 10 | `silent` | 1:45 |
| 13 | `int` | 3:2 |
| 14 | `i` | 3:6 |
| 16 | `err` | 3:9 |
| 18 | `tg3_disable_ints` | 5:2 |
| 20 | `tp` | 5:19 |
| 23 | `tp` | 7:2 |
| 25 | `rx_mode` | 7:6 |
| 28 | `RX_MODE_ENABLE` | 7:18 |
| 30 | `tw32_f` | 8:2 |
| 32 | `MAC_RX_MODE` | 8:9 |
| 34 | `tp` | 8:22 |
| 36 | `rx_mode` | 8:26 |
| 39 | `udelay` | 9:2 |
| 44 | `err` | 11:2 |
| 46 | `tg3_stop_block` | 11:9 |
| 48 | `tp` | 11:24 |
| 50 | `RCVBDI_MODE` | 11:28 |
| 52 | `RCVBDI_MODE_ENABLE` | 11:41 |
| 54 | `silent` | 11:61 |
| 57 | `err` | 12:2 |
| 59 | `tg3_stop_block` | 12:9 |
| 61 | `tp` | 12:24 |
| 63 | `RCVLPC_MODE` | 12:28 |
| 65 | `RCVLPC_MODE_ENABLE` | 12:41 |
| 67 | `silent` | 12:61 |
| 70 | `err` | 13:2 |
| 72 | `tg3_stop_block` | 13:9 |
| 74 | `tp` | 13:24 |
| 76 | `RCVLSC_MODE` | 13:28 |
| 78 | `RCVLSC_MODE_ENABLE` | 13:41 |
| 80 | `silent` | 13:61 |
| 83 | `err` | 14:2 |
| 85 | `tg3_stop_block` | 14:9 |
| 87 | `tp` | 14:24 |
| 89 | `RCVDBDI_MODE` | 14:28 |
| 91 | `RCVDBDI_MODE_ENABLE` | 14:42 |
| 93 | `silent` | 14:63 |
| 96 | `err` | 15:2 |
| 98 | `tg3_stop_block` | 15:9 |
| 100 | `tp` | 15:24 |
| 102 | `RCVDCC_MODE` | 15:28 |
| 104 | `RCVDCC_MODE_ENABLE` | 15:41 |
| 106 | `silent` | 15:61 |
| 109 | `err` | 16:2 |
| 111 | `tg3_stop_block` | 16:9 |
| 113 | `tp` | 16:24 |
| 115 | `RCVCC_MODE` | 16:28 |
| 117 | `RCVCC_MODE_ENABLE` | 16:40 |
| 119 | `silent` | 16:59 |
| 122 | `err` | 18:2 |
| 124 | `tg3_stop_block` | 18:9 |
| 126 | `tp` | 18:24 |
| 128 | `SNDBDS_MODE` | 18:28 |
| 130 | `SNDBDS_MODE_ENABLE` | 18:41 |
| 132 | `silent` | 18:61 |
| 135 | `err` | 19:2 |
| 137 | `tg3_stop_block` | 19:9 |
| 139 | `tp` | 19:24 |
| 141 | `SNDBDI_MODE` | 19:28 |
| 143 | `SNDBDI_MODE_ENABLE` | 19:41 |
| 145 | `silent` | 19:61 |
| 148 | `err` | 20:2 |
| 150 | `tg3_stop_block` | 20:9 |
| 152 | `tp` | 20:24 |
| 154 | `SNDDATAI_MODE` | 20:28 |
| 156 | `SNDDATAI_MODE_ENABLE` | 20:43 |
| 158 | `silent` | 20:65 |
| 161 | `err` | 21:2 |
| 163 | `tg3_stop_block` | 21:9 |
| 165 | `tp` | 21:24 |
| 167 | `RDMAC_MODE` | 21:28 |
| 169 | `RDMAC_MODE_ENABLE` | 21:40 |
| 171 | `silent` | 21:59 |
| 174 | `err` | 22:2 |
| 176 | `tg3_stop_block` | 22:9 |
| 178 | `tp` | 22:24 |
| 180 | `SNDDATAC_MODE` | 22:28 |
| 182 | `SNDDATAC_MODE_ENABLE` | 22:43 |
| 184 | `silent` | 22:65 |
| 187 | `err` | 23:2 |
| 189 | `tg3_stop_block` | 23:9 |
| 191 | `tp` | 23:24 |
| 193 | `DMAC_MODE` | 23:28 |
| 195 | `DMAC_MODE_ENABLE` | 23:39 |
| 197 | `silent` | 23:57 |
| 200 | `err` | 24:2 |
| 202 | `tg3_stop_block` | 24:9 |
| 204 | `tp` | 24:24 |
| 206 | `SNDBDC_MODE` | 24:28 |
| 208 | `SNDBDC_MODE_ENABLE` | 24:41 |
| 210 | `silent` | 24:61 |
| 213 | `tp` | 26:2 |
| 215 | `mac_mode` | 26:6 |
| 218 | `MAC_MODE_TDE_ENABLE` | 26:19 |
| 220 | `tw32_f` | 27:2 |
| 222 | `MAC_MODE` | 27:9 |
| 224 | `tp` | 27:19 |
| 226 | `mac_mode` | 27:23 |
| 229 | `udelay` | 28:2 |
| 234 | `tp` | 30:2 |
| 236 | `tx_mode` | 30:6 |
| 239 | `TX_MODE_ENABLE` | 30:18 |
| 241 | `tw32_f` | 31:2 |
| 243 | `MAC_TX_MODE` | 31:9 |
| 245 | `tp` | 31:22 |
| 247 | `tx_mode` | 31:26 |
| 250 | `for` | 33:2 |
| 252 | `i` | 33:7 |
| 256 | `i` | 33:14 |
| 258 | `MAX_WAIT_CNT` | 33:18 |
| 260 | `i` | 33:32 |
| 264 | `udelay` | 34:3 |
| 269 | `if` | 35:3 |
| 273 | `tr32` | 35:9 |
| 275 | `MAC_TX_MODE` | 35:14 |
| 278 | `TX_MODE_ENABLE` | 35:29 |
| 281 | `break` | 36:4 |
| 284 | `if` | 38:2 |
| 286 | `i` | 38:6 |
| 288 | `MAX_WAIT_CNT` | 38:11 |
| 291 | `dev_err` | 39:3 |
| 294 | `tp` | 39:12 |
| 296 | `pdev` | 39:16 |
| 298 | `dev` | 39:22 |
| 303 | `__func__` | 41:26 |
| 305 | `tr32` | 41:36 |
| 307 | `MAC_TX_MODE` | 41:41 |
| 311 | `err` | 42:3 |
| 314 | `ENODEV` | 42:11 |
| 317 | `err` | 45:2 |
| 319 | `tg3_stop_block` | 45:9 |
| 321 | `tp` | 45:24 |
| 323 | `HOSTCC_MODE` | 45:28 |
| 325 | `HOSTCC_MODE_ENABLE` | 45:41 |
| 327 | `silent` | 45:61 |
| 330 | `err` | 46:2 |
| 332 | `tg3_stop_block` | 46:9 |
| 334 | `tp` | 46:24 |
| 336 | `WDMAC_MODE` | 46:28 |
| 338 | `WDMAC_MODE_ENABLE` | 46:40 |
| 340 | `silent` | 46:59 |
| 343 | `err` | 47:2 |
| 345 | `tg3_stop_block` | 47:9 |
| 347 | `tp` | 47:24 |
| 349 | `MBFREE_MODE` | 47:28 |
| 351 | `MBFREE_MODE_ENABLE` | 47:41 |
| 353 | `silent` | 47:61 |
| 356 | `tw32` | 49:2 |
| 358 | `FTQ_RESET` | 49:7 |
| 363 | `tw32` | 50:2 |
| 365 | `FTQ_RESET` | 50:7 |
| 370 | `err` | 52:2 |
| 372 | `tg3_stop_block` | 52:9 |
| 374 | `tp` | 52:24 |
| 376 | `BUFMGR_MODE` | 52:28 |
| 378 | `BUFMGR_MODE_ENABLE` | 52:41 |
| 380 | `silent` | 52:61 |
| 383 | `err` | 53:2 |
| 385 | `tg3_stop_block` | 53:9 |
| 387 | `tp` | 53:24 |
| 389 | `MEMARB_MODE` | 53:28 |
| 391 | `MEMARB_MODE_ENABLE` | 53:41 |
| 393 | `silent` | 53:61 |
| 396 | `for` | 55:2 |
| 398 | `i` | 55:7 |
| 402 | `i` | 55:14 |
| 404 | `tp` | 55:18 |
| 406 | `irq_cnt` | 55:22 |
| 408 | `i` | 55:31 |
| 412 | `struct` | 56:3 |
| 413 | `tg3_napi` | 56:10 |
| 415 | `tnapi` | 56:20 |
| 418 | `tp` | 56:29 |
| 420 | `napi` | 56:33 |
| 422 | `i` | 56:38 |
| 425 | `if` | 57:3 |
| 427 | `tnapi` | 57:7 |
| 429 | `hw_status` | 57:14 |
| 431 | `memset` | 58:4 |
| 433 | `tnapi` | 58:11 |
| 435 | `hw_status` | 58:18 |
| 439 | `TG3_HW_STATUS_SIZE` | 58:32 |
| 443 | `return` | 61:2 |
| 444 | `err` | 61:9 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'int'` |
| 3 | `'t'` |
| 4 | `'g'` |
| 5 | `'3'` |
| 6 | `'_'` |
| 7 | `'ab'` |
| 8 | `'ort'` |
| 9 | `'_'` |
| 10 | `'hw'` |
| 11 | `'('` |
| 12 | `'struct'` |
| 13 | `'t'` |
| 14 | `'g'` |
| 15 | `'3'` |
| 16 | `'*'` |
| 17 | `'tp'` |
| 18 | `','` |
| 19 | `'int'` |
| 20 | `'silent'` |
| 21 | `')'` |
| 22 | `'\n'` |
| 23 | `'{'` |
| 24 | `'\n'` |
| 25 | `'\t'` |
| 26 | `'int'` |
| 27 | `'i'` |
| 28 | `','` |
| 29 | `'err'` |
| 30 | `';'` |
| 31 | `'\n\n'` |
| 32 | `'\t'` |
| 33 | `'tg'` |
| 34 | `'3'` |
| 35 | `'_'` |
| 36 | `'disable'` |
| 37 | `'_'` |
| 38 | `'ints'` |
| 39 | `'('` |
| 40 | `'tp'` |
| 41 | `');'` |
| 42 | `'\n\n'` |
| 43 | `'\t'` |
| 44 | `'tp'` |
| 45 | `'->'` |
| 46 | `'rx'` |
| 47 | `'_'` |
| 48 | `'mode'` |
| 49 | `'&'` |
| 50 | `'='` |
| 51 | `'~'` |
| 52 | `'R'` |
| 53 | `'X'` |
| 54 | `'_'` |
| 55 | `'MODE'` |
| 56 | `'_'` |
| 57 | `'EN'` |
| 58 | `'ABLE'` |
| 59 | `';'` |
| 60 | `'\n'` |
| 61 | `'\t'` |
| 62 | `'tw'` |
| 63 | `'32'` |
| 64 | `'_'` |
| 65 | `'f'` |
| 66 | `'('` |
| 67 | `'MAC'` |
| 68 | `'_'` |
| 69 | `'R'` |
| 70 | `'X'` |
| 71 | `'_'` |
| 72 | `'MODE'` |
| 73 | `','` |
| 74 | `'t'` |
| 75 | `'p'` |
| 76 | `'->'` |
| 77 | `'rx'` |
| 78 | `'_'` |
| 79 | `'mode'` |
| 80 | `');'` |
| 81 | `'\n'` |
| 82 | `'\t'` |
| 83 | `'ud'` |
| 84 | `'el'` |
| 85 | `'ay'` |
| 86 | `'('` |
| 87 | `'10'` |
| 88 | `');'` |
| 89 | `'\n\n'` |
| 90 | `'\t'` |
| 91 | `'err'` |
| 93 | `'='` |
| 94 | `'t'` |
| 95 | `'g'` |
| 96 | `'3'` |
| 97 | `'_'` |
| 98 | `'stop'` |
| 99 | `'_'` |
| 100 | `'block'` |
| 101 | `'('` |
| 102 | `'tp'` |
| 103 | `','` |
| 104 | `'RC'` |
| 105 | `'V'` |
| 106 | `'BD'` |
| 107 | `'I'` |
| 108 | `'_'` |
| 109 | `'MODE'` |
| 110 | `','` |
| 111 | `'RC'` |
| 112 | `'V'` |
| 113 | `'BD'` |
| 114 | `'I'` |
| 115 | `'_'` |
| 116 | `'MODE'` |
| 117 | `'_'` |
| 118 | `'EN'` |
| 119 | `'ABLE'` |
| 120 | `','` |
| 121 | `'silent'` |
| 122 | `');'` |
| 123 | `'\n'` |
| 124 | `'\t'` |
| 125 | `'err'` |
| 126 | `'|'` |
| 127 | `'='` |
| 128 | `'t'` |
| 129 | `'g'` |
| 130 | `'3'` |
| 131 | `'_'` |
| 132 | `'stop'` |
| 133 | `'_'` |
| 134 | `'block'` |
| 135 | `'('` |
| 136 | `'tp'` |
| 137 | `','` |
| 138 | `'RC'` |
| 139 | `'VL'` |
| 140 | `'PC'` |
| 141 | `'_'` |
| 142 | `'MODE'` |
| 143 | `','` |
| 144 | `'RC'` |
| 145 | `'VL'` |
| 146 | `'PC'` |
| 147 | `'_'` |
| 148 | `'MODE'` |
| 149 | `'_'` |
| 150 | `'EN'` |
| 151 | `'ABLE'` |
| 152 | `','` |
| 153 | `'silent'` |
| 154 | `');'` |
| 155 | `'\n'` |
| 156 | `'\t'` |
| 157 | `'err'` |
| 158 | `'|'` |
| 159 | `'='` |
| 160 | `'t'` |
| 161 | `'g'` |
| 162 | `'3'` |
| 163 | `'_'` |
| 164 | `'stop'` |
| 165 | `'_'` |
| 166 | `'block'` |
| 167 | `'('` |
| 168 | `'tp'` |
| 169 | `','` |
| 170 | `'RC'` |
| 171 | `'VL'` |
| 172 | `'SC'` |
| 173 | `'_'` |
| 174 | `'MODE'` |
| 175 | `','` |
| 176 | `'RC'` |
| 177 | `'VL'` |
| 178 | `'SC'` |
| 179 | `'_'` |
| 180 | `'MODE'` |
| 181 | `'_'` |
| 182 | `'EN'` |
| 183 | `'ABLE'` |
| 184 | `','` |
| 185 | `'silent'` |
| 186 | `');'` |
| 187 | `'\n'` |
| 188 | `'\t'` |
| 189 | `'err'` |
| 190 | `'|'` |
| 191 | `'='` |
| 192 | `'t'` |
| 193 | `'g'` |
| 194 | `'3'` |
| 195 | `'_'` |
| 196 | `'stop'` |
| 197 | `'_'` |
| 198 | `'block'` |
| 199 | `'('` |
| 200 | `'tp'` |
| 201 | `','` |
| 202 | `'RC'` |
| 203 | `'VD'` |
| 204 | `'BD'` |
| 205 | `'I'` |
| 206 | `'_'` |
| 207 | `'MODE'` |
| 208 | `','` |
| 209 | `'RC'` |
| 210 | `'VD'` |
| 211 | `'BD'` |
| 212 | `'I'` |
| 213 | `'_'` |
| 214 | `'MODE'` |
| 215 | `'_'` |
| 216 | `'EN'` |
| 217 | `'ABLE'` |
| 218 | `','` |
| 219 | `'silent'` |
| 220 | `');'` |
| 221 | `'\n'` |
| 222 | `'\t'` |
| 223 | `'err'` |
| 224 | `'|'` |
| 225 | `'='` |
| 226 | `'t'` |
| 227 | `'g'` |
| 228 | `'3'` |
| 229 | `'_'` |
| 230 | `'stop'` |
| 231 | `'_'` |
| 232 | `'block'` |
| 233 | `'('` |
| 234 | `'tp'` |
| 235 | `','` |
| 236 | `'RC'` |
| 237 | `'VD'` |
| 238 | `'CC'` |
| 239 | `'_'` |
| 240 | `'MODE'` |
| 241 | `','` |
| 242 | `'RC'` |
| 243 | `'VD'` |
| 244 | `'CC'` |
| 245 | `'_'` |
| 246 | `'MODE'` |
| 247 | `'_'` |
| 248 | `'EN'` |
| 249 | `'ABLE'` |
| 250 | `','` |
| 251 | `'silent'` |
| 252 | `');'` |
| 253 | `'\n'` |
| 254 | `'\t'` |
| 255 | `'err'` |
| 256 | `'|'` |
| 257 | `'='` |
| 258 | `'t'` |
| 259 | `'g'` |
| 260 | `'3'` |
| 261 | `'_'` |
| 262 | `'stop'` |
| 263 | `'_'` |
| 264 | `'block'` |
| 265 | `'('` |
| 266 | `'tp'` |
| 267 | `','` |
| 268 | `'RC'` |
| 269 | `'V'` |
| 270 | `'CC'` |
| 271 | `'_'` |
| 272 | `'MODE'` |
| 273 | `','` |
| 274 | `'RC'` |
| 275 | `'V'` |
| 276 | `'CC'` |
| 277 | `'_'` |
| 278 | `'MODE'` |
| 279 | `'_'` |
| 280 | `'EN'` |
| 281 | `'ABLE'` |
| 282 | `','` |
| 283 | `'silent'` |
| 284 | `');'` |
| 285 | `'\n\n'` |
| 286 | `'\t'` |
| 287 | `'err'` |
| 288 | `'|'` |
| 289 | `'='` |
| 290 | `'t'` |
| 291 | `'g'` |
| 292 | `'3'` |
| 293 | `'_'` |
| 294 | `'stop'` |
| 295 | `'_'` |
| 296 | `'block'` |
| 297 | `'('` |
| 298 | `'tp'` |
| 299 | `','` |
| 300 | `'S'` |
| 301 | `'ND'` |
| 302 | `'B'` |
| 303 | `'DS'` |
| 304 | `'_'` |
| 305 | `'MODE'` |
| 306 | `','` |
| 307 | `'S'` |
| 308 | `'ND'` |
| 309 | `'B'` |
| 310 | `'DS'` |
| 311 | `'_'` |
| 312 | `'MODE'` |
| 313 | `'_'` |
| 314 | `'EN'` |
| 315 | `'ABLE'` |
| 316 | `','` |
| 317 | `'silent'` |
| 318 | `');'` |
| 319 | `'\n'` |
| 320 | `'\t'` |
| 321 | `'err'` |
| 322 | `'|'` |
| 323 | `'='` |
| 324 | `'t'` |
| 325 | `'g'` |
| 326 | `'3'` |
| 327 | `'_'` |
| 328 | `'stop'` |
| 329 | `'_'` |
| 330 | `'block'` |
| 331 | `'('` |
| 332 | `'tp'` |
| 333 | `','` |
| 334 | `'S'` |
| 335 | `'ND'` |
| 336 | `'BD'` |
| 337 | `'I'` |
| 338 | `'_'` |
| 339 | `'MODE'` |
| 340 | `','` |
| 341 | `'S'` |
| 342 | `'ND'` |
| 343 | `'BD'` |
| 344 | `'I'` |
| 345 | `'_'` |
| 346 | `'MODE'` |
| 347 | `'_'` |
| 348 | `'EN'` |
| 349 | `'ABLE'` |
| 350 | `','` |
| 351 | `'silent'` |
| 352 | `');'` |
| 353 | `'\n'` |
| 354 | `'\t'` |
| 355 | `'err'` |
| 356 | `'|'` |
| 357 | `'='` |
| 358 | `'t'` |
| 359 | `'g'` |
| 360 | `'3'` |
| 361 | `'_'` |
| 362 | `'stop'` |
| 363 | `'_'` |
| 364 | `'block'` |
| 365 | `'('` |
| 366 | `'tp'` |
| 367 | `','` |
| 368 | `'S'` |
| 369 | `'ND'` |
| 370 | `'DATA'` |
| 371 | `'I'` |
| 372 | `'_'` |
| 373 | `'MODE'` |
| 374 | `','` |
| 375 | `'S'` |
| 376 | `'ND'` |
| 377 | `'DATA'` |
| 378 | `'I'` |
| 379 | `'_'` |
| 380 | `'MODE'` |
| 381 | `'_'` |
| 382 | `'EN'` |
| 383 | `'ABLE'` |
| 384 | `','` |
| 385 | `'silent'` |
| 386 | `');'` |
| 387 | `'\n'` |
| 388 | `'\t'` |
| 389 | `'err'` |
| 390 | `'|'` |
| 391 | `'='` |
| 392 | `'t'` |
| 393 | `'g'` |
| 394 | `'3'` |
| 395 | `'_'` |
| 396 | `'stop'` |
| 397 | `'_'` |
| 398 | `'block'` |
| 399 | `'('` |
| 400 | `'tp'` |
| 401 | `','` |
| 402 | `'R'` |
| 403 | `'DM'` |
| 404 | `'AC'` |
| 405 | `'_'` |
| 406 | `'MODE'` |
| 407 | `','` |
| 408 | `'R'` |
| 409 | `'DM'` |
| 410 | `'AC'` |
| 411 | `'_'` |
| 412 | `'MODE'` |
| 413 | `'_'` |
| 414 | `'EN'` |
| 415 | `'ABLE'` |
| 416 | `','` |
| 417 | `'silent'` |
| 418 | `');'` |
| 419 | `'\n'` |
| 420 | `'\t'` |
| 421 | `'err'` |
| 422 | `'|'` |
| 423 | `'='` |
| 424 | `'t'` |
| 425 | `'g'` |
| 426 | `'3'` |
| 427 | `'_'` |
| 428 | `'stop'` |
| 429 | `'_'` |
| 430 | `'block'` |
| 431 | `'('` |
| 432 | `'tp'` |
| 433 | `','` |
| 434 | `'S'` |
| 435 | `'ND'` |
| 436 | `'D'` |
| 437 | `'AT'` |
| 438 | `'AC'` |
| 439 | `'_'` |
| 440 | `'MODE'` |
| 441 | `','` |
| 442 | `'S'` |
| 443 | `'ND'` |
| 444 | `'D'` |
| 445 | `'AT'` |
| 446 | `'AC'` |
| 447 | `'_'` |
| 448 | `'MODE'` |
| 449 | `'_'` |
| 450 | `'EN'` |
| 451 | `'ABLE'` |
| 452 | `','` |
| 453 | `'silent'` |
| 454 | `');'` |
| 455 | `'\n'` |
| 456 | `'\t'` |
| 457 | `'err'` |
| 458 | `'|'` |
| 459 | `'='` |
| 460 | `'t'` |
| 461 | `'g'` |
| 462 | `'3'` |
| 463 | `'_'` |
| 464 | `'stop'` |
| 465 | `'_'` |
| 466 | `'block'` |
| 467 | `'('` |
| 468 | `'tp'` |
| 469 | `','` |
| 470 | `'DM'` |
| 471 | `'AC'` |
| 472 | `'_'` |
| 473 | `'MODE'` |
| 474 | `','` |
| 475 | `'DM'` |
| 476 | `'AC'` |
| 477 | `'_'` |
| 478 | `'MODE'` |
| 479 | `'_'` |
| 480 | `'EN'` |
| 481 | `'ABLE'` |
| 482 | `','` |
| 483 | `'silent'` |
| 484 | `');'` |
| 485 | `'\n'` |
| 486 | `'\t'` |
| 487 | `'err'` |
| 488 | `'|'` |
| 489 | `'='` |
| 490 | `'t'` |
| 491 | `'g'` |
| 492 | `'3'` |
| 493 | `'_'` |
| 494 | `'stop'` |
| 495 | `'_'` |
| 496 | `'block'` |
| 497 | `'('` |
| 498 | `'tp'` |
| 499 | `','` |
| 500 | `'S'` |
| 501 | `'ND'` |
| 502 | `'B'` |
| 503 | `'DC'` |
| 504 | `'_'` |
| 505 | `'MODE'` |
| 506 | `','` |
| 507 | `'S'` |
| 508 | `'ND'` |
| 509 | `'B'` |
| 510 | `'DC'` |
