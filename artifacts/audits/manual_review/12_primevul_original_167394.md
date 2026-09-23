# Review 12: `primevul:original:167394` (cpp)

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
   1 | i915_gem_execbuffer_relocate_object(struct drm_i915_gem_object *obj,
   2 | 				    struct eb_objects *eb)
   3 | {
   4 | 	struct drm_i915_gem_relocation_entry __user *user_relocs;
   5 | 	struct drm_i915_gem_exec_object2 *entry = obj->exec_entry;
   6 | 	int i, ret;
   7 | 
   8 | 	user_relocs = (void __user *)(uintptr_t)entry->relocs_ptr;
   9 | 	for (i = 0; i < entry->relocation_count; i++) {
  10 | 		struct drm_i915_gem_relocation_entry reloc;
  11 | 
  12 | 		if (__copy_from_user_inatomic(&reloc,
  13 | 					      user_relocs+i,
  14 | 					      sizeof(reloc)))
  15 | 			return -EFAULT;
  16 | 
  17 | 		ret = i915_gem_execbuffer_relocate_entry(obj, eb, &reloc);
  18 | 		if (ret)
  19 | 			return ret;
  20 | 
  21 | 		if (__copy_to_user_inatomic(&user_relocs[i].presumed_offset,
  22 | 					    &reloc.presumed_offset,
  23 | 					    sizeof(reloc.presumed_offset)))
  24 | 			return -EFAULT;
  25 | 	}
  26 | 
  27 | 	return 0;
  28 | }
  29 | 
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `i915_gem_execbuffer_relocate_object` | 1:1 |
| 2 | `struct` | 1:37 |
| 3 | `drm_i915_gem_object` | 1:44 |
| 5 | `obj` | 1:65 |
| 7 | `struct` | 2:9 |
| 8 | `eb_objects` | 2:16 |
| 10 | `eb` | 2:28 |
| 13 | `struct` | 4:2 |
| 14 | `drm_i915_gem_relocation_entry` | 4:9 |
| 15 | `__user` | 4:39 |
| 17 | `user_relocs` | 4:47 |
| 19 | `struct` | 5:2 |
| 20 | `drm_i915_gem_exec_object2` | 5:9 |
| 22 | `entry` | 5:36 |
| 24 | `obj` | 5:44 |
| 26 | `exec_entry` | 5:49 |
| 28 | `int` | 6:2 |
| 29 | `i` | 6:6 |
| 31 | `ret` | 6:9 |
| 33 | `user_relocs` | 8:2 |
| 36 | `void` | 8:17 |
| 37 | `__user` | 8:22 |
| 41 | `uintptr_t` | 8:32 |
| 43 | `entry` | 8:42 |
| 45 | `relocs_ptr` | 8:49 |
| 47 | `for` | 9:2 |
| 49 | `i` | 9:7 |
| 53 | `i` | 9:14 |
| 55 | `entry` | 9:18 |
| 57 | `relocation_count` | 9:25 |
| 59 | `i` | 9:43 |
| 63 | `struct` | 10:3 |
| 64 | `drm_i915_gem_relocation_entry` | 10:10 |
| 65 | `reloc` | 10:40 |
| 67 | `if` | 12:3 |
| 69 | `__copy_from_user_inatomic` | 12:7 |
| 72 | `reloc` | 12:34 |
| 74 | `user_relocs` | 13:12 |
| 76 | `i` | 13:24 |
| 78 | `sizeof` | 14:12 |
| 80 | `reloc` | 14:19 |
| 84 | `return` | 15:4 |
| 86 | `EFAULT` | 15:12 |
| 88 | `ret` | 17:3 |
| 90 | `i915_gem_execbuffer_relocate_entry` | 17:9 |
| 92 | `obj` | 17:44 |
| 94 | `eb` | 17:49 |
| 97 | `reloc` | 17:54 |
| 100 | `if` | 18:3 |
| 102 | `ret` | 18:7 |
| 104 | `return` | 19:4 |
| 105 | `ret` | 19:11 |
| 107 | `if` | 21:3 |
| 109 | `__copy_to_user_inatomic` | 21:7 |
| 112 | `user_relocs` | 21:32 |
| 114 | `i` | 21:44 |
| 117 | `presumed_offset` | 21:47 |
| 120 | `reloc` | 22:11 |
| 122 | `presumed_offset` | 22:17 |
| 124 | `sizeof` | 23:10 |
| 126 | `reloc` | 23:17 |
| 128 | `presumed_offset` | 23:23 |
| 132 | `return` | 24:4 |
| 134 | `EFAULT` | 24:12 |
| 137 | `return` | 27:2 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'i'` |
| 2 | `'915'` |
| 3 | `'_'` |
| 4 | `'gem'` |
| 5 | `'_'` |
| 6 | `'exec'` |
| 7 | `'buffer'` |
| 8 | `'_'` |
| 9 | `'rel'` |
| 10 | `'ocate'` |
| 11 | `'_'` |
| 12 | `'object'` |
| 13 | `'('` |
| 14 | `'struct'` |
| 15 | `'dr'` |
| 16 | `'m'` |
| 17 | `'_'` |
| 18 | `'i'` |
| 19 | `'915'` |
| 20 | `'_'` |
| 21 | `'gem'` |
| 22 | `'_'` |
| 23 | `'object'` |
| 24 | `'*'` |
| 25 | `'obj'` |
| 26 | `','` |
| 27 | `'\n'` |
| 28 | `'\t'` |
| 29 | `'\t'` |
| 30 | `'\t'` |
| 31 | `'\t'` |
| 35 | `'struct'` |
| 36 | `'eb'` |
| 37 | `'_'` |
| 38 | `'objects'` |
| 39 | `'*'` |
| 40 | `'eb'` |
| 41 | `')'` |
| 42 | `'\n'` |
| 43 | `'{'` |
| 44 | `'\n'` |
| 45 | `'\t'` |
| 46 | `'struct'` |
| 47 | `'dr'` |
| 48 | `'m'` |
| 49 | `'_'` |
| 50 | `'i'` |
| 51 | `'915'` |
| 52 | `'_'` |
| 53 | `'gem'` |
| 54 | `'_'` |
| 55 | `'rel'` |
| 56 | `'ocation'` |
| 57 | `'_'` |
| 58 | `'entry'` |
| 59 | `'__'` |
| 60 | `'user'` |
| 61 | `'*'` |
| 62 | `'user'` |
| 63 | `'_'` |
| 64 | `'rel'` |
| 65 | `'oc'` |
| 66 | `'s'` |
| 67 | `';'` |
| 68 | `'\n'` |
| 69 | `'\t'` |
| 70 | `'struct'` |
| 71 | `'dr'` |
| 72 | `'m'` |
| 73 | `'_'` |
| 74 | `'i'` |
| 75 | `'915'` |
| 76 | `'_'` |
| 77 | `'gem'` |
| 78 | `'_'` |
| 79 | `'exec'` |
| 80 | `'_'` |
| 81 | `'object'` |
| 82 | `'2'` |
| 83 | `'*'` |
| 84 | `'entry'` |
| 85 | `'='` |
| 86 | `'obj'` |
| 87 | `'->'` |
| 88 | `'exec'` |
| 89 | `'_'` |
| 90 | `'entry'` |
| 91 | `';'` |
| 92 | `'\n'` |
| 93 | `'\t'` |
| 94 | `'int'` |
| 95 | `'i'` |
| 96 | `','` |
| 97 | `'ret'` |
| 98 | `';'` |
| 99 | `'\n\n'` |
| 100 | `'\t'` |
| 101 | `'user'` |
| 102 | `'_'` |
| 103 | `'rel'` |
| 104 | `'oc'` |
| 105 | `'s'` |
| 106 | `'='` |
| 107 | `'('` |
| 108 | `'void'` |
| 109 | `'__'` |
| 110 | `'user'` |
| 111 | `'*'` |
| 112 | `')('` |
| 113 | `'uint'` |
| 114 | `'ptr'` |
| 115 | `'_'` |
| 116 | `'t'` |
| 117 | `')'` |
| 118 | `'entry'` |
| 119 | `'->'` |
| 120 | `'rel'` |
| 121 | `'oc'` |
| 122 | `'s'` |
| 123 | `'_'` |
| 124 | `'ptr'` |
| 125 | `';'` |
| 126 | `'\n'` |
| 127 | `'\t'` |
| 128 | `'for'` |
| 129 | `'('` |
| 130 | `'i'` |
| 131 | `'='` |
| 132 | `'0'` |
| 133 | `';'` |
| 134 | `'i'` |
| 135 | `'<'` |
| 136 | `'entry'` |
| 137 | `'->'` |
| 138 | `'rel'` |
| 139 | `'ocation'` |
| 140 | `'_'` |
| 141 | `'count'` |
| 142 | `';'` |
| 143 | `'i'` |
| 144 | `'++)'` |
| 145 | `'{'` |
| 146 | `'\n'` |
| 147 | `'\t'` |
| 148 | `'\t'` |
| 149 | `'struct'` |
| 150 | `'dr'` |
| 151 | `'m'` |
| 152 | `'_'` |
| 153 | `'i'` |
| 154 | `'915'` |
| 155 | `'_'` |
| 156 | `'gem'` |
| 157 | `'_'` |
| 158 | `'rel'` |
| 159 | `'ocation'` |
| 160 | `'_'` |
| 161 | `'entry'` |
| 162 | `'rel'` |
| 163 | `'oc'` |
| 164 | `';'` |
| 165 | `'\n\n'` |
| 166 | `'\t'` |
| 167 | `'\t'` |
| 168 | `'if'` |
| 169 | `'('` |
| 170 | `'__'` |
| 171 | `'copy'` |
| 172 | `'_'` |
| 173 | `'from'` |
| 174 | `'_'` |
| 175 | `'user'` |
| 176 | `'_'` |
| 177 | `'in'` |
| 178 | `'atomic'` |
| 179 | `'(&'` |
| 180 | `'rel'` |
| 181 | `'oc'` |
| 182 | `','` |
| 183 | `'\n'` |
| 184 | `'\t'` |
| 185 | `'\t'` |
| 186 | `'\t'` |
| 187 | `'\t'` |
| 188 | `'\t'` |
| 194 | `'user'` |
| 195 | `'_'` |
| 196 | `'rel'` |
| 197 | `'oc'` |
| 198 | `'s'` |
| 199 | `'+'` |
| 200 | `'i'` |
| 201 | `','` |
| 202 | `'\n'` |
| 203 | `'\t'` |
| 204 | `'\t'` |
| 205 | `'\t'` |
| 206 | `'\t'` |
| 207 | `'\t'` |
| 213 | `'sizeof'` |
| 214 | `'('` |
| 215 | `'rel'` |
| 216 | `'oc'` |
| 217 | `')))'` |
| 218 | `'\n'` |
| 219 | `'\t'` |
| 220 | `'\t'` |
| 221 | `'\t'` |
| 222 | `'return'` |
| 223 | `'-'` |
| 224 | `'E'` |
| 225 | `'FAULT'` |
| 226 | `';'` |
| 227 | `'\n\n'` |
| 228 | `'\t'` |
| 229 | `'\t'` |
| 230 | `'ret'` |
| 231 | `'='` |
| 232 | `'i'` |
| 233 | `'915'` |
| 234 | `'_'` |
| 235 | `'gem'` |
| 236 | `'_'` |
| 237 | `'exec'` |
| 238 | `'buffer'` |
| 239 | `'_'` |
| 240 | `'rel'` |
| 241 | `'ocate'` |
| 242 | `'_'` |
| 243 | `'entry'` |
| 244 | `'('` |
| 245 | `'obj'` |
| 246 | `','` |
| 247 | `'eb'` |
| 248 | `','` |
| 249 | `'&'` |
| 250 | `'rel'` |
| 251 | `'oc'` |
| 252 | `');'` |
| 253 | `'\n'` |
| 254 | `'\t'` |
| 255 | `'\t'` |
| 256 | `'if'` |
| 257 | `'('` |
| 258 | `'ret'` |
| 259 | `')'` |
| 260 | `'\n'` |
| 261 | `'\t'` |
| 262 | `'\t'` |
| 263 | `'\t'` |
| 264 | `'return'` |
| 265 | `'ret'` |
| 266 | `';'` |
| 267 | `'\n\n'` |
| 268 | `'\t'` |
| 269 | `'\t'` |
| 270 | `'if'` |
| 271 | `'('` |
| 272 | `'__'` |
| 273 | `'copy'` |
| 274 | `'_'` |
| 275 | `'to'` |
| 276 | `'_'` |
| 277 | `'user'` |
| 278 | `'_'` |
| 279 | `'in'` |
| 280 | `'atomic'` |
| 281 | `'(&'` |
| 282 | `'user'` |
| 283 | `'_'` |
| 284 | `'rel'` |
| 285 | `'oc'` |
| 286 | `'s'` |
| 287 | `'['` |
| 288 | `'i'` |
| 289 | `'].'` |
| 290 | `'pres'` |
| 291 | `'umed'` |
| 292 | `'_'` |
| 293 | `'offset'` |
| 294 | `','` |
| 295 | `'\n'` |
| 296 | `'\t'` |
| 297 | `'\t'` |
| 298 | `'\t'` |
| 299 | `'\t'` |
| 300 | `'\t'` |
| 304 | `'&'` |
| 305 | `'rel'` |
| 306 | `'oc'` |
| 307 | `'.'` |
| 308 | `'pres'` |
| 309 | `'umed'` |
| 310 | `'_'` |
| 311 | `'offset'` |
| 312 | `','` |
| 313 | `'\n'` |
| 314 | `'\t'` |
| 315 | `'\t'` |
| 316 | `'\t'` |
| 317 | `'\t'` |
| 318 | `'\t'` |
| 322 | `'sizeof'` |
| 323 | `'('` |
| 324 | `'rel'` |
| 325 | `'oc'` |
| 326 | `'.'` |
| 327 | `'pres'` |
| 328 | `'umed'` |
| 329 | `'_'` |
| 330 | `'offset'` |
| 331 | `')))'` |
| 332 | `'\n'` |
| 333 | `'\t'` |
| 334 | `'\t'` |
| 335 | `'\t'` |
| 336 | `'return'` |
| 337 | `'-'` |
| 338 | `'E'` |
| 339 | `'FAULT'` |
| 340 | `';'` |
| 341 | `'\n'` |
| 342 | `'\t'` |
| 343 | `'}'` |
| 344 | `'\n\n'` |
| 345 | `'\t'` |
| 346 | `'return'` |
| 347 | `'0'` |
| 348 | `';'` |
| 349 | `'\n'` |
| 350 | `'}'` |
| 351 | `'\n'` |
