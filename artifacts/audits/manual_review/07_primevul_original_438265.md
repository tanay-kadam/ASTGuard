# Review 07: `primevul:original:438265` (cpp)

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
   1 | TEST(HeaderMapImplTest, AddCopy) {
   2 |   TestRequestHeaderMapImpl headers;
   3 | 
   4 |   // Start with a string value.
   5 |   std::unique_ptr<LowerCaseString> lcKeyPtr(new LowerCaseString("hello"));
   6 |   headers.addCopy(*lcKeyPtr, "world");
   7 | 
   8 |   const HeaderString& value = headers.get(*lcKeyPtr)->value();
   9 | 
  10 |   EXPECT_EQ("world", value.getStringView());
  11 |   EXPECT_EQ(5UL, value.size());
  12 | 
  13 |   lcKeyPtr.reset();
  14 | 
  15 |   const HeaderString& value2 = headers.get(LowerCaseString("hello"))->value();
  16 | 
  17 |   EXPECT_EQ("world", value2.getStringView());
  18 |   EXPECT_EQ(5UL, value2.size());
  19 |   EXPECT_EQ(value.getStringView(), value2.getStringView());
  20 |   EXPECT_EQ(1UL, headers.size());
  21 | 
  22 |   // Repeat with an int value.
  23 |   //
  24 |   // addReferenceKey and addCopy can both add multiple instances of a
  25 |   // given header, so we need to delete the old "hello" header.
  26 |   // Test that removing will return 0 byte size.
  27 |   EXPECT_EQ(1UL, headers.remove(LowerCaseString("hello")));
  28 |   EXPECT_EQ(headers.byteSize(), 0);
  29 | 
  30 |   // Build "hello" with string concatenation to make it unlikely that the
  31 |   // compiler is just reusing the same string constant for everything.
  32 |   lcKeyPtr = std::make_unique<LowerCaseString>(std::string("he") + "llo");
  33 |   EXPECT_STREQ("hello", lcKeyPtr->get().c_str());
  34 | 
  35 |   headers.addCopy(*lcKeyPtr, 42);
  36 | 
  37 |   const HeaderString& value3 = headers.get(*lcKeyPtr)->value();
  38 | 
  39 |   EXPECT_EQ("42", value3.getStringView());
  40 |   EXPECT_EQ(2UL, value3.size());
  41 | 
  42 |   lcKeyPtr.reset();
  43 | 
  44 |   const HeaderString& value4 = headers.get(LowerCaseString("hello"))->value();
  45 | 
  46 |   EXPECT_EQ("42", value4.getStringView());
  47 |   EXPECT_EQ(2UL, value4.size());
  48 |   EXPECT_EQ(1UL, headers.size());
  49 | 
  50 |   // Here, again, we'll build yet another key string.
  51 |   LowerCaseString lcKey3(std::string("he") + "ll" + "o");
  52 |   EXPECT_STREQ("hello", lcKey3.get().c_str());
  53 | 
  54 |   EXPECT_EQ("42", headers.get(lcKey3)->value().getStringView());
  55 |   EXPECT_EQ(2UL, headers.get(lcKey3)->value().size());
  56 | 
  57 |   LowerCaseString envoy_retry_on("x-envoy-retry-on");
  58 |   headers.addCopy(envoy_retry_on, "max-age=1345");
  59 |   EXPECT_EQ("max-age=1345", headers.get(envoy_retry_on)->value().getStringView());
  60 |   EXPECT_EQ("max-age=1345", headers.getEnvoyRetryOnValue());
  61 |   headers.addCopy(envoy_retry_on, "public");
  62 |   EXPECT_EQ("max-age=1345,public", headers.get(envoy_retry_on)->value().getStringView());
  63 |   headers.addCopy(envoy_retry_on, "");
  64 |   EXPECT_EQ("max-age=1345,public", headers.get(envoy_retry_on)->value().getStringView());
  65 |   headers.addCopy(envoy_retry_on, 123);
  66 |   EXPECT_EQ("max-age=1345,public,123", headers.get(envoy_retry_on)->value().getStringView());
  67 |   headers.addCopy(envoy_retry_on, std::numeric_limits<uint64_t>::max());
  68 |   EXPECT_EQ("max-age=1345,public,123,18446744073709551615",
  69 |             headers.get(envoy_retry_on)->value().getStringView());
  70 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `TEST` | 1:1 |
| 2 | `HeaderMapImplTest` | 1:6 |
| 4 | `AddCopy` | 1:25 |
| 7 | `TestRequestHeaderMapImpl` | 2:3 |
| 8 | `headers` | 2:28 |
| 10 | `std` | 5:3 |
| 12 | `unique_ptr` | 5:8 |
| 14 | `LowerCaseString` | 5:19 |
| 16 | `lcKeyPtr` | 5:36 |
| 18 | `new` | 5:45 |
| 19 | `LowerCaseString` | 5:49 |
| 25 | `headers` | 6:3 |
| 27 | `addCopy` | 6:11 |
| 30 | `lcKeyPtr` | 6:20 |
| 35 | `const` | 8:3 |
| 36 | `HeaderString` | 8:9 |
| 38 | `value` | 8:23 |
| 40 | `headers` | 8:31 |
| 42 | `get` | 8:39 |
| 45 | `lcKeyPtr` | 8:44 |
| 48 | `value` | 8:55 |
| 52 | `EXPECT_EQ` | 10:3 |
| 56 | `value` | 10:22 |
| 58 | `getStringView` | 10:28 |
| 63 | `EXPECT_EQ` | 11:3 |
| 67 | `value` | 11:18 |
| 69 | `size` | 11:24 |
| 74 | `lcKeyPtr` | 13:3 |
| 76 | `reset` | 13:12 |
| 80 | `const` | 15:3 |
| 81 | `HeaderString` | 15:9 |
| 83 | `value2` | 15:23 |
| 85 | `headers` | 15:32 |
| 87 | `get` | 15:40 |
| 89 | `LowerCaseString` | 15:44 |
| 95 | `value` | 15:71 |
| 99 | `EXPECT_EQ` | 17:3 |
| 103 | `value2` | 17:22 |
| 105 | `getStringView` | 17:29 |
| 110 | `EXPECT_EQ` | 18:3 |
| 114 | `value2` | 18:18 |
| 116 | `size` | 18:25 |
| 121 | `EXPECT_EQ` | 19:3 |
| 123 | `value` | 19:13 |
| 125 | `getStringView` | 19:19 |
| 129 | `value2` | 19:36 |
| 131 | `getStringView` | 19:43 |
| 136 | `EXPECT_EQ` | 20:3 |
| 140 | `headers` | 20:18 |
| 142 | `size` | 20:26 |
| 147 | `EXPECT_EQ` | 27:3 |
| 151 | `headers` | 27:18 |
| 153 | `remove` | 27:26 |
| 155 | `LowerCaseString` | 27:33 |
| 162 | `EXPECT_EQ` | 28:3 |
| 164 | `headers` | 28:13 |
| 166 | `byteSize` | 28:21 |
| 173 | `lcKeyPtr` | 32:3 |
| 175 | `std` | 32:14 |
| 177 | `make_unique` | 32:19 |
| 179 | `LowerCaseString` | 32:31 |
| 182 | `std` | 32:48 |
| 184 | `string` | 32:53 |
| 192 | `EXPECT_STREQ` | 33:3 |
| 196 | `lcKeyPtr` | 33:25 |
| 198 | `get` | 33:35 |
| 202 | `c_str` | 33:41 |
| 207 | `headers` | 35:3 |
| 209 | `addCopy` | 35:11 |
| 212 | `lcKeyPtr` | 35:20 |
| 217 | `const` | 37:3 |
| 218 | `HeaderString` | 37:9 |
| 220 | `value3` | 37:23 |
| 222 | `headers` | 37:32 |
| 224 | `get` | 37:40 |
| 227 | `lcKeyPtr` | 37:45 |
| 230 | `value` | 37:56 |
| 234 | `EXPECT_EQ` | 39:3 |
| 238 | `value3` | 39:19 |
| 240 | `getStringView` | 39:26 |
| 245 | `EXPECT_EQ` | 40:3 |
| 249 | `value3` | 40:18 |
| 251 | `size` | 40:25 |
| 256 | `lcKeyPtr` | 42:3 |
| 258 | `reset` | 42:12 |
| 262 | `const` | 44:3 |
| 263 | `HeaderString` | 44:9 |
| 265 | `value4` | 44:23 |
| 267 | `headers` | 44:32 |
| 269 | `get` | 44:40 |
| 271 | `LowerCaseString` | 44:44 |
| 277 | `value` | 44:71 |
| 281 | `EXPECT_EQ` | 46:3 |
| 285 | `value4` | 46:19 |
| 287 | `getStringView` | 46:26 |
| 292 | `EXPECT_EQ` | 47:3 |
| 296 | `value4` | 47:18 |
| 298 | `size` | 47:25 |
| 303 | `EXPECT_EQ` | 48:3 |
| 307 | `headers` | 48:18 |
| 309 | `size` | 48:26 |
| 314 | `LowerCaseString` | 51:3 |
| 315 | `lcKey3` | 51:19 |
| 317 | `std` | 51:26 |
| 319 | `string` | 51:31 |
| 329 | `EXPECT_STREQ` | 52:3 |
| 333 | `lcKey3` | 52:25 |
| 335 | `get` | 52:32 |
| 339 | `c_str` | 52:38 |
| 344 | `EXPECT_EQ` | 54:3 |
| 348 | `headers` | 54:19 |
| 350 | `get` | 54:27 |
| 352 | `lcKey3` | 54:31 |
| 355 | `value` | 54:40 |
| 359 | `getStringView` | 54:48 |
| 364 | `EXPECT_EQ` | 55:3 |
| 368 | `headers` | 55:18 |
| 370 | `get` | 55:26 |
| 372 | `lcKey3` | 55:30 |
| 375 | `value` | 55:39 |
| 379 | `size` | 55:47 |
| 384 | `LowerCaseString` | 57:3 |
| 385 | `envoy_retry_on` | 57:19 |
| 390 | `headers` | 58:3 |
| 392 | `addCopy` | 58:11 |
| 394 | `envoy_retry_on` | 58:19 |
| 399 | `EXPECT_EQ` | 59:3 |
| 403 | `headers` | 59:29 |
| 405 | `get` | 59:37 |
| 407 | `envoy_retry_on` | 59:41 |
| 410 | `value` | 59:58 |
| 414 | `getStringView` | 59:66 |
| 419 | `EXPECT_EQ` | 60:3 |
| 423 | `headers` | 60:29 |
| 425 | `getEnvoyRetryOnValue` | 60:37 |
| 430 | `headers` | 61:3 |
| 432 | `addCopy` | 61:11 |
| 434 | `envoy_retry_on` | 61:19 |
| 439 | `EXPECT_EQ` | 62:3 |
| 443 | `headers` | 62:36 |
| 445 | `get` | 62:44 |
| 447 | `envoy_retry_on` | 62:48 |
| 450 | `value` | 62:65 |
| 454 | `getStringView` | 62:73 |
| 459 | `headers` | 63:3 |
| 461 | `addCopy` | 63:11 |
| 463 | `envoy_retry_on` | 63:19 |
| 468 | `EXPECT_EQ` | 64:3 |
| 472 | `headers` | 64:36 |
| 474 | `get` | 64:44 |
| 476 | `envoy_retry_on` | 64:48 |
| 479 | `value` | 64:65 |
| 483 | `getStringView` | 64:73 |
| 488 | `headers` | 65:3 |
| 490 | `addCopy` | 65:11 |
| 492 | `envoy_retry_on` | 65:19 |
| 497 | `EXPECT_EQ` | 66:3 |
| 501 | `headers` | 66:40 |
| 503 | `get` | 66:48 |
| 505 | `envoy_retry_on` | 66:52 |
| 508 | `value` | 66:69 |
| 512 | `getStringView` | 66:77 |
| 517 | `headers` | 67:3 |
| 519 | `addCopy` | 67:11 |
| 521 | `envoy_retry_on` | 67:19 |
| 523 | `std` | 67:35 |
| 525 | `numeric_limits` | 67:40 |
| 527 | `uint64_t` | 67:55 |
| 530 | `max` | 67:66 |
| 535 | `EXPECT_EQ` | 68:3 |
| 539 | `headers` | 69:13 |
| 541 | `get` | 69:21 |
| 543 | `envoy_retry_on` | 69:25 |
| 546 | `value` | 69:42 |
| 550 | `getStringView` | 69:50 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'T'` |
| 2 | `'EST'` |
| 3 | `'('` |
| 4 | `'Header'` |
| 5 | `'Map'` |
| 6 | `'Impl'` |
| 7 | `'Test'` |
| 8 | `','` |
| 9 | `'Add'` |
| 10 | `'Copy'` |
| 11 | `')'` |
| 12 | `'{'` |
| 13 | `'\n'` |
| 15 | `'Test'` |
| 16 | `'Request'` |
| 17 | `'Header'` |
| 18 | `'Map'` |
| 19 | `'Impl'` |
| 20 | `'headers'` |
| 21 | `';'` |
| 22 | `'\n\n'` |
| 24 | `'//'` |
| 25 | `'Start'` |
| 26 | `'with'` |
| 27 | `'a'` |
| 28 | `'string'` |
| 29 | `'value'` |
| 30 | `'.'` |
| 31 | `'\n'` |
| 33 | `'std'` |
| 34 | `'::'` |
| 35 | `'unique'` |
| 36 | `'_'` |
| 37 | `'ptr'` |
| 38 | `'<'` |
| 39 | `'Lower'` |
| 40 | `'Case'` |
| 41 | `'String'` |
| 42 | `'>'` |
| 43 | `'l'` |
| 44 | `'c'` |
| 45 | `'Key'` |
| 46 | `'Ptr'` |
| 47 | `'('` |
| 48 | `'new'` |
| 49 | `'Lower'` |
| 50 | `'Case'` |
| 51 | `'String'` |
| 52 | `'("'` |
| 53 | `'hello'` |
| 54 | `'")'` |
| 55 | `');'` |
| 56 | `'\n'` |
| 58 | `'headers'` |
| 59 | `'.'` |
| 60 | `'add'` |
| 61 | `'Copy'` |
| 62 | `'(*'` |
| 63 | `'lc'` |
| 64 | `'Key'` |
| 65 | `'Ptr'` |
| 66 | `','` |
| 67 | `'"'` |
| 68 | `'world'` |
| 69 | `'");'` |
| 70 | `'\n\n'` |
| 72 | `'const'` |
| 73 | `'Header'` |
| 74 | `'String'` |
| 75 | `'&'` |
| 76 | `'value'` |
| 77 | `'='` |
| 78 | `'headers'` |
| 79 | `'.'` |
| 80 | `'get'` |
| 81 | `'(*'` |
| 82 | `'lc'` |
| 83 | `'Key'` |
| 84 | `'Ptr'` |
| 85 | `')'` |
| 86 | `'->'` |
| 87 | `'value'` |
| 88 | `'();'` |
| 89 | `'\n\n'` |
| 91 | `'EXP'` |
| 92 | `'ECT'` |
| 93 | `'_'` |
| 94 | `'E'` |
| 95 | `'Q'` |
| 96 | `'("'` |
| 97 | `'world'` |
| 98 | `'",'` |
| 99 | `'value'` |
| 100 | `'.'` |
| 101 | `'get'` |
| 102 | `'String'` |
| 103 | `'View'` |
| 104 | `'());'` |
| 105 | `'\n'` |
| 107 | `'EXP'` |
| 108 | `'ECT'` |
| 109 | `'_'` |
| 110 | `'E'` |
| 111 | `'Q'` |
| 112 | `'('` |
| 113 | `'5'` |
| 114 | `'UL'` |
| 115 | `','` |
| 116 | `'value'` |
| 117 | `'.'` |
| 118 | `'size'` |
| 119 | `'());'` |
| 120 | `'\n\n'` |
| 122 | `'l'` |
| 123 | `'c'` |
| 124 | `'Key'` |
| 125 | `'Ptr'` |
| 126 | `'.'` |
| 127 | `'reset'` |
| 128 | `'();'` |
| 129 | `'\n\n'` |
| 131 | `'const'` |
| 132 | `'Header'` |
| 133 | `'String'` |
| 134 | `'&'` |
| 135 | `'value'` |
| 136 | `'2'` |
| 137 | `'='` |
| 138 | `'headers'` |
| 139 | `'.'` |
| 140 | `'get'` |
| 141 | `'('` |
| 142 | `'Lower'` |
| 143 | `'Case'` |
| 144 | `'String'` |
| 145 | `'("'` |
| 146 | `'hello'` |
| 147 | `'"))'` |
| 148 | `'->'` |
| 149 | `'value'` |
| 150 | `'();'` |
| 151 | `'\n\n'` |
| 153 | `'EXP'` |
| 154 | `'ECT'` |
| 155 | `'_'` |
| 156 | `'E'` |
| 157 | `'Q'` |
| 158 | `'("'` |
| 159 | `'world'` |
| 160 | `'",'` |
| 161 | `'value'` |
| 162 | `'2'` |
| 163 | `'.'` |
| 164 | `'get'` |
| 165 | `'String'` |
| 166 | `'View'` |
| 167 | `'());'` |
| 168 | `'\n'` |
| 170 | `'EXP'` |
| 171 | `'ECT'` |
| 172 | `'_'` |
| 173 | `'E'` |
| 174 | `'Q'` |
| 175 | `'('` |
| 176 | `'5'` |
| 177 | `'UL'` |
| 178 | `','` |
| 179 | `'value'` |
| 180 | `'2'` |
| 181 | `'.'` |
| 182 | `'size'` |
| 183 | `'());'` |
| 184 | `'\n'` |
| 186 | `'EXP'` |
| 187 | `'ECT'` |
| 188 | `'_'` |
| 189 | `'E'` |
| 190 | `'Q'` |
| 191 | `'('` |
| 192 | `'value'` |
| 193 | `'.'` |
| 194 | `'get'` |
| 195 | `'String'` |
| 196 | `'View'` |
| 197 | `'(),'` |
| 198 | `'value'` |
| 199 | `'2'` |
| 200 | `'.'` |
| 201 | `'get'` |
| 202 | `'String'` |
| 203 | `'View'` |
| 204 | `'());'` |
| 205 | `'\n'` |
| 207 | `'EXP'` |
| 208 | `'ECT'` |
| 209 | `'_'` |
| 210 | `'E'` |
| 211 | `'Q'` |
| 212 | `'('` |
| 213 | `'1'` |
| 214 | `'UL'` |
| 215 | `','` |
| 216 | `'headers'` |
| 217 | `'.'` |
| 218 | `'size'` |
| 219 | `'());'` |
| 220 | `'\n\n'` |
| 222 | `'//'` |
| 223 | `'Repeat'` |
| 224 | `'with'` |
| 225 | `'an'` |
| 226 | `'int'` |
| 227 | `'value'` |
| 228 | `'.'` |
| 229 | `'\n'` |
| 231 | `'//'` |
| 232 | `'\n'` |
| 234 | `'//'` |
| 235 | `'add'` |
| 236 | `'Reference'` |
| 237 | `'Key'` |
| 238 | `'and'` |
| 239 | `'add'` |
| 240 | `'Copy'` |
| 241 | `'can'` |
| 242 | `'both'` |
| 243 | `'add'` |
| 244 | `'multiple'` |
| 245 | `'instances'` |
| 246 | `'of'` |
| 247 | `'a'` |
| 248 | `'\n'` |
| 250 | `'//'` |
| 251 | `'given'` |
| 252 | `'header'` |
| 253 | `','` |
| 254 | `'so'` |
| 255 | `'we'` |
| 256 | `'need'` |
| 257 | `'to'` |
| 258 | `'delete'` |
| 259 | `'the'` |
| 260 | `'old'` |
| 261 | `'"'` |
| 262 | `'hello'` |
| 263 | `'"'` |
| 264 | `'header'` |
| 265 | `'.'` |
| 266 | `'\n'` |
| 268 | `'//'` |
| 269 | `'Test'` |
| 270 | `'that'` |
| 271 | `'removing'` |
| 272 | `'will'` |
| 273 | `'return'` |
| 274 | `'0'` |
| 275 | `'byte'` |
| 276 | `'size'` |
| 277 | `'.'` |
| 278 | `'\n'` |
| 280 | `'EXP'` |
| 281 | `'ECT'` |
| 282 | `'_'` |
| 283 | `'E'` |
| 284 | `'Q'` |
| 285 | `'('` |
| 286 | `'1'` |
| 287 | `'UL'` |
| 288 | `','` |
| 289 | `'headers'` |
| 290 | `'.'` |
| 291 | `'remove'` |
| 292 | `'('` |
| 293 | `'Lower'` |
| 294 | `'Case'` |
| 295 | `'String'` |
| 296 | `'("'` |
| 297 | `'hello'` |
| 298 | `'"))'` |
| 299 | `');'` |
| 300 | `'\n'` |
| 302 | `'EXP'` |
| 303 | `'ECT'` |
| 304 | `'_'` |
| 305 | `'E'` |
| 306 | `'Q'` |
| 307 | `'('` |
| 308 | `'headers'` |
| 309 | `'.'` |
| 310 | `'byte'` |
| 311 | `'Size'` |
| 312 | `'(),'` |
| 313 | `'0'` |
| 314 | `');'` |
| 315 | `'\n\n'` |
| 317 | `'//'` |
| 318 | `'Build'` |
| 319 | `'"'` |
| 320 | `'hello'` |
| 321 | `'"'` |
| 322 | `'with'` |
| 323 | `'string'` |
| 324 | `'conc'` |
| 325 | `'aten'` |
| 326 | `'ation'` |
| 327 | `'to'` |
| 328 | `'make'` |
| 329 | `'it'` |
| 330 | `'unlikely'` |
| 331 | `'that'` |
| 332 | `'the'` |
| 333 | `'\n'` |
| 335 | `'//'` |
| 336 | `'compiler'` |
| 337 | `'is'` |
| 338 | `'just'` |
| 339 | `'re'` |
| 340 | `'using'` |
| 341 | `'the'` |
| 342 | `'same'` |
| 343 | `'string'` |
| 344 | `'constant'` |
| 345 | `'for'` |
| 346 | `'everything'` |
| 347 | `'.'` |
| 348 | `'\n'` |
| 350 | `'l'` |
| 351 | `'c'` |
| 352 | `'Key'` |
| 353 | `'Ptr'` |
| 354 | `'='` |
| 355 | `'std'` |
| 356 | `'::'` |
| 357 | `'make'` |
| 358 | `'_'` |
| 359 | `'unique'` |
| 360 | `'<'` |
| 361 | `'Lower'` |
| 362 | `'Case'` |
| 363 | `'String'` |
| 364 | `'>('` |
| 365 | `'std'` |
| 366 | `'::'` |
| 367 | `'string'` |
| 368 | `'("'` |
| 369 | `'he'` |
| 370 | `'")'` |
| 371 | `'+'` |
| 372 | `'"'` |
| 373 | `'llo'` |
| 374 | `'");'` |
| 375 | `'\n'` |
| 377 | `'EXP'` |
| 378 | `'ECT'` |
| 379 | `'_'` |
| 380 | `'ST'` |
| 381 | `'RE'` |
| 382 | `'Q'` |
| 383 | `'("'` |
| 384 | `'hello'` |
| 385 | `'",'` |
| 386 | `'l'` |
| 387 | `'c'` |
| 388 | `'Key'` |
| 389 | `'Ptr'` |
| 390 | `'->'` |
| 391 | `'get'` |
| 392 | `'().'` |
| 393 | `'c'` |
| 394 | `'_'` |
| 395 | `'str'` |
| 396 | `'());'` |
| 397 | `'\n\n'` |
| 399 | `'headers'` |
| 400 | `'.'` |
| 401 | `'add'` |
| 402 | `'Copy'` |
| 403 | `'(*'` |
| 404 | `'lc'` |
| 405 | `'Key'` |
| 406 | `'Ptr'` |
| 407 | `','` |
| 408 | `'42'` |
| 409 | `');'` |
| 410 | `'\n\n'` |
| 412 | `'const'` |
| 413 | `'Header'` |
| 414 | `'String'` |
| 415 | `'&'` |
| 416 | `'value'` |
| 417 | `'3'` |
| 418 | `'='` |
| 419 | `'headers'` |
| 420 | `'.'` |
| 421 | `'get'` |
| 422 | `'(*'` |
| 423 | `'lc'` |
| 424 | `'Key'` |
| 425 | `'Ptr'` |
| 426 | `')'` |
| 427 | `'->'` |
| 428 | `'value'` |
| 429 | `'();'` |
| 430 | `'\n\n'` |
| 432 | `'EXP'` |
| 433 | `'ECT'` |
| 434 | `'_'` |
| 435 | `'E'` |
| 436 | `'Q'` |
| 437 | `'("'` |
| 438 | `'42'` |
| 439 | `'",'` |
| 440 | `'value'` |
| 441 | `'3'` |
| 442 | `'.'` |
| 443 | `'get'` |
| 444 | `'String'` |
| 445 | `'View'` |
| 446 | `'());'` |
| 447 | `'\n'` |
| 449 | `'EXP'` |
| 450 | `'ECT'` |
| 451 | `'_'` |
| 452 | `'E'` |
| 453 | `'Q'` |
| 454 | `'('` |
| 455 | `'2'` |
| 456 | `'UL'` |
| 457 | `','` |
| 458 | `'value'` |
| 459 | `'3'` |
| 460 | `'.'` |
| 461 | `'size'` |
| 462 | `'());'` |
| 463 | `'\n\n'` |
| 465 | `'l'` |
| 466 | `'c'` |
| 467 | `'Key'` |
| 468 | `'Ptr'` |
| 469 | `'.'` |
| 470 | `'reset'` |
| 471 | `'();'` |
| 472 | `'\n\n'` |
| 474 | `'const'` |
| 475 | `'Header'` |
| 476 | `'String'` |
| 477 | `'&'` |
| 478 | `'value'` |
| 479 | `'4'` |
| 480 | `'='` |
| 481 | `'headers'` |
| 482 | `'.'` |
| 483 | `'get'` |
| 484 | `'('` |
| 485 | `'Lower'` |
| 486 | `'Case'` |
| 487 | `'String'` |
| 488 | `'("'` |
| 489 | `'hello'` |
| 490 | `'"))'` |
| 491 | `'->'` |
| 492 | `'value'` |
| 493 | `'();'` |
| 494 | `'\n\n'` |
| 496 | `'EXP'` |
| 497 | `'ECT'` |
| 498 | `'_'` |
| 499 | `'E'` |
| 500 | `'Q'` |
| 501 | `'("'` |
| 502 | `'42'` |
| 503 | `'",'` |
| 504 | `'value'` |
| 505 | `'4'` |
| 506 | `'.'` |
| 507 | `'get'` |
| 508 | `'String'` |
| 509 | `'View'` |
| 510 | `'());'` |
