# Review 15: `primevul:original:130121` (cpp)

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
   1 | bool ShouldPropagateUserActivation(const url::Origin& previous_origin,
   2 |                                    const url::Origin& new_origin) {
   3 |   if ((previous_origin.scheme() != "http" &&
   4 |        previous_origin.scheme() != "https") ||
   5 |       (new_origin.scheme() != "http" && new_origin.scheme() != "https")) {
   6 |     return false;
   7 |   }
   8 | 
   9 |   if (previous_origin.host() == new_origin.host())
  10 |     return true;
  11 | 
  12 |   std::string previous_domain =
  13 |       net::registry_controlled_domains::GetDomainAndRegistry(
  14 |           previous_origin.host(),
  15 |           net::registry_controlled_domains::INCLUDE_PRIVATE_REGISTRIES);
  16 |   std::string new_domain =
  17 |       net::registry_controlled_domains::GetDomainAndRegistry(
  18 |           new_origin.host(),
  19 |           net::registry_controlled_domains::INCLUDE_PRIVATE_REGISTRIES);
  20 |   return !previous_domain.empty() && previous_domain == new_domain;
  21 | }
  22 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `bool` | 1:1 |
| 1 | `ShouldPropagateUserActivation` | 1:6 |
| 3 | `const` | 1:36 |
| 4 | `url` | 1:42 |
| 6 | `Origin` | 1:47 |
| 8 | `previous_origin` | 1:55 |
| 10 | `const` | 2:36 |
| 11 | `url` | 2:42 |
| 13 | `Origin` | 2:47 |
| 15 | `new_origin` | 2:55 |
| 18 | `if` | 3:3 |
| 21 | `previous_origin` | 3:8 |
| 23 | `scheme` | 3:24 |
| 29 | `previous_origin` | 4:8 |
| 31 | `scheme` | 4:24 |
| 39 | `new_origin` | 5:8 |
| 41 | `scheme` | 5:19 |
| 47 | `new_origin` | 5:41 |
| 49 | `scheme` | 5:52 |
| 57 | `return` | 6:5 |
| 58 | `false` | 6:12 |
| 61 | `if` | 9:3 |
| 63 | `previous_origin` | 9:7 |
| 65 | `host` | 9:23 |
| 69 | `new_origin` | 9:33 |
| 71 | `host` | 9:44 |
| 75 | `return` | 10:5 |
| 76 | `true` | 10:12 |
| 78 | `std` | 12:3 |
| 80 | `string` | 12:8 |
| 81 | `previous_domain` | 12:15 |
| 83 | `net` | 13:7 |
| 85 | `registry_controlled_domains` | 13:12 |
| 87 | `GetDomainAndRegistry` | 13:41 |
| 89 | `previous_origin` | 14:11 |
| 91 | `host` | 14:27 |
| 95 | `net` | 15:11 |
| 97 | `registry_controlled_domains` | 15:16 |
| 99 | `INCLUDE_PRIVATE_REGISTRIES` | 15:45 |
| 102 | `std` | 16:3 |
| 104 | `string` | 16:8 |
| 105 | `new_domain` | 16:15 |
| 107 | `net` | 17:7 |
| 109 | `registry_controlled_domains` | 17:12 |
| 111 | `GetDomainAndRegistry` | 17:41 |
| 113 | `new_origin` | 18:11 |
| 115 | `host` | 18:22 |
| 119 | `net` | 19:11 |
| 121 | `registry_controlled_domains` | 19:16 |
| 123 | `INCLUDE_PRIVATE_REGISTRIES` | 19:45 |
| 126 | `return` | 20:3 |
| 128 | `previous_domain` | 20:11 |
| 130 | `empty` | 20:27 |
| 134 | `previous_domain` | 20:38 |
| 136 | `new_domain` | 20:57 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'bool'` |
| 2 | `'Should'` |
| 3 | `'Prop'` |
| 4 | `'agate'` |
| 5 | `'User'` |
| 6 | `'Activ'` |
| 7 | `'ation'` |
| 8 | `'('` |
| 9 | `'const'` |
| 10 | `'url'` |
| 11 | `'::'` |
| 12 | `'Origin'` |
| 13 | `'&'` |
| 14 | `'previous'` |
| 15 | `'_'` |
| 16 | `'origin'` |
| 17 | `','` |
| 18 | `'\n'` |
| 53 | `'const'` |
| 54 | `'url'` |
| 55 | `'::'` |
| 56 | `'Origin'` |
| 57 | `'&'` |
| 58 | `'new'` |
| 59 | `'_'` |
| 60 | `'origin'` |
| 61 | `')'` |
| 62 | `'{'` |
| 63 | `'\n'` |
| 65 | `'if'` |
| 66 | `'(('` |
| 67 | `'pre'` |
| 68 | `'vious'` |
| 69 | `'_'` |
| 70 | `'origin'` |
| 71 | `'.'` |
| 72 | `'sche'` |
| 73 | `'me'` |
| 74 | `'()'` |
| 75 | `'!='` |
| 76 | `'"'` |
| 77 | `'http'` |
| 78 | `'"'` |
| 79 | `'&&'` |
| 80 | `'\n'` |
| 87 | `'previous'` |
| 88 | `'_'` |
| 89 | `'origin'` |
| 90 | `'.'` |
| 91 | `'sche'` |
| 92 | `'me'` |
| 93 | `'()'` |
| 94 | `'!='` |
| 95 | `'"'` |
| 96 | `'https'` |
| 97 | `'")'` |
| 98 | `'||'` |
| 99 | `'\n'` |
| 105 | `'('` |
| 106 | `'new'` |
| 107 | `'_'` |
| 108 | `'origin'` |
| 109 | `'.'` |
| 110 | `'sche'` |
| 111 | `'me'` |
| 112 | `'()'` |
| 113 | `'!='` |
| 114 | `'"'` |
| 115 | `'http'` |
| 116 | `'"'` |
| 117 | `'&&'` |
| 118 | `'new'` |
| 119 | `'_'` |
| 120 | `'origin'` |
| 121 | `'.'` |
| 122 | `'sche'` |
| 123 | `'me'` |
| 124 | `'()'` |
| 125 | `'!='` |
| 126 | `'"'` |
| 127 | `'https'` |
| 128 | `'"))'` |
| 129 | `'{'` |
| 130 | `'\n'` |
| 134 | `'return'` |
| 135 | `'false'` |
| 136 | `';'` |
| 137 | `'\n'` |
| 139 | `'}'` |
| 140 | `'\n\n'` |
| 142 | `'if'` |
| 143 | `'('` |
| 144 | `'pre'` |
| 145 | `'vious'` |
| 146 | `'_'` |
| 147 | `'origin'` |
| 148 | `'.'` |
| 149 | `'host'` |
| 150 | `'()'` |
| 151 | `'=='` |
| 152 | `'new'` |
| 153 | `'_'` |
| 154 | `'origin'` |
| 155 | `'.'` |
| 156 | `'host'` |
| 157 | `'())'` |
| 158 | `'\n'` |
| 162 | `'return'` |
| 163 | `'true'` |
| 164 | `';'` |
| 165 | `'\n\n'` |
| 167 | `'std'` |
| 168 | `'::'` |
| 169 | `'string'` |
| 170 | `'previous'` |
| 171 | `'_'` |
| 172 | `'domain'` |
| 173 | `'='` |
| 174 | `'\n'` |
| 180 | `'net'` |
| 181 | `'::'` |
| 182 | `'reg'` |
| 183 | `'istry'` |
| 184 | `'_'` |
| 185 | `'controlled'` |
| 186 | `'_'` |
| 187 | `'dom'` |
| 188 | `'ains'` |
| 189 | `'::'` |
| 190 | `'Get'` |
| 191 | `'Domain'` |
| 192 | `'And'` |
| 193 | `'Reg'` |
| 194 | `'istry'` |
| 195 | `'('` |
| 196 | `'\n'` |
| 206 | `'previous'` |
| 207 | `'_'` |
| 208 | `'origin'` |
| 209 | `'.'` |
| 210 | `'host'` |
| 211 | `'(),'` |
| 212 | `'\n'` |
| 222 | `'net'` |
| 223 | `'::'` |
| 224 | `'reg'` |
| 225 | `'istry'` |
| 226 | `'_'` |
| 227 | `'controlled'` |
| 228 | `'_'` |
| 229 | `'dom'` |
| 230 | `'ains'` |
| 231 | `'::'` |
| 232 | `'IN'` |
| 233 | `'CL'` |
| 234 | `'U'` |
| 235 | `'DE'` |
| 236 | `'_'` |
| 237 | `'PR'` |
| 238 | `'IV'` |
| 239 | `'ATE'` |
| 240 | `'_'` |
| 241 | `'REG'` |
| 242 | `'IS'` |
| 243 | `'TR'` |
| 244 | `'IES'` |
| 245 | `');'` |
| 246 | `'\n'` |
| 248 | `'std'` |
| 249 | `'::'` |
| 250 | `'string'` |
| 251 | `'new'` |
| 252 | `'_'` |
| 253 | `'domain'` |
| 254 | `'='` |
| 255 | `'\n'` |
| 261 | `'net'` |
| 262 | `'::'` |
| 263 | `'reg'` |
| 264 | `'istry'` |
| 265 | `'_'` |
| 266 | `'controlled'` |
| 267 | `'_'` |
| 268 | `'dom'` |
| 269 | `'ains'` |
| 270 | `'::'` |
| 271 | `'Get'` |
| 272 | `'Domain'` |
| 273 | `'And'` |
| 274 | `'Reg'` |
| 275 | `'istry'` |
| 276 | `'('` |
| 277 | `'\n'` |
| 287 | `'new'` |
| 288 | `'_'` |
| 289 | `'origin'` |
| 290 | `'.'` |
| 291 | `'host'` |
| 292 | `'(),'` |
| 293 | `'\n'` |
| 303 | `'net'` |
| 304 | `'::'` |
| 305 | `'reg'` |
| 306 | `'istry'` |
| 307 | `'_'` |
| 308 | `'controlled'` |
| 309 | `'_'` |
| 310 | `'dom'` |
| 311 | `'ains'` |
| 312 | `'::'` |
| 313 | `'IN'` |
| 314 | `'CL'` |
| 315 | `'U'` |
| 316 | `'DE'` |
| 317 | `'_'` |
| 318 | `'PR'` |
| 319 | `'IV'` |
| 320 | `'ATE'` |
| 321 | `'_'` |
| 322 | `'REG'` |
| 323 | `'IS'` |
| 324 | `'TR'` |
| 325 | `'IES'` |
| 326 | `');'` |
| 327 | `'\n'` |
| 329 | `'return'` |
| 330 | `'!'` |
| 331 | `'pre'` |
| 332 | `'vious'` |
| 333 | `'_'` |
| 334 | `'domain'` |
| 335 | `'.'` |
| 336 | `'empty'` |
| 337 | `'()'` |
| 338 | `'&&'` |
| 339 | `'previous'` |
| 340 | `'_'` |
| 341 | `'domain'` |
| 342 | `'=='` |
| 343 | `'new'` |
| 344 | `'_'` |
| 345 | `'domain'` |
| 346 | `';'` |
| 347 | `'\n'` |
| 348 | `'}'` |
| 349 | `'\n'` |
