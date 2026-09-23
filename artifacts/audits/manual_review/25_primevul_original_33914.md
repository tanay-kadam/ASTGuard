# Review 25: `primevul:original:33914` (cpp)

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
   1 | static void tg3_init_bufmgr_config(struct tg3 *tp)
   2 | {
   3 | 	if (tg3_flag(tp, 57765_PLUS)) {
   4 | 		tp->bufmgr_config.mbuf_read_dma_low_water =
   5 | 			DEFAULT_MB_RDMA_LOW_WATER_5705;
   6 | 		tp->bufmgr_config.mbuf_mac_rx_low_water =
   7 | 			DEFAULT_MB_MACRX_LOW_WATER_57765;
   8 | 		tp->bufmgr_config.mbuf_high_water =
   9 | 			DEFAULT_MB_HIGH_WATER_57765;
  10 | 
  11 | 		tp->bufmgr_config.mbuf_read_dma_low_water_jumbo =
  12 | 			DEFAULT_MB_RDMA_LOW_WATER_5705;
  13 | 		tp->bufmgr_config.mbuf_mac_rx_low_water_jumbo =
  14 | 			DEFAULT_MB_MACRX_LOW_WATER_JUMBO_57765;
  15 | 		tp->bufmgr_config.mbuf_high_water_jumbo =
  16 | 			DEFAULT_MB_HIGH_WATER_JUMBO_57765;
  17 | 	} else if (tg3_flag(tp, 5705_PLUS)) {
  18 | 		tp->bufmgr_config.mbuf_read_dma_low_water =
  19 | 			DEFAULT_MB_RDMA_LOW_WATER_5705;
  20 | 		tp->bufmgr_config.mbuf_mac_rx_low_water =
  21 | 			DEFAULT_MB_MACRX_LOW_WATER_5705;
  22 | 		tp->bufmgr_config.mbuf_high_water =
  23 | 			DEFAULT_MB_HIGH_WATER_5705;
  24 | 		if (tg3_asic_rev(tp) == ASIC_REV_5906) {
  25 | 			tp->bufmgr_config.mbuf_mac_rx_low_water =
  26 | 				DEFAULT_MB_MACRX_LOW_WATER_5906;
  27 | 			tp->bufmgr_config.mbuf_high_water =
  28 | 				DEFAULT_MB_HIGH_WATER_5906;
  29 | 		}
  30 | 
  31 | 		tp->bufmgr_config.mbuf_read_dma_low_water_jumbo =
  32 | 			DEFAULT_MB_RDMA_LOW_WATER_JUMBO_5780;
  33 | 		tp->bufmgr_config.mbuf_mac_rx_low_water_jumbo =
  34 | 			DEFAULT_MB_MACRX_LOW_WATER_JUMBO_5780;
  35 | 		tp->bufmgr_config.mbuf_high_water_jumbo =
  36 | 			DEFAULT_MB_HIGH_WATER_JUMBO_5780;
  37 | 	} else {
  38 | 		tp->bufmgr_config.mbuf_read_dma_low_water =
  39 | 			DEFAULT_MB_RDMA_LOW_WATER;
  40 | 		tp->bufmgr_config.mbuf_mac_rx_low_water =
  41 | 			DEFAULT_MB_MACRX_LOW_WATER;
  42 | 		tp->bufmgr_config.mbuf_high_water =
  43 | 			DEFAULT_MB_HIGH_WATER;
  44 | 
  45 | 		tp->bufmgr_config.mbuf_read_dma_low_water_jumbo =
  46 | 			DEFAULT_MB_RDMA_LOW_WATER_JUMBO;
  47 | 		tp->bufmgr_config.mbuf_mac_rx_low_water_jumbo =
  48 | 			DEFAULT_MB_MACRX_LOW_WATER_JUMBO;
  49 | 		tp->bufmgr_config.mbuf_high_water_jumbo =
  50 | 			DEFAULT_MB_HIGH_WATER_JUMBO;
  51 | 	}
  52 | 
  53 | 	tp->bufmgr_config.dma_low_water = DEFAULT_DMA_LOW_WATER;
  54 | 	tp->bufmgr_config.dma_high_water = DEFAULT_DMA_HIGH_WATER;
  55 | }
  56 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `void` | 1:8 |
