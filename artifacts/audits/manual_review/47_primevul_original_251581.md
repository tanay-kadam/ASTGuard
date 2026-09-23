# Review 47: `primevul:original:251581` (cpp)

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
   1 | Error HeifContext::decode_overlay_image(heif_item_id ID,
   2 |                                         std::shared_ptr<HeifPixelImage>& img,
   3 |                                         const std::vector<uint8_t>& overlay_data) const
   4 | {
   5 |   // find the IDs this image is composed of
   6 | 
   7 |   auto iref_box = m_heif_file->get_iref_box();
   8 | 
   9 |   if (!iref_box) {
  10 |     return Error(heif_error_Invalid_input,
  11 |                  heif_suberror_No_iref_box,
  12 |                  "No iref box available, but needed for iovl image");
  13 |   }
  14 | 
  15 |   std::vector<heif_item_id> image_references = iref_box->get_references(ID, fourcc("dimg"));
  16 | 
  17 |   /* TODO: probably, it is valid that an iovl image has no references ?
  18 | 
  19 |   if (image_references.empty()) {
  20 |     return Error(heif_error_Invalid_input,
  21 |                  heif_suberror_Missing_grid_images,
  22 |                  "'iovl' image with more than one reference image");
  23 |   }
  24 |   */
  25 | 
  26 | 
  27 |   ImageOverlay overlay;
  28 |   Error err = overlay.parse(image_references.size(), overlay_data);
  29 |   if (err) {
  30 |     return err;
  31 |   }
  32 | 
  33 |   if (image_references.size() != overlay.get_num_offsets()) {
  34 |     return Error(heif_error_Invalid_input,
  35 |                  heif_suberror_Invalid_overlay_data,
  36 |                  "Number of image offsets does not match the number of image references");
  37 |   }
  38 | 
  39 |   uint32_t w = overlay.get_canvas_width();
  40 |   uint32_t h = overlay.get_canvas_height();
  41 | 
  42 |   if (w >= MAX_IMAGE_WIDTH || h >= MAX_IMAGE_HEIGHT) {
  43 |     std::stringstream sstr;
  44 |     sstr << "Image size " << w << "x" << h << " exceeds the maximum image size "
  45 |          << MAX_IMAGE_WIDTH << "x" << MAX_IMAGE_HEIGHT << "\n";
  46 | 
  47 |     return Error(heif_error_Memory_allocation_error,
  48 |                  heif_suberror_Security_limit_exceeded,
  49 |                  sstr.str());
  50 |   }
  51 | 
  52 |   // TODO: seems we always have to compose this in RGB since the background color is an RGB value
  53 |   img = std::make_shared<HeifPixelImage>();
  54 |   img->create(w,h,
  55 |               heif_colorspace_RGB,
  56 |               heif_chroma_444);
  57 |   img->add_plane(heif_channel_R,w,h,8); // TODO: other bit depths
  58 |   img->add_plane(heif_channel_G,w,h,8); // TODO: other bit depths
  59 |   img->add_plane(heif_channel_B,w,h,8); // TODO: other bit depths
  60 | 
  61 |   uint16_t bkg_color[4];
  62 |   overlay.get_background_color(bkg_color);
  63 | 
  64 |   err = img->fill_RGB_16bit(bkg_color[0], bkg_color[1], bkg_color[2], bkg_color[3]);
  65 |   if (err) {
  66 |     return err;
  67 |   }
  68 | 
  69 | 
  70 |   for (size_t i=0;i<image_references.size();i++) {
  71 |     std::shared_ptr<HeifPixelImage> overlay_img;
  72 |     err = decode_image(image_references[i], overlay_img);
  73 |     if (err != Error::Ok) {
  74 |       return err;
  75 |     }
  76 | 
  77 |     overlay_img = overlay_img->convert_colorspace(heif_colorspace_RGB, heif_chroma_444);
  78 |     if (!overlay_img) {
  79 |       return Error(heif_error_Unsupported_feature, heif_suberror_Unsupported_color_conversion);
  80 |     }
  81 | 
  82 |     int32_t dx,dy;
  83 |     overlay.get_offset(i, &dx,&dy);
  84 | 
  85 |     err = img->overlay(overlay_img, dx,dy);
  86 |     if (err) {
  87 |       if (err.error_code == heif_error_Invalid_input &&
  88 |           err.sub_error_code == heif_suberror_Overlay_image_outside_of_canvas) {
  89 |         // NOP, ignore this error
  90 | 
  91 |         err = Error::Ok;
  92 |       }
  93 |       else {
  94 |         return err;
  95 |       }
  96 |     }
  97 |   }
  98 | 
  99 |   return err;
 100 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `Error` | 1:1 |
| 1 | `HeifContext` | 1:7 |
| 3 | `decode_overlay_image` | 1:20 |
| 5 | `heif_item_id` | 1:41 |
| 6 | `ID` | 1:54 |
| 8 | `std` | 2:41 |
| 10 | `shared_ptr` | 2:46 |
| 12 | `HeifPixelImage` | 2:57 |
| 15 | `img` | 2:74 |
| 17 | `const` | 3:41 |
| 18 | `std` | 3:47 |
| 20 | `vector` | 3:52 |
| 22 | `uint8_t` | 3:59 |
| 25 | `overlay_data` | 3:69 |
| 27 | `const` | 3:83 |
| 29 | `auto` | 7:3 |
| 30 | `iref_box` | 7:8 |
| 32 | `m_heif_file` | 7:19 |
| 34 | `get_iref_box` | 7:32 |
| 38 | `if` | 9:3 |
| 41 | `iref_box` | 9:8 |
| 44 | `return` | 10:5 |
| 45 | `Error` | 10:12 |
| 47 | `heif_error_Invalid_input` | 10:18 |
| 49 | `heif_suberror_No_iref_box` | 11:18 |
| 55 | `std` | 15:3 |
| 57 | `vector` | 15:8 |
| 59 | `heif_item_id` | 15:15 |
| 61 | `image_references` | 15:29 |
| 63 | `iref_box` | 15:48 |
| 65 | `get_references` | 15:58 |
| 67 | `ID` | 15:73 |
| 69 | `fourcc` | 15:77 |
| 75 | `ImageOverlay` | 27:3 |
| 76 | `overlay` | 27:16 |
| 78 | `Error` | 28:3 |
| 79 | `err` | 28:9 |
| 81 | `overlay` | 28:15 |
| 83 | `parse` | 28:23 |
| 85 | `image_references` | 28:29 |
| 87 | `size` | 28:46 |
| 91 | `overlay_data` | 28:54 |
| 94 | `if` | 29:3 |
| 96 | `err` | 29:7 |
| 99 | `return` | 30:5 |
| 100 | `err` | 30:12 |
| 103 | `if` | 33:3 |
| 105 | `image_references` | 33:7 |
| 107 | `size` | 33:24 |
| 111 | `overlay` | 33:34 |
| 113 | `get_num_offsets` | 33:42 |
| 118 | `return` | 34:5 |
| 119 | `Error` | 34:12 |
| 121 | `heif_error_Invalid_input` | 34:18 |
| 123 | `heif_suberror_Invalid_overlay_data` | 35:18 |
| 129 | `uint32_t` | 39:3 |
| 130 | `w` | 39:12 |
| 132 | `overlay` | 39:16 |
| 134 | `get_canvas_width` | 39:24 |
| 138 | `uint32_t` | 40:3 |
| 139 | `h` | 40:12 |
| 141 | `overlay` | 40:16 |
| 143 | `get_canvas_height` | 40:24 |
| 147 | `if` | 42:3 |
| 149 | `w` | 42:7 |
| 151 | `MAX_IMAGE_WIDTH` | 42:12 |
| 153 | `h` | 42:31 |
| 155 | `MAX_IMAGE_HEIGHT` | 42:36 |
| 158 | `std` | 43:5 |
| 160 | `stringstream` | 43:10 |
| 161 | `sstr` | 43:23 |
| 163 | `sstr` | 44:5 |
| 167 | `w` | 44:30 |
| 171 | `h` | 44:42 |
| 175 | `MAX_IMAGE_WIDTH` | 45:13 |
| 179 | `MAX_IMAGE_HEIGHT` | 45:39 |
| 183 | `return` | 47:5 |
| 184 | `Error` | 47:12 |
| 186 | `heif_error_Memory_allocation_error` | 47:18 |
| 188 | `heif_suberror_Security_limit_exceeded` | 48:18 |
| 190 | `sstr` | 49:18 |
| 192 | `str` | 49:23 |
| 198 | `img` | 53:3 |
| 200 | `std` | 53:9 |
| 202 | `make_shared` | 53:14 |
| 204 | `HeifPixelImage` | 53:26 |
| 209 | `img` | 54:3 |
| 211 | `create` | 54:8 |
| 213 | `w` | 54:15 |
| 215 | `h` | 54:17 |
| 217 | `heif_colorspace_RGB` | 55:15 |
| 219 | `heif_chroma_444` | 56:15 |
| 222 | `img` | 57:3 |
| 224 | `add_plane` | 57:8 |
| 226 | `heif_channel_R` | 57:18 |
| 228 | `w` | 57:33 |
| 230 | `h` | 57:35 |
| 235 | `img` | 58:3 |
| 237 | `add_plane` | 58:8 |
| 239 | `heif_channel_G` | 58:18 |
| 241 | `w` | 58:33 |
| 243 | `h` | 58:35 |
| 248 | `img` | 59:3 |
| 250 | `add_plane` | 59:8 |
| 252 | `heif_channel_B` | 59:18 |
| 254 | `w` | 59:33 |
| 256 | `h` | 59:35 |
| 261 | `uint16_t` | 61:3 |
| 262 | `bkg_color` | 61:12 |
| 267 | `overlay` | 62:3 |
| 269 | `get_background_color` | 62:11 |
| 271 | `bkg_color` | 62:32 |
| 274 | `err` | 64:3 |
| 276 | `img` | 64:9 |
| 278 | `fill_RGB_16bit` | 64:14 |
| 280 | `bkg_color` | 64:29 |
| 285 | `bkg_color` | 64:43 |
| 290 | `bkg_color` | 64:57 |
| 295 | `bkg_color` | 64:71 |
| 301 | `if` | 65:3 |
| 303 | `err` | 65:7 |
| 306 | `return` | 66:5 |
| 307 | `err` | 66:12 |
| 310 | `for` | 70:3 |
| 312 | `size_t` | 70:8 |
| 313 | `i` | 70:15 |
| 317 | `i` | 70:19 |
| 319 | `image_references` | 70:21 |
| 321 | `size` | 70:38 |
| 325 | `i` | 70:45 |
| 329 | `std` | 71:5 |
| 331 | `shared_ptr` | 71:10 |
| 333 | `HeifPixelImage` | 71:21 |
| 335 | `overlay_img` | 71:37 |
| 337 | `err` | 72:5 |
| 339 | `decode_image` | 72:11 |
| 341 | `image_references` | 72:24 |
| 343 | `i` | 72:41 |
| 346 | `overlay_img` | 72:45 |
| 349 | `if` | 73:5 |
| 351 | `err` | 73:9 |
| 353 | `Error` | 73:16 |
| 355 | `Ok` | 73:23 |
| 358 | `return` | 74:7 |
| 359 | `err` | 74:14 |
| 362 | `overlay_img` | 77:5 |
| 364 | `overlay_img` | 77:19 |
| 366 | `convert_colorspace` | 77:32 |
| 368 | `heif_colorspace_RGB` | 77:51 |
| 370 | `heif_chroma_444` | 77:72 |
| 373 | `if` | 78:5 |
| 376 | `overlay_img` | 78:10 |
| 379 | `return` | 79:7 |
| 380 | `Error` | 79:14 |
| 382 | `heif_error_Unsupported_feature` | 79:20 |
| 384 | `heif_suberror_Unsupported_color_conversion` | 79:52 |
| 388 | `int32_t` | 82:5 |
| 389 | `dx` | 82:13 |
| 391 | `dy` | 82:16 |
| 393 | `overlay` | 83:5 |
| 395 | `get_offset` | 83:13 |
| 397 | `i` | 83:24 |
| 400 | `dx` | 83:28 |
| 403 | `dy` | 83:32 |
| 406 | `err` | 85:5 |
| 408 | `img` | 85:11 |
| 410 | `overlay` | 85:16 |
| 412 | `overlay_img` | 85:24 |
| 414 | `dx` | 85:37 |
| 416 | `dy` | 85:40 |
| 419 | `if` | 86:5 |
| 421 | `err` | 86:9 |
| 424 | `if` | 87:7 |
| 426 | `err` | 87:11 |
| 428 | `error_code` | 87:15 |
| 430 | `heif_error_Invalid_input` | 87:29 |
| 432 | `err` | 88:11 |
| 434 | `sub_error_code` | 88:15 |
| 436 | `heif_suberror_Overlay_image_outside_of_canvas` | 88:33 |
| 439 | `err` | 91:9 |
| 441 | `Error` | 91:15 |
| 443 | `Ok` | 91:22 |
| 446 | `else` | 93:7 |
| 448 | `return` | 94:9 |
| 449 | `err` | 94:16 |
| 454 | `return` | 99:3 |
| 455 | `err` | 99:10 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'Error'` |
| 2 | `'He'` |
| 3 | `'if'` |
| 4 | `'Context'` |
| 5 | `'::'` |
| 6 | `'dec'` |
| 7 | `'ode'` |
| 8 | `'_'` |
| 9 | `'over'` |
| 10 | `'lay'` |
| 11 | `'_'` |
| 12 | `'image'` |
| 13 | `'('` |
| 14 | `'he'` |
| 15 | `'if'` |
| 16 | `'_'` |
| 17 | `'item'` |
| 18 | `'_'` |
| 19 | `'id'` |
| 20 | `'ID'` |
| 21 | `','` |
| 22 | `'\n'` |
| 62 | `'std'` |
| 63 | `'::'` |
| 64 | `'shared'` |
| 65 | `'_'` |
| 66 | `'ptr'` |
| 67 | `'<'` |
| 68 | `'He'` |
| 69 | `'if'` |
| 70 | `'Pixel'` |
| 71 | `'Image'` |
| 72 | `'>'` |
| 73 | `'&'` |
| 74 | `'img'` |
| 75 | `','` |
| 76 | `'\n'` |
| 116 | `'const'` |
| 117 | `'std'` |
| 118 | `'::'` |
| 119 | `'vector'` |
| 120 | `'<'` |
| 121 | `'uint'` |
| 122 | `'8'` |
| 123 | `'_'` |
| 124 | `'t'` |
| 125 | `'>'` |
| 126 | `'&'` |
| 127 | `'overlay'` |
| 128 | `'_'` |
| 129 | `'data'` |
| 130 | `')'` |
| 131 | `'const'` |
| 132 | `'\n'` |
| 133 | `'{'` |
| 134 | `'\n'` |
| 136 | `'//'` |
| 137 | `'find'` |
| 138 | `'the'` |
| 139 | `'IDs'` |
| 140 | `'this'` |
| 141 | `'image'` |
| 142 | `'is'` |
| 143 | `'composed'` |
| 144 | `'of'` |
| 145 | `'\n\n'` |
| 147 | `'auto'` |
| 148 | `'ire'` |
| 149 | `'f'` |
| 150 | `'_'` |
| 151 | `'box'` |
| 152 | `'='` |
| 153 | `'m'` |
| 154 | `'_'` |
| 155 | `'he'` |
| 156 | `'if'` |
| 157 | `'_'` |
| 158 | `'file'` |
| 159 | `'->'` |
| 160 | `'get'` |
| 161 | `'_'` |
| 162 | `'ire'` |
| 163 | `'f'` |
| 164 | `'_'` |
| 165 | `'box'` |
| 166 | `'();'` |
| 167 | `'\n\n'` |
| 169 | `'if'` |
| 170 | `'(!'` |
| 171 | `'ire'` |
| 172 | `'f'` |
| 173 | `'_'` |
| 174 | `'box'` |
| 175 | `')'` |
| 176 | `'{'` |
| 177 | `'\n'` |
| 181 | `'return'` |
| 182 | `'Error'` |
| 183 | `'('` |
| 184 | `'he'` |
| 185 | `'if'` |
| 186 | `'_'` |
| 187 | `'error'` |
| 188 | `'_'` |
| 189 | `'Invalid'` |
| 190 | `'_'` |
| 191 | `'input'` |
| 192 | `','` |
| 193 | `'\n'` |
| 210 | `'he'` |
| 211 | `'if'` |
| 212 | `'_'` |
| 213 | `'su'` |
| 214 | `'ber'` |
| 215 | `'ror'` |
| 216 | `'_'` |
| 217 | `'No'` |
| 218 | `'_'` |
| 219 | `'ire'` |
| 220 | `'f'` |
| 221 | `'_'` |
| 222 | `'box'` |
| 223 | `','` |
| 224 | `'\n'` |
| 241 | `'"'` |
| 242 | `'No'` |
| 243 | `'ire'` |
| 244 | `'f'` |
| 245 | `'box'` |
| 246 | `'available'` |
| 247 | `','` |
| 248 | `'but'` |
| 249 | `'needed'` |
| 250 | `'for'` |
| 251 | `'i'` |
| 252 | `'ov'` |
| 253 | `'l'` |
| 254 | `'image'` |
| 255 | `'");'` |
| 256 | `'\n'` |
| 258 | `'}'` |
| 259 | `'\n\n'` |
| 261 | `'std'` |
| 262 | `'::'` |
| 263 | `'vector'` |
| 264 | `'<'` |
| 265 | `'he'` |
| 266 | `'if'` |
| 267 | `'_'` |
| 268 | `'item'` |
| 269 | `'_'` |
| 270 | `'id'` |
| 271 | `'>'` |
| 272 | `'image'` |
| 273 | `'_'` |
| 274 | `'ref'` |
| 275 | `'erences'` |
| 276 | `'='` |
| 277 | `'ire'` |
| 278 | `'f'` |
| 279 | `'_'` |
| 280 | `'box'` |
| 281 | `'->'` |
| 282 | `'get'` |
| 283 | `'_'` |
| 284 | `'ref'` |
| 285 | `'erences'` |
| 286 | `'('` |
| 287 | `'ID'` |
| 288 | `','` |
| 289 | `'four'` |
| 290 | `'cc'` |
| 291 | `'("'` |
| 292 | `'d'` |
| 293 | `'img'` |
| 294 | `'")'` |
| 295 | `');'` |
| 296 | `'\n\n'` |
| 298 | `'/*'` |
| 299 | `'TOD'` |
| 300 | `'O'` |
| 301 | `':'` |
| 302 | `'probably'` |
| 303 | `','` |
| 304 | `'it'` |
| 305 | `'is'` |
| 306 | `'valid'` |
| 307 | `'that'` |
| 308 | `'an'` |
| 309 | `'i'` |
| 310 | `'ov'` |
| 311 | `'l'` |
| 312 | `'image'` |
| 313 | `'has'` |
| 314 | `'no'` |
| 315 | `'references'` |
| 316 | `'?'` |
| 317 | `'\n\n'` |
| 319 | `'if'` |
| 320 | `'('` |
| 321 | `'image'` |
| 322 | `'_'` |
| 323 | `'ref'` |
| 324 | `'erences'` |
| 325 | `'.'` |
| 326 | `'empty'` |
| 327 | `'())'` |
| 328 | `'{'` |
| 329 | `'\n'` |
| 333 | `'return'` |
| 334 | `'Error'` |
| 335 | `'('` |
| 336 | `'he'` |
| 337 | `'if'` |
| 338 | `'_'` |
| 339 | `'error'` |
| 340 | `'_'` |
| 341 | `'Invalid'` |
| 342 | `'_'` |
| 343 | `'input'` |
| 344 | `','` |
| 345 | `'\n'` |
| 362 | `'he'` |
| 363 | `'if'` |
| 364 | `'_'` |
| 365 | `'su'` |
| 366 | `'ber'` |
| 367 | `'ror'` |
| 368 | `'_'` |
| 369 | `'Missing'` |
| 370 | `'_'` |
| 371 | `'grid'` |
| 372 | `'_'` |
| 373 | `'images'` |
| 374 | `','` |
| 375 | `'\n'` |
| 392 | `'"\''` |
| 393 | `'iov'` |
| 394 | `'l'` |
| 395 | `"'"` |
| 396 | `'image'` |
| 397 | `'with'` |
| 398 | `'more'` |
| 399 | `'than'` |
| 400 | `'one'` |
| 401 | `'reference'` |
| 402 | `'image'` |
| 403 | `'");'` |
| 404 | `'\n'` |
| 406 | `'}'` |
| 407 | `'\n'` |
| 409 | `'*/'` |
| 410 | `'\n\n'` |
| 411 | `'\n'` |
| 413 | `'Image'` |
| 414 | `'Over'` |
| 415 | `'lay'` |
| 416 | `'overlay'` |
| 417 | `';'` |
| 418 | `'\n'` |
| 420 | `'Error'` |
| 421 | `'err'` |
| 422 | `'='` |
| 423 | `'overlay'` |
| 424 | `'.'` |
| 425 | `'parse'` |
| 426 | `'('` |
| 427 | `'image'` |
| 428 | `'_'` |
| 429 | `'ref'` |
| 430 | `'erences'` |
| 431 | `'.'` |
| 432 | `'size'` |
| 433 | `'(),'` |
| 434 | `'overlay'` |
| 435 | `'_'` |
| 436 | `'data'` |
| 437 | `');'` |
| 438 | `'\n'` |
| 440 | `'if'` |
| 441 | `'('` |
| 442 | `'err'` |
| 443 | `')'` |
| 444 | `'{'` |
| 445 | `'\n'` |
| 449 | `'return'` |
| 450 | `'err'` |
| 451 | `';'` |
| 452 | `'\n'` |
| 454 | `'}'` |
| 455 | `'\n\n'` |
| 457 | `'if'` |
| 458 | `'('` |
| 459 | `'image'` |
| 460 | `'_'` |
| 461 | `'ref'` |
| 462 | `'erences'` |
| 463 | `'.'` |
| 464 | `'size'` |
| 465 | `'()'` |
| 466 | `'!='` |
| 467 | `'overlay'` |
| 468 | `'.'` |
| 469 | `'get'` |
| 470 | `'_'` |
| 471 | `'num'` |
| 472 | `'_'` |
| 473 | `'offs'` |
| 474 | `'ets'` |
| 475 | `'())'` |
| 476 | `'{'` |
| 477 | `'\n'` |
| 481 | `'return'` |
| 482 | `'Error'` |
| 483 | `'('` |
| 484 | `'he'` |
| 485 | `'if'` |
| 486 | `'_'` |
| 487 | `'error'` |
| 488 | `'_'` |
| 489 | `'Invalid'` |
| 490 | `'_'` |
| 491 | `'input'` |
| 492 | `','` |
| 493 | `'\n'` |
| 510 | `'he'` |