| 2 | `tg3_init_bufmgr_config` | 1:13 |
| 4 | `struct` | 1:36 |
| 5 | `tg3` | 1:43 |
| 7 | `tp` | 1:48 |
| 10 | `if` | 3:2 |
| 12 | `tg3_flag` | 3:6 |
| 14 | `tp` | 3:15 |
| 17 | `_PLUS` | 3:24 |
| 21 | `tp` | 4:3 |
| 23 | `bufmgr_config` | 4:7 |
| 25 | `mbuf_read_dma_low_water` | 4:21 |
| 27 | `DEFAULT_MB_RDMA_LOW_WATER_5705` | 5:4 |
| 29 | `tp` | 6:3 |
| 31 | `bufmgr_config` | 6:7 |
| 33 | `mbuf_mac_rx_low_water` | 6:21 |
| 35 | `DEFAULT_MB_MACRX_LOW_WATER_57765` | 7:4 |
| 37 | `tp` | 8:3 |
| 39 | `bufmgr_config` | 8:7 |
| 41 | `mbuf_high_water` | 8:21 |
| 43 | `DEFAULT_MB_HIGH_WATER_57765` | 9:4 |
| 45 | `tp` | 11:3 |
| 47 | `bufmgr_config` | 11:7 |
| 49 | `mbuf_read_dma_low_water_jumbo` | 11:21 |
| 51 | `DEFAULT_MB_RDMA_LOW_WATER_5705` | 12:4 |
| 53 | `tp` | 13:3 |
| 55 | `bufmgr_config` | 13:7 |
| 57 | `mbuf_mac_rx_low_water_jumbo` | 13:21 |
| 59 | `DEFAULT_MB_MACRX_LOW_WATER_JUMBO_57765` | 14:4 |
| 61 | `tp` | 15:3 |
| 63 | `bufmgr_config` | 15:7 |
| 65 | `mbuf_high_water_jumbo` | 15:21 |
| 67 | `DEFAULT_MB_HIGH_WATER_JUMBO_57765` | 16:4 |
| 70 | `else` | 17:4 |
| 71 | `if` | 17:9 |
| 73 | `tg3_flag` | 17:13 |
| 75 | `tp` | 17:22 |
| 78 | `_PLUS` | 17:30 |
| 82 | `tp` | 18:3 |
| 84 | `bufmgr_config` | 18:7 |
| 86 | `mbuf_read_dma_low_water` | 18:21 |
| 88 | `DEFAULT_MB_RDMA_LOW_WATER_5705` | 19:4 |
| 90 | `tp` | 20:3 |
| 92 | `bufmgr_config` | 20:7 |
| 94 | `mbuf_mac_rx_low_water` | 20:21 |
| 96 | `DEFAULT_MB_MACRX_LOW_WATER_5705` | 21:4 |
| 98 | `tp` | 22:3 |
| 100 | `bufmgr_config` | 22:7 |
| 102 | `mbuf_high_water` | 22:21 |
| 104 | `DEFAULT_MB_HIGH_WATER_5705` | 23:4 |
| 106 | `if` | 24:3 |
| 108 | `tg3_asic_rev` | 24:7 |
| 110 | `tp` | 24:20 |
| 113 | `ASIC_REV_5906` | 24:27 |
| 116 | `tp` | 25:4 |
| 118 | `bufmgr_config` | 25:8 |
| 120 | `mbuf_mac_rx_low_water` | 25:22 |
| 122 | `DEFAULT_MB_MACRX_LOW_WATER_5906` | 26:5 |
| 124 | `tp` | 27:4 |
| 126 | `bufmgr_config` | 27:8 |
| 128 | `mbuf_high_water` | 27:22 |
| 130 | `DEFAULT_MB_HIGH_WATER_5906` | 28:5 |
| 133 | `tp` | 31:3 |
| 135 | `bufmgr_config` | 31:7 |
| 137 | `mbuf_read_dma_low_water_jumbo` | 31:21 |
| 139 | `DEFAULT_MB_RDMA_LOW_WATER_JUMBO_5780` | 32:4 |
| 141 | `tp` | 33:3 |
| 143 | `bufmgr_config` | 33:7 |
| 145 | `mbuf_mac_rx_low_water_jumbo` | 33:21 |
| 147 | `DEFAULT_MB_MACRX_LOW_WATER_JUMBO_5780` | 34:4 |
| 149 | `tp` | 35:3 |
| 151 | `bufmgr_config` | 35:7 |
| 153 | `mbuf_high_water_jumbo` | 35:21 |
| 155 | `DEFAULT_MB_HIGH_WATER_JUMBO_5780` | 36:4 |
| 158 | `else` | 37:4 |
| 160 | `tp` | 38:3 |
| 162 | `bufmgr_config` | 38:7 |
| 164 | `mbuf_read_dma_low_water` | 38:21 |
| 166 | `DEFAULT_MB_RDMA_LOW_WATER` | 39:4 |
| 168 | `tp` | 40:3 |
| 170 | `bufmgr_config` | 40:7 |
| 172 | `mbuf_mac_rx_low_water` | 40:21 |
| 174 | `DEFAULT_MB_MACRX_LOW_WATER` | 41:4 |
| 176 | `tp` | 42:3 |
| 178 | `bufmgr_config` | 42:7 |
| 180 | `mbuf_high_water` | 42:21 |
| 182 | `DEFAULT_MB_HIGH_WATER` | 43:4 |
| 184 | `tp` | 45:3 |
| 186 | `bufmgr_config` | 45:7 |
| 188 | `mbuf_read_dma_low_water_jumbo` | 45:21 |
| 190 | `DEFAULT_MB_RDMA_LOW_WATER_JUMBO` | 46:4 |
| 192 | `tp` | 47:3 |
| 194 | `bufmgr_config` | 47:7 |
| 196 | `mbuf_mac_rx_low_water_jumbo` | 47:21 |
| 198 | `DEFAULT_MB_MACRX_LOW_WATER_JUMBO` | 48:4 |
| 200 | `tp` | 49:3 |
| 202 | `bufmgr_config` | 49:7 |
| 204 | `mbuf_high_water_jumbo` | 49:21 |
| 206 | `DEFAULT_MB_HIGH_WATER_JUMBO` | 50:4 |
| 209 | `tp` | 53:2 |
| 211 | `bufmgr_config` | 53:6 |
| 213 | `dma_low_water` | 53:20 |
| 215 | `DEFAULT_DMA_LOW_WATER` | 53:36 |
| 217 | `tp` | 54:2 |
| 219 | `bufmgr_config` | 54:6 |
| 221 | `dma_high_water` | 54:20 |
| 223 | `DEFAULT_DMA_HIGH_WATER` | 54:37 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'void'` |
| 3 | `'t'` |
| 4 | `'g'` |
| 5 | `'3'` |
| 6 | `'_'` |
| 7 | `'init'` |
| 8 | `'_'` |
| 9 | `'buf'` |
| 10 | `'m'` |
| 11 | `'gr'` |
| 12 | `'_'` |
| 13 | `'config'` |
| 14 | `'('` |
| 15 | `'struct'` |
| 16 | `'t'` |
| 17 | `'g'` |
| 18 | `'3'` |
| 19 | `'*'` |
| 20 | `'tp'` |
| 21 | `')'` |
| 22 | `'\n'` |
| 23 | `'{'` |
| 24 | `'\n'` |
| 25 | `'\t'` |
| 26 | `'if'` |
| 27 | `'('` |
| 28 | `'tg'` |
| 29 | `'3'` |
| 30 | `'_'` |
| 31 | `'flag'` |
| 32 | `'('` |
| 33 | `'tp'` |
| 34 | `','` |
| 35 | `'5'` |
| 36 | `'77'` |
| 37 | `'65'` |
| 38 | `'_'` |
| 39 | `'PL'` |
| 40 | `'US'` |
| 41 | `'))'` |
| 42 | `'{'` |
| 43 | `'\n'` |
| 44 | `'\t'` |
| 45 | `'\t'` |
| 46 | `'tp'` |
| 47 | `'->'` |
| 48 | `'buf'` |
| 49 | `'m'` |
| 50 | `'gr'` |
| 51 | `'_'` |
| 52 | `'config'` |
| 53 | `'.'` |
| 54 | `'mb'` |
| 55 | `'uf'` |
| 56 | `'_'` |
| 57 | `'read'` |
| 58 | `'_'` |
| 59 | `'d'` |
| 60 | `'ma'` |
| 61 | `'_'` |
| 62 | `'low'` |
| 63 | `'_'` |
| 64 | `'water'` |
| 65 | `'='` |
| 66 | `'\n'` |
| 67 | `'\t'` |
| 68 | `'\t'` |
| 69 | `'\t'` |
| 70 | `'DE'` |
| 71 | `'FAULT'` |
| 72 | `'_'` |
| 73 | `'MB'` |
| 74 | `'_'` |
| 75 | `'RD'` |
| 76 | `'MA'` |
| 77 | `'_'` |
| 78 | `'L'` |
| 79 | `'OW'` |
| 80 | `'_'` |
| 81 | `'W'` |
| 82 | `'ATER'` |
| 83 | `'_'` |
| 84 | `'5'` |
| 85 | `'705'` |
| 86 | `';'` |
| 87 | `'\n'` |
| 88 | `'\t'` |
| 89 | `'\t'` |
| 90 | `'tp'` |
| 91 | `'->'` |
| 92 | `'buf'` |
| 93 | `'m'` |
| 94 | `'gr'` |
| 95 | `'_'` |
| 96 | `'config'` |
| 97 | `'.'` |
| 98 | `'mb'` |
| 99 | `'uf'` |
| 100 | `'_'` |
| 101 | `'mac'` |
| 102 | `'_'` |
| 103 | `'rx'` |
| 104 | `'_'` |
| 105 | `'low'` |
| 106 | `'_'` |
| 107 | `'water'` |
| 108 | `'='` |
| 109 | `'\n'` |
| 110 | `'\t'` |
| 111 | `'\t'` |
| 112 | `'\t'` |
| 113 | `'DE'` |
| 114 | `'FAULT'` |
| 115 | `'_'` |
| 116 | `'MB'` |
| 117 | `'_'` |
| 118 | `'MAC'` |
| 119 | `'R'` |
| 120 | `'X'` |
| 121 | `'_'` |
| 122 | `'L'` |
| 123 | `'OW'` |
| 124 | `'_'` |
| 125 | `'W'` |
| 126 | `'ATER'` |
| 127 | `'_'` |
| 128 | `'577'` |
| 129 | `'65'` |
| 130 | `';'` |
| 131 | `'\n'` |
| 132 | `'\t'` |
| 133 | `'\t'` |
| 134 | `'tp'` |
| 135 | `'->'` |
| 136 | `'buf'` |
| 137 | `'m'` |
| 138 | `'gr'` |
| 139 | `'_'` |
| 140 | `'config'` |
| 141 | `'.'` |
| 142 | `'mb'` |
| 143 | `'uf'` |
| 144 | `'_'` |
| 145 | `'high'` |
| 146 | `'_'` |
| 147 | `'water'` |
| 148 | `'='` |
| 149 | `'\n'` |
| 150 | `'\t'` |
| 151 | `'\t'` |
| 152 | `'\t'` |
| 153 | `'DE'` |
| 154 | `'FAULT'` |
| 155 | `'_'` |
| 156 | `'MB'` |
| 157 | `'_'` |
| 158 | `'H'` |
| 159 | `'IGH'` |
| 160 | `'_'` |
| 161 | `'W'` |
| 162 | `'ATER'` |
| 163 | `'_'` |
| 164 | `'577'` |
| 165 | `'65'` |
| 166 | `';'` |
| 167 | `'\n\n'` |
| 168 | `'\t'` |
| 169 | `'\t'` |
| 170 | `'tp'` |
| 171 | `'->'` |
| 172 | `'buf'` |
| 173 | `'m'` |
| 174 | `'gr'` |
| 175 | `'_'` |
| 176 | `'config'` |
| 177 | `'.'` |
| 178 | `'mb'` |
| 179 | `'uf'` |
| 180 | `'_'` |
| 181 | `'read'` |
| 182 | `'_'` |
| 183 | `'d'` |
| 184 | `'ma'` |
| 185 | `'_'` |
| 186 | `'low'` |
| 187 | `'_'` |
| 188 | `'water'` |
| 189 | `'_'` |
| 190 | `'j'` |
| 191 | `'umbo'` |
| 192 | `'='` |
| 193 | `'\n'` |
| 194 | `'\t'` |
| 195 | `'\t'` |
| 196 | `'\t'` |
| 197 | `'DE'` |
| 198 | `'FAULT'` |
| 199 | `'_'` |
| 200 | `'MB'` |
| 201 | `'_'` |
| 202 | `'RD'` |
| 203 | `'MA'` |
| 204 | `'_'` |
| 205 | `'L'` |
| 206 | `'OW'` |
| 207 | `'_'` |
| 208 | `'W'` |
| 209 | `'ATER'` |
| 210 | `'_'` |
| 211 | `'5'` |
| 212 | `'705'` |
| 213 | `';'` |
| 214 | `'\n'` |
| 215 | `'\t'` |
| 216 | `'\t'` |
| 217 | `'tp'` |
| 218 | `'->'` |
| 219 | `'buf'` |
| 220 | `'m'` |
| 221 | `'gr'` |
| 222 | `'_'` |
| 223 | `'config'` |
| 224 | `'.'` |
| 225 | `'mb'` |
| 226 | `'uf'` |
| 227 | `'_'` |
| 228 | `'mac'` |
| 229 | `'_'` |
| 230 | `'rx'` |
| 231 | `'_'` |
| 232 | `'low'` |
| 233 | `'_'` |
| 234 | `'water'` |
| 235 | `'_'` |
| 236 | `'j'` |
| 237 | `'umbo'` |
| 238 | `'='` |
| 239 | `'\n'` |
| 240 | `'\t'` |
| 241 | `'\t'` |
| 242 | `'\t'` |
| 243 | `'DE'` |
| 244 | `'FAULT'` |
| 245 | `'_'` |
| 246 | `'MB'` |
| 247 | `'_'` |
| 248 | `'MAC'` |
| 249 | `'R'` |
| 250 | `'X'` |
| 251 | `'_'` |
| 252 | `'L'` |
| 253 | `'OW'` |
| 254 | `'_'` |
| 255 | `'W'` |
| 256 | `'ATER'` |
| 257 | `'_'` |
| 258 | `'J'` |
| 259 | `'UM'` |
| 260 | `'BO'` |
| 261 | `'_'` |
| 262 | `'577'` |
| 263 | `'65'` |
| 264 | `';'` |
| 265 | `'\n'` |
| 266 | `'\t'` |
| 267 | `'\t'` |
| 268 | `'tp'` |
| 269 | `'->'` |
| 270 | `'buf'` |
| 271 | `'m'` |
| 272 | `'gr'` |
| 273 | `'_'` |
| 274 | `'config'` |
| 275 | `'.'` |
| 276 | `'mb'` |
| 277 | `'uf'` |
| 278 | `'_'` |
| 279 | `'high'` |
| 280 | `'_'` |
| 281 | `'water'` |
| 282 | `'_'` |
| 283 | `'j'` |
| 284 | `'umbo'` |
| 285 | `'='` |
| 286 | `'\n'` |
| 287 | `'\t'` |
| 288 | `'\t'` |
| 289 | `'\t'` |
| 290 | `'DE'` |
| 291 | `'FAULT'` |
| 292 | `'_'` |
| 293 | `'MB'` |
| 294 | `'_'` |
| 295 | `'H'` |
| 296 | `'IGH'` |
| 297 | `'_'` |
| 298 | `'W'` |
| 299 | `'ATER'` |
| 300 | `'_'` |
| 301 | `'J'` |
| 302 | `'UM'` |
| 303 | `'BO'` |
| 304 | `'_'` |
| 305 | `'577'` |
| 306 | `'65'` |
| 307 | `';'` |
| 308 | `'\n'` |
| 309 | `'\t'` |
| 310 | `'}'` |
| 311 | `'else'` |
| 312 | `'if'` |
| 313 | `'('` |
| 314 | `'tg'` |
| 315 | `'3'` |
| 316 | `'_'` |
| 317 | `'flag'` |
| 318 | `'('` |
| 319 | `'tp'` |
| 320 | `','` |
| 321 | `'5'` |
| 322 | `'705'` |
| 323 | `'_'` |
| 324 | `'PL'` |
| 325 | `'US'` |
| 326 | `'))'` |
| 327 | `'{'` |
| 328 | `'\n'` |
| 329 | `'\t'` |
| 330 | `'\t'` |
| 331 | `'tp'` |
| 332 | `'->'` |
| 333 | `'buf'` |
| 334 | `'m'` |
| 335 | `'gr'` |
| 336 | `'_'` |
| 337 | `'config'` |
| 338 | `'.'` |
| 339 | `'mb'` |
| 340 | `'uf'` |
| 341 | `'_'` |
| 342 | `'read'` |
| 343 | `'_'` |
| 344 | `'d'` |
| 345 | `'ma'` |
| 346 | `'_'` |
| 347 | `'low'` |
| 348 | `'_'` |
| 349 | `'water'` |
| 350 | `'='` |
| 351 | `'\n'` |
| 352 | `'\t'` |
| 353 | `'\t'` |
| 354 | `'\t'` |
| 355 | `'DE'` |
| 356 | `'FAULT'` |
| 357 | `'_'` |
| 358 | `'MB'` |
| 359 | `'_'` |
| 360 | `'RD'` |
| 361 | `'MA'` |
| 362 | `'_'` |
| 363 | `'L'` |
| 364 | `'OW'` |
| 365 | `'_'` |
| 366 | `'W'` |
| 367 | `'ATER'` |
| 368 | `'_'` |
| 369 | `'5'` |
| 370 | `'705'` |
| 371 | `';'` |
| 372 | `'\n'` |
| 373 | `'\t'` |
| 374 | `'\t'` |
| 375 | `'tp'` |
| 376 | `'->'` |
| 377 | `'buf'` |
| 378 | `'m'` |
| 379 | `'gr'` |
| 380 | `'_'` |
| 381 | `'config'` |
| 382 | `'.'` |
| 383 | `'mb'` |
| 384 | `'uf'` |
| 385 | `'_'` |
| 386 | `'mac'` |
| 387 | `'_'` |
| 388 | `'rx'` |
| 389 | `'_'` |
| 390 | `'low'` |
| 391 | `'_'` |
| 392 | `'water'` |
| 393 | `'='` |
| 394 | `'\n'` |
| 395 | `'\t'` |
| 396 | `'\t'` |
| 397 | `'\t'` |
| 398 | `'DE'` |
| 399 | `'FAULT'` |
| 400 | `'_'` |
| 401 | `'MB'` |
| 402 | `'_'` |
| 403 | `'MAC'` |
| 404 | `'R'` |
| 405 | `'X'` |
| 406 | `'_'` |
| 407 | `'L'` |
| 408 | `'OW'` |
| 409 | `'_'` |
| 410 | `'W'` |
| 411 | `'ATER'` |
| 412 | `'_'` |
| 413 | `'5'` |
| 414 | `'705'` |
| 415 | `';'` |
| 416 | `'\n'` |
| 417 | `'\t'` |
| 418 | `'\t'` |
| 419 | `'tp'` |
| 420 | `'->'` |
| 421 | `'buf'` |
| 422 | `'m'` |
| 423 | `'gr'` |
| 424 | `'_'` |
| 425 | `'config'` |
| 426 | `'.'` |
| 427 | `'mb'` |
| 428 | `'uf'` |
| 429 | `'_'` |
| 430 | `'high'` |
| 431 | `'_'` |
| 432 | `'water'` |
| 433 | `'='` |
| 434 | `'\n'` |
| 435 | `'\t'` |
| 436 | `'\t'` |
| 437 | `'\t'` |
| 438 | `'DE'` |
| 439 | `'FAULT'` |
| 440 | `'_'` |
| 441 | `'MB'` |
| 442 | `'_'` |
| 443 | `'H'` |
| 444 | `'IGH'` |
| 445 | `'_'` |
| 446 | `'W'` |
| 447 | `'ATER'` |
| 448 | `'_'` |
| 449 | `'5'` |
| 450 | `'705'` |
| 451 | `';'` |
| 452 | `'\n'` |
| 453 | `'\t'` |
| 454 | `'\t'` |
| 455 | `'if'` |
| 456 | `'('` |
| 457 | `'tg'` |
| 458 | `'3'` |
| 459 | `'_'` |
| 460 | `'as'` |
| 461 | `'ic'` |
| 462 | `'_'` |
| 463 | `'rev'` |
| 464 | `'('` |
| 465 | `'tp'` |
| 466 | `')'` |
| 467 | `'=='` |
| 468 | `'ASIC'` |
| 469 | `'_'` |
| 470 | `'RE'` |
| 471 | `'V'` |
| 472 | `'_'` |
| 473 | `'59'` |
| 474 | `'06'` |
| 475 | `')'` |
| 476 | `'{'` |
| 477 | `'\n'` |
| 478 | `'\t'` |
| 479 | `'\t'` |
| 480 | `'\t'` |
| 481 | `'tp'` |
| 482 | `'->'` |
| 483 | `'buf'` |
| 484 | `'m'` |
| 485 | `'gr'` |
| 486 | `'_'` |
| 487 | `'config'` |
| 488 | `'.'` |
| 489 | `'mb'` |
| 490 | `'uf'` |
| 491 | `'_'` |
| 492 | `'mac'` |
| 493 | `'_'` |
| 494 | `'rx'` |
| 495 | `'_'` |
| 496 | `'low'` |
| 497 | `'_'` |
| 498 | `'water'` |
| 499 | `'='` |
| 500 | `'\n'` |
| 501 | `'\t'` |
| 502 | `'\t'` |
| 503 | `'\t'` |
| 504 | `'\t'` |
| 505 | `'DE'` |
| 506 | `'FAULT'` |
| 507 | `'_'` |
| 508 | `'MB'` |
| 509 | `'_'` |
| 510 | `'MAC'` |
