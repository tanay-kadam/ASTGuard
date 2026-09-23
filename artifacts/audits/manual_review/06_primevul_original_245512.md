# Review 06: `primevul:original:245512` (c)

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
   1 | static int mov_write_audio_tag(AVFormatContext *s, AVIOContext *pb, MOVMuxContext *mov, MOVTrack *track)
   2 | {
   3 |     int64_t pos = avio_tell(pb);
   4 |     int version = 0;
   5 |     uint32_t tag = track->tag;
   6 | 
   7 |     if (track->mode == MODE_MOV) {
   8 |         if (track->timescale > UINT16_MAX || !track->par->channels) {
   9 |             if (mov_get_lpcm_flags(track->par->codec_id))
  10 |                 tag = AV_RL32("lpcm");
  11 |             version = 2;
  12 |         } else if (track->audio_vbr || mov_pcm_le_gt16(track->par->codec_id) ||
  13 |                    mov_pcm_be_gt16(track->par->codec_id) ||
  14 |                    track->par->codec_id == AV_CODEC_ID_ADPCM_MS ||
  15 |                    track->par->codec_id == AV_CODEC_ID_ADPCM_IMA_WAV ||
  16 |                    track->par->codec_id == AV_CODEC_ID_QDM2) {
  17 |             version = 1;
  18 |         }
  19 |     }
  20 | 
  21 |     avio_wb32(pb, 0); /* size */
  22 |     if (mov->encryption_scheme != MOV_ENC_NONE) {
  23 |         ffio_wfourcc(pb, "enca");
  24 |     } else {
  25 |         avio_wl32(pb, tag); // store it byteswapped
  26 |     }
  27 |     avio_wb32(pb, 0); /* Reserved */
  28 |     avio_wb16(pb, 0); /* Reserved */
  29 |     avio_wb16(pb, 1); /* Data-reference index, XXX  == 1 */
  30 | 
  31 |     /* SoundDescription */
  32 |     avio_wb16(pb, version); /* Version */
  33 |     avio_wb16(pb, 0); /* Revision level */
  34 |     avio_wb32(pb, 0); /* Reserved */
  35 | 
  36 |     if (version == 2) {
  37 |         avio_wb16(pb, 3);
  38 |         avio_wb16(pb, 16);
  39 |         avio_wb16(pb, 0xfffe);
  40 |         avio_wb16(pb, 0);
  41 |         avio_wb32(pb, 0x00010000);
  42 |         avio_wb32(pb, 72);
  43 |         avio_wb64(pb, av_double2int(track->par->sample_rate));
  44 |         avio_wb32(pb, track->par->channels);
  45 |         avio_wb32(pb, 0x7F000000);
  46 |         avio_wb32(pb, av_get_bits_per_sample(track->par->codec_id));
  47 |         avio_wb32(pb, mov_get_lpcm_flags(track->par->codec_id));
  48 |         avio_wb32(pb, track->sample_size);
  49 |         avio_wb32(pb, get_samples_per_packet(track));
  50 |     } else {
  51 |         if (track->mode == MODE_MOV) {
  52 |             avio_wb16(pb, track->par->channels);
  53 |             if (track->par->codec_id == AV_CODEC_ID_PCM_U8 ||
  54 |                 track->par->codec_id == AV_CODEC_ID_PCM_S8)
  55 |                 avio_wb16(pb, 8); /* bits per sample */
  56 |             else if (track->par->codec_id == AV_CODEC_ID_ADPCM_G726)
  57 |                 avio_wb16(pb, track->par->bits_per_coded_sample);
  58 |             else
  59 |                 avio_wb16(pb, 16);
  60 |             avio_wb16(pb, track->audio_vbr ? -2 : 0); /* compression ID */
  61 |         } else { /* reserved for mp4/3gp */
  62 |             avio_wb16(pb, 2);
  63 |             avio_wb16(pb, 16);
  64 |             avio_wb16(pb, 0);
  65 |         }
  66 | 
  67 |         avio_wb16(pb, 0); /* packet size (= 0) */
  68 |         avio_wb16(pb, track->par->sample_rate <= UINT16_MAX ?
  69 |                       track->par->sample_rate : 0);
  70 |         avio_wb16(pb, 0); /* Reserved */
  71 |     }
  72 | 
  73 |     if (version == 1) { /* SoundDescription V1 extended info */
  74 |         if (mov_pcm_le_gt16(track->par->codec_id) ||
  75 |             mov_pcm_be_gt16(track->par->codec_id))
  76 |             avio_wb32(pb, 1); /*  must be 1 for  uncompressed formats */
  77 |         else
  78 |             avio_wb32(pb, track->par->frame_size); /* Samples per packet */
  79 |         avio_wb32(pb, track->sample_size / track->par->channels); /* Bytes per packet */
  80 |         avio_wb32(pb, track->sample_size); /* Bytes per frame */
  81 |         avio_wb32(pb, 2); /* Bytes per sample */
  82 |     }
  83 | 
  84 |     if (track->mode == MODE_MOV &&
  85 |         (track->par->codec_id == AV_CODEC_ID_AAC           ||
  86 |          track->par->codec_id == AV_CODEC_ID_AC3           ||
  87 |          track->par->codec_id == AV_CODEC_ID_EAC3          ||
  88 |          track->par->codec_id == AV_CODEC_ID_AMR_NB        ||
  89 |          track->par->codec_id == AV_CODEC_ID_ALAC          ||
  90 |          track->par->codec_id == AV_CODEC_ID_ADPCM_MS      ||
  91 |          track->par->codec_id == AV_CODEC_ID_ADPCM_IMA_WAV ||
  92 |          track->par->codec_id == AV_CODEC_ID_QDM2          ||
  93 |          (mov_pcm_le_gt16(track->par->codec_id) && version==1) ||
  94 |          (mov_pcm_be_gt16(track->par->codec_id) && version==1)))
  95 |         mov_write_wave_tag(s, pb, track);
  96 |     else if (track->tag == MKTAG('m','p','4','a'))
  97 |         mov_write_esds_tag(pb, track);
  98 |     else if (track->par->codec_id == AV_CODEC_ID_AMR_NB)
  99 |         mov_write_amr_tag(pb, track);
 100 |     else if (track->par->codec_id == AV_CODEC_ID_AC3)
 101 |         mov_write_ac3_tag(pb, track);
 102 |     else if (track->par->codec_id == AV_CODEC_ID_EAC3)
 103 |         mov_write_eac3_tag(pb, track);
 104 |     else if (track->par->codec_id == AV_CODEC_ID_ALAC)
 105 |         mov_write_extradata_tag(pb, track);
 106 |     else if (track->par->codec_id == AV_CODEC_ID_WMAPRO)
 107 |         mov_write_wfex_tag(s, pb, track);
 108 |     else if (track->vos_len > 0)
 109 |         mov_write_glbl_tag(pb, track);
 110 | 
 111 |     if (track->mode == MODE_MOV && track->par->codec_type == AVMEDIA_TYPE_AUDIO)
 112 |         mov_write_chan_tag(s, pb, track);
 113 | 
 114 |     if (mov->encryption_scheme != MOV_ENC_NONE) {
 115 |         ff_mov_cenc_write_sinf_tag(track, pb, mov->encryption_kid);
 116 |     }
 117 | 
 118 |     return update_size(pb, pos);
 119 | }
```

## Identifier tokens

| id | text | line:col |
|---|---|---|
| 0 | `static` | 1:1 |
| 1 | `int` | 1:8 |
| 2 | `mov_write_audio_tag` | 1:12 |
| 4 | `AVFormatContext` | 1:32 |
| 6 | `s` | 1:49 |
| 8 | `AVIOContext` | 1:52 |
| 10 | `pb` | 1:65 |
| 12 | `MOVMuxContext` | 1:69 |
| 14 | `mov` | 1:84 |
| 16 | `MOVTrack` | 1:89 |
| 18 | `track` | 1:99 |
| 21 | `int64_t` | 3:5 |
| 22 | `pos` | 3:13 |
| 24 | `avio_tell` | 3:19 |
| 26 | `pb` | 3:29 |
| 29 | `int` | 4:5 |
| 30 | `version` | 4:9 |
| 34 | `uint32_t` | 5:5 |
| 35 | `tag` | 5:14 |
| 37 | `track` | 5:20 |
| 39 | `tag` | 5:27 |
| 41 | `if` | 7:5 |
| 43 | `track` | 7:9 |
| 45 | `mode` | 7:16 |
| 47 | `MODE_MOV` | 7:24 |
| 50 | `if` | 8:9 |
| 52 | `track` | 8:13 |
| 54 | `timescale` | 8:20 |
| 56 | `UINT16_MAX` | 8:32 |
| 59 | `track` | 8:47 |
| 61 | `par` | 8:54 |
| 63 | `channels` | 8:59 |
| 66 | `if` | 9:13 |
| 68 | `mov_get_lpcm_flags` | 9:17 |
| 70 | `track` | 9:36 |
| 72 | `par` | 9:43 |
| 74 | `codec_id` | 9:48 |
| 77 | `tag` | 10:17 |
| 79 | `AV_RL32` | 10:23 |
| 84 | `version` | 11:13 |
| 89 | `else` | 12:11 |
| 90 | `if` | 12:16 |
| 92 | `track` | 12:20 |
| 94 | `audio_vbr` | 12:27 |
| 96 | `mov_pcm_le_gt16` | 12:40 |
| 98 | `track` | 12:56 |
| 100 | `par` | 12:63 |
| 102 | `codec_id` | 12:68 |
| 105 | `mov_pcm_be_gt16` | 13:20 |
| 107 | `track` | 13:36 |
| 109 | `par` | 13:43 |
| 111 | `codec_id` | 13:48 |
| 114 | `track` | 14:20 |
| 116 | `par` | 14:27 |
| 118 | `codec_id` | 14:32 |
| 120 | `AV_CODEC_ID_ADPCM_MS` | 14:44 |
| 122 | `track` | 15:20 |
| 124 | `par` | 15:27 |
| 126 | `codec_id` | 15:32 |
| 128 | `AV_CODEC_ID_ADPCM_IMA_WAV` | 15:44 |
| 130 | `track` | 16:20 |
| 132 | `par` | 16:27 |
| 134 | `codec_id` | 16:32 |
| 136 | `AV_CODEC_ID_QDM2` | 16:44 |
| 139 | `version` | 17:13 |
| 145 | `avio_wb32` | 21:5 |
| 147 | `pb` | 21:15 |
| 152 | `if` | 22:5 |
| 154 | `mov` | 22:9 |
| 156 | `encryption_scheme` | 22:14 |
| 158 | `MOV_ENC_NONE` | 22:35 |
| 161 | `ffio_wfourcc` | 23:9 |
| 163 | `pb` | 23:22 |
| 169 | `else` | 24:7 |
| 171 | `avio_wl32` | 25:9 |
| 173 | `pb` | 25:19 |
| 175 | `tag` | 25:23 |
| 179 | `avio_wb32` | 27:5 |
| 181 | `pb` | 27:15 |
| 186 | `avio_wb16` | 28:5 |
| 188 | `pb` | 28:15 |
| 193 | `avio_wb16` | 29:5 |
| 195 | `pb` | 29:15 |
| 200 | `avio_wb16` | 32:5 |
| 202 | `pb` | 32:15 |
| 204 | `version` | 32:19 |
| 207 | `avio_wb16` | 33:5 |
| 209 | `pb` | 33:15 |
| 214 | `avio_wb32` | 34:5 |
| 216 | `pb` | 34:15 |
| 221 | `if` | 36:5 |
| 223 | `version` | 36:9 |
| 228 | `avio_wb16` | 37:9 |
| 230 | `pb` | 37:19 |
| 235 | `avio_wb16` | 38:9 |
| 237 | `pb` | 38:19 |
| 242 | `avio_wb16` | 39:9 |
| 244 | `pb` | 39:19 |
| 249 | `avio_wb16` | 40:9 |
| 251 | `pb` | 40:19 |
| 256 | `avio_wb32` | 41:9 |
| 258 | `pb` | 41:19 |
| 263 | `avio_wb32` | 42:9 |
| 265 | `pb` | 42:19 |
| 270 | `avio_wb64` | 43:9 |
| 272 | `pb` | 43:19 |
| 274 | `av_double2int` | 43:23 |
| 276 | `track` | 43:37 |
| 278 | `par` | 43:44 |
| 280 | `sample_rate` | 43:49 |
| 284 | `avio_wb32` | 44:9 |
| 286 | `pb` | 44:19 |
| 288 | `track` | 44:23 |
| 290 | `par` | 44:30 |
| 292 | `channels` | 44:35 |
| 295 | `avio_wb32` | 45:9 |
| 297 | `pb` | 45:19 |
| 302 | `avio_wb32` | 46:9 |
| 304 | `pb` | 46:19 |
| 306 | `av_get_bits_per_sample` | 46:23 |
| 308 | `track` | 46:46 |
| 310 | `par` | 46:53 |
| 312 | `codec_id` | 46:58 |
| 316 | `avio_wb32` | 47:9 |
| 318 | `pb` | 47:19 |
| 320 | `mov_get_lpcm_flags` | 47:23 |
| 322 | `track` | 47:42 |
| 324 | `par` | 47:49 |
| 326 | `codec_id` | 47:54 |
| 330 | `avio_wb32` | 48:9 |
| 332 | `pb` | 48:19 |
| 334 | `track` | 48:23 |
| 336 | `sample_size` | 48:30 |
| 339 | `avio_wb32` | 49:9 |
| 341 | `pb` | 49:19 |
| 343 | `get_samples_per_packet` | 49:23 |
| 345 | `track` | 49:46 |
| 350 | `else` | 50:7 |
| 352 | `if` | 51:9 |
| 354 | `track` | 51:13 |
| 356 | `mode` | 51:20 |
| 358 | `MODE_MOV` | 51:28 |
| 361 | `avio_wb16` | 52:13 |
| 363 | `pb` | 52:23 |
| 365 | `track` | 52:27 |
| 367 | `par` | 52:34 |
| 369 | `channels` | 52:39 |
| 372 | `if` | 53:13 |
| 374 | `track` | 53:17 |
| 376 | `par` | 53:24 |
| 378 | `codec_id` | 53:29 |
| 380 | `AV_CODEC_ID_PCM_U8` | 53:41 |
| 382 | `track` | 54:17 |
| 384 | `par` | 54:24 |
| 386 | `codec_id` | 54:29 |
| 388 | `AV_CODEC_ID_PCM_S8` | 54:41 |
| 390 | `avio_wb16` | 55:17 |
| 392 | `pb` | 55:27 |
| 397 | `else` | 56:13 |
| 398 | `if` | 56:18 |
| 400 | `track` | 56:22 |
| 402 | `par` | 56:29 |
| 404 | `codec_id` | 56:34 |
| 406 | `AV_CODEC_ID_ADPCM_G726` | 56:46 |
| 408 | `avio_wb16` | 57:17 |
| 410 | `pb` | 57:27 |
| 412 | `track` | 57:31 |
| 414 | `par` | 57:38 |
| 416 | `bits_per_coded_sample` | 57:43 |
| 419 | `else` | 58:13 |
| 420 | `avio_wb16` | 59:17 |
| 422 | `pb` | 59:27 |
| 427 | `avio_wb16` | 60:13 |
| 429 | `pb` | 60:23 |
| 431 | `track` | 60:27 |
| 433 | `audio_vbr` | 60:34 |
| 442 | `else` | 61:11 |
| 444 | `avio_wb16` | 62:13 |
| 446 | `pb` | 62:23 |
| 451 | `avio_wb16` | 63:13 |
| 453 | `pb` | 63:23 |
| 458 | `avio_wb16` | 64:13 |
| 460 | `pb` | 64:23 |
| 466 | `avio_wb16` | 67:9 |
| 468 | `pb` | 67:19 |
| 473 | `avio_wb16` | 68:9 |
| 475 | `pb` | 68:19 |
| 477 | `track` | 68:23 |
| 479 | `par` | 68:30 |
| 481 | `sample_rate` | 68:35 |
| 483 | `UINT16_MAX` | 68:50 |
| 485 | `track` | 69:23 |
| 487 | `par` | 69:30 |
| 489 | `sample_rate` | 69:35 |
| 494 | `avio_wb16` | 70:9 |
| 496 | `pb` | 70:19 |
| 502 | `if` | 73:5 |
| 504 | `version` | 73:9 |
| 509 | `if` | 74:9 |
| 511 | `mov_pcm_le_gt16` | 74:13 |
| 513 | `track` | 74:29 |
| 515 | `par` | 74:36 |
| 517 | `codec_id` | 74:41 |
| 520 | `mov_pcm_be_gt16` | 75:13 |
| 522 | `track` | 75:29 |
| 524 | `par` | 75:36 |
| 526 | `codec_id` | 75:41 |
| 529 | `avio_wb32` | 76:13 |
| 531 | `pb` | 76:23 |
| 536 | `else` | 77:9 |
| 537 | `avio_wb32` | 78:13 |
| 539 | `pb` | 78:23 |
| 541 | `track` | 78:27 |
| 543 | `par` | 78:34 |
| 545 | `frame_size` | 78:39 |
| 548 | `avio_wb32` | 79:9 |
| 550 | `pb` | 79:19 |
| 552 | `track` | 79:23 |
| 554 | `sample_size` | 79:30 |
| 556 | `track` | 79:44 |
| 558 | `par` | 79:51 |
| 560 | `channels` | 79:56 |
| 563 | `avio_wb32` | 80:9 |
| 565 | `pb` | 80:19 |
| 567 | `track` | 80:23 |
| 569 | `sample_size` | 80:30 |
| 572 | `avio_wb32` | 81:9 |
| 574 | `pb` | 81:19 |
| 580 | `if` | 84:5 |
| 582 | `track` | 84:9 |
| 584 | `mode` | 84:16 |
| 586 | `MODE_MOV` | 84:24 |
| 589 | `track` | 85:10 |
| 591 | `par` | 85:17 |
| 593 | `codec_id` | 85:22 |
| 595 | `AV_CODEC_ID_AAC` | 85:34 |
| 597 | `track` | 86:10 |
| 599 | `par` | 86:17 |
| 601 | `codec_id` | 86:22 |
| 603 | `AV_CODEC_ID_AC3` | 86:34 |
| 605 | `track` | 87:10 |
| 607 | `par` | 87:17 |
| 609 | `codec_id` | 87:22 |
| 611 | `AV_CODEC_ID_EAC3` | 87:34 |
| 613 | `track` | 88:10 |
| 615 | `par` | 88:17 |
| 617 | `codec_id` | 88:22 |
| 619 | `AV_CODEC_ID_AMR_NB` | 88:34 |
| 621 | `track` | 89:10 |
| 623 | `par` | 89:17 |
| 625 | `codec_id` | 89:22 |
| 627 | `AV_CODEC_ID_ALAC` | 89:34 |
| 629 | `track` | 90:10 |
| 631 | `par` | 90:17 |
| 633 | `codec_id` | 90:22 |
| 635 | `AV_CODEC_ID_ADPCM_MS` | 90:34 |
| 637 | `track` | 91:10 |
| 639 | `par` | 91:17 |
| 641 | `codec_id` | 91:22 |
| 643 | `AV_CODEC_ID_ADPCM_IMA_WAV` | 91:34 |
| 645 | `track` | 92:10 |
| 647 | `par` | 92:17 |
| 649 | `codec_id` | 92:22 |
| 651 | `AV_CODEC_ID_QDM2` | 92:34 |
| 654 | `mov_pcm_le_gt16` | 93:11 |
| 656 | `track` | 93:27 |
| 658 | `par` | 93:34 |
| 660 | `codec_id` | 93:39 |
| 663 | `version` | 93:52 |
| 669 | `mov_pcm_be_gt16` | 94:11 |
| 671 | `track` | 94:27 |
| 673 | `par` | 94:34 |
| 675 | `codec_id` | 94:39 |
| 678 | `version` | 94:52 |
| 684 | `mov_write_wave_tag` | 95:9 |
| 686 | `s` | 95:28 |
| 688 | `pb` | 95:31 |
| 690 | `track` | 95:35 |
| 693 | `else` | 96:5 |
| 694 | `if` | 96:10 |
| 696 | `track` | 96:14 |
| 698 | `tag` | 96:21 |
| 700 | `MKTAG` | 96:28 |
| 711 | `mov_write_esds_tag` | 97:9 |
| 713 | `pb` | 97:28 |
| 715 | `track` | 97:32 |
| 718 | `else` | 98:5 |
| 719 | `if` | 98:10 |
| 721 | `track` | 98:14 |
| 723 | `par` | 98:21 |
| 725 | `codec_id` | 98:26 |
| 727 | `AV_CODEC_ID_AMR_NB` | 98:38 |
| 729 | `mov_write_amr_tag` | 99:9 |
| 731 | `pb` | 99:27 |
| 733 | `track` | 99:31 |
| 736 | `else` | 100:5 |
| 737 | `if` | 100:10 |
| 739 | `track` | 100:14 |
| 741 | `par` | 100:21 |
| 743 | `codec_id` | 100:26 |
| 745 | `AV_CODEC_ID_AC3` | 100:38 |
| 747 | `mov_write_ac3_tag` | 101:9 |
| 749 | `pb` | 101:27 |
| 751 | `track` | 101:31 |
| 754 | `else` | 102:5 |
| 755 | `if` | 102:10 |
| 757 | `track` | 102:14 |
| 759 | `par` | 102:21 |
| 761 | `codec_id` | 102:26 |
| 763 | `AV_CODEC_ID_EAC3` | 102:38 |
| 765 | `mov_write_eac3_tag` | 103:9 |
| 767 | `pb` | 103:28 |
| 769 | `track` | 103:32 |
| 772 | `else` | 104:5 |
| 773 | `if` | 104:10 |
| 775 | `track` | 104:14 |
| 777 | `par` | 104:21 |
| 779 | `codec_id` | 104:26 |
| 781 | `AV_CODEC_ID_ALAC` | 104:38 |
| 783 | `mov_write_extradata_tag` | 105:9 |
| 785 | `pb` | 105:33 |
| 787 | `track` | 105:37 |
| 790 | `else` | 106:5 |
| 791 | `if` | 106:10 |
| 793 | `track` | 106:14 |
| 795 | `par` | 106:21 |
| 797 | `codec_id` | 106:26 |
| 799 | `AV_CODEC_ID_WMAPRO` | 106:38 |
| 801 | `mov_write_wfex_tag` | 107:9 |
| 803 | `s` | 107:28 |
| 805 | `pb` | 107:31 |
| 807 | `track` | 107:35 |
| 810 | `else` | 108:5 |
| 811 | `if` | 108:10 |
| 813 | `track` | 108:14 |
| 815 | `vos_len` | 108:21 |
| 819 | `mov_write_glbl_tag` | 109:9 |
| 821 | `pb` | 109:28 |
| 823 | `track` | 109:32 |
| 826 | `if` | 111:5 |
| 828 | `track` | 111:9 |
| 830 | `mode` | 111:16 |
| 832 | `MODE_MOV` | 111:24 |
| 834 | `track` | 111:36 |
| 836 | `par` | 111:43 |
| 838 | `codec_type` | 111:48 |
| 840 | `AVMEDIA_TYPE_AUDIO` | 111:62 |
| 842 | `mov_write_chan_tag` | 112:9 |
| 844 | `s` | 112:28 |
| 846 | `pb` | 112:31 |
| 848 | `track` | 112:35 |
| 851 | `if` | 114:5 |
| 853 | `mov` | 114:9 |
| 855 | `encryption_scheme` | 114:14 |
| 857 | `MOV_ENC_NONE` | 114:35 |
| 860 | `ff_mov_cenc_write_sinf_tag` | 115:9 |
| 862 | `track` | 115:36 |
| 864 | `pb` | 115:43 |
| 866 | `mov` | 115:47 |
| 868 | `encryption_kid` | 115:52 |
| 872 | `return` | 118:5 |
| 873 | `update_size` | 118:12 |
| 875 | `pb` | 118:24 |
| 877 | `pos` | 118:28 |

## BPE span check

Set `span_alignment_ok` to false if any piece below does not show the source text it should cover.

| bpe index | source bytes |
|---|---|
| 1 | `'static'` |
| 2 | `'int'` |
| 3 | `'mov'` |
| 4 | `'_'` |
| 5 | `'write'` |
| 6 | `'_'` |
| 7 | `'audio'` |
| 8 | `'_'` |
| 9 | `'tag'` |
| 10 | `'('` |
| 11 | `'AV'` |
| 12 | `'Format'` |
| 13 | `'Context'` |
| 14 | `'*'` |
| 15 | `'s'` |
| 16 | `','` |
| 17 | `'AV'` |
| 18 | `'IO'` |
| 19 | `'Context'` |
| 20 | `'*'` |
| 21 | `'pb'` |
| 22 | `','` |
| 23 | `'MOV'` |
| 24 | `'M'` |
| 25 | `'ux'` |
| 26 | `'Context'` |
| 27 | `'*'` |
| 28 | `'m'` |
| 29 | `'ov'` |
| 30 | `','` |
| 31 | `'MOV'` |
| 32 | `'Track'` |
| 33 | `'*'` |
| 34 | `'track'` |
| 35 | `')'` |
| 36 | `'\n'` |
| 37 | `'{'` |
| 38 | `'\n'` |
| 42 | `'int'` |
| 43 | `'64'` |
| 44 | `'_'` |
| 45 | `'t'` |
| 46 | `'pos'` |
| 47 | `'='` |
| 48 | `'av'` |
| 49 | `'io'` |
| 50 | `'_'` |
| 51 | `'tell'` |
| 52 | `'('` |
| 53 | `'pb'` |
| 54 | `');'` |
| 55 | `'\n'` |
| 59 | `'int'` |
| 60 | `'version'` |
| 61 | `'='` |
| 62 | `'0'` |
| 63 | `';'` |
| 64 | `'\n'` |
| 68 | `'uint'` |
| 69 | `'32'` |
| 70 | `'_'` |
| 71 | `'t'` |
| 72 | `'tag'` |
| 73 | `'='` |
| 74 | `'track'` |
| 75 | `'->'` |
| 76 | `'tag'` |
| 77 | `';'` |
| 78 | `'\n\n'` |
| 82 | `'if'` |
| 83 | `'('` |
| 84 | `'track'` |
| 85 | `'->'` |
| 86 | `'mode'` |
| 87 | `'=='` |
| 88 | `'M'` |
| 89 | `'ODE'` |
| 90 | `'_'` |
| 91 | `'M'` |
| 92 | `'OV'` |
| 93 | `')'` |
| 94 | `'{'` |
| 95 | `'\n'` |
| 103 | `'if'` |
| 104 | `'('` |
| 105 | `'track'` |
| 106 | `'->'` |
| 107 | `'times'` |
| 108 | `'cale'` |
| 109 | `'>'` |
| 110 | `'U'` |
| 111 | `'INT'` |
| 112 | `'16'` |
| 113 | `'_'` |
| 114 | `'MAX'` |
| 115 | `'||'` |
| 116 | `'!'` |
| 117 | `'track'` |
| 118 | `'->'` |
| 119 | `'par'` |
| 120 | `'->'` |
| 121 | `'ch'` |
| 122 | `'annels'` |
| 123 | `')'` |
| 124 | `'{'` |
| 125 | `'\n'` |
| 137 | `'if'` |
| 138 | `'('` |
| 139 | `'m'` |
| 140 | `'ov'` |
| 141 | `'_'` |
| 142 | `'get'` |
| 143 | `'_'` |
| 144 | `'lp'` |
| 145 | `'cm'` |
| 146 | `'_'` |
| 147 | `'flags'` |
| 148 | `'('` |
| 149 | `'track'` |
| 150 | `'->'` |
| 151 | `'par'` |
| 152 | `'->'` |
| 153 | `'cod'` |
| 154 | `'ec'` |
| 155 | `'_'` |
| 156 | `'id'` |
| 157 | `'))'` |
| 158 | `'\n'` |
| 174 | `'tag'` |
| 175 | `'='` |
| 176 | `'AV'` |
| 177 | `'_'` |
| 178 | `'RL'` |
| 179 | `'32'` |
| 180 | `'("'` |
| 181 | `'lp'` |
| 182 | `'cm'` |
| 183 | `'");'` |
| 184 | `'\n'` |
| 196 | `'version'` |
| 197 | `'='` |
| 198 | `'2'` |
| 199 | `';'` |
| 200 | `'\n'` |
| 208 | `'}'` |
| 209 | `'else'` |
| 210 | `'if'` |
| 211 | `'('` |
| 212 | `'track'` |
| 213 | `'->'` |
| 214 | `'audio'` |
| 215 | `'_'` |
| 216 | `'v'` |
| 217 | `'br'` |
| 218 | `'||'` |
| 219 | `'mov'` |
| 220 | `'_'` |
| 221 | `'p'` |
| 222 | `'cm'` |
| 223 | `'_'` |
| 224 | `'le'` |
| 225 | `'_'` |
| 226 | `'gt'` |
| 227 | `'16'` |
| 228 | `'('` |
| 229 | `'track'` |
| 230 | `'->'` |
| 231 | `'par'` |
| 232 | `'->'` |
| 233 | `'cod'` |
| 234 | `'ec'` |
| 235 | `'_'` |
| 236 | `'id'` |
| 237 | `')'` |
| 238 | `'||'` |
| 239 | `'\n'` |
| 258 | `'mov'` |
| 259 | `'_'` |
| 260 | `'p'` |
| 261 | `'cm'` |
| 262 | `'_'` |
| 263 | `'be'` |
| 264 | `'_'` |
| 265 | `'gt'` |
| 266 | `'16'` |
| 267 | `'('` |
| 268 | `'track'` |
| 269 | `'->'` |
| 270 | `'par'` |
| 271 | `'->'` |
| 272 | `'cod'` |
| 273 | `'ec'` |
| 274 | `'_'` |
| 275 | `'id'` |
| 276 | `')'` |
| 277 | `'||'` |
| 278 | `'\n'` |
| 297 | `'track'` |
| 298 | `'->'` |
| 299 | `'par'` |
| 300 | `'->'` |
| 301 | `'cod'` |
| 302 | `'ec'` |
| 303 | `'_'` |
| 304 | `'id'` |
| 305 | `'=='` |
| 306 | `'AV'` |
| 307 | `'_'` |
| 308 | `'C'` |
| 309 | `'OD'` |
| 310 | `'EC'` |
| 311 | `'_'` |
| 312 | `'ID'` |
| 313 | `'_'` |
| 314 | `'AD'` |
| 315 | `'PC'` |
| 316 | `'M'` |
| 317 | `'_'` |
| 318 | `'MS'` |
| 319 | `'||'` |
| 320 | `'\n'` |
| 339 | `'track'` |
| 340 | `'->'` |
| 341 | `'par'` |
| 342 | `'->'` |
| 343 | `'cod'` |
| 344 | `'ec'` |
| 345 | `'_'` |
| 346 | `'id'` |
| 347 | `'=='` |
| 348 | `'AV'` |
| 349 | `'_'` |
| 350 | `'C'` |
| 351 | `'OD'` |
| 352 | `'EC'` |
| 353 | `'_'` |
| 354 | `'ID'` |
| 355 | `'_'` |
| 356 | `'AD'` |
| 357 | `'PC'` |
| 358 | `'M'` |
| 359 | `'_'` |
| 360 | `'IM'` |
| 361 | `'A'` |
| 362 | `'_'` |
| 363 | `'W'` |
| 364 | `'AV'` |
| 365 | `'||'` |
| 366 | `'\n'` |
| 385 | `'track'` |
| 386 | `'->'` |
| 387 | `'par'` |
| 388 | `'->'` |
| 389 | `'cod'` |
| 390 | `'ec'` |
| 391 | `'_'` |
| 392 | `'id'` |
| 393 | `'=='` |
| 394 | `'AV'` |
| 395 | `'_'` |
| 396 | `'C'` |
| 397 | `'OD'` |
| 398 | `'EC'` |
| 399 | `'_'` |
| 400 | `'ID'` |
| 401 | `'_'` |
| 402 | `'Q'` |
| 403 | `'DM'` |
| 404 | `'2'` |
| 405 | `')'` |
| 406 | `'{'` |
| 407 | `'\n'` |
| 419 | `'version'` |
| 420 | `'='` |
| 421 | `'1'` |
| 422 | `';'` |
| 423 | `'\n'` |
| 431 | `'}'` |
| 432 | `'\n'` |
| 436 | `'}'` |
| 437 | `'\n\n'` |
| 441 | `'av'` |
| 442 | `'io'` |
| 443 | `'_'` |
| 444 | `'wb'` |
| 445 | `'32'` |
| 446 | `'('` |
| 447 | `'pb'` |
| 448 | `','` |
| 449 | `'0'` |
| 450 | `');'` |
| 451 | `'/*'` |
| 452 | `'size'` |
| 453 | `'*/'` |
| 454 | `'\n'` |
| 458 | `'if'` |
| 459 | `'('` |
| 460 | `'m'` |
| 461 | `'ov'` |
| 462 | `'->'` |
| 463 | `'enc'` |
| 464 | `'ryption'` |
| 465 | `'_'` |
| 466 | `'sche'` |
| 467 | `'me'` |
| 468 | `'!='` |
| 469 | `'MOV'` |
| 470 | `'_'` |
| 471 | `'ENC'` |
| 472 | `'_'` |
| 473 | `'N'` |
| 474 | `'ONE'` |
| 475 | `')'` |
| 476 | `'{'` |
| 477 | `'\n'` |
| 485 | `'ff'` |
| 486 | `'io'` |
| 487 | `'_'` |
| 488 | `'w'` |
| 489 | `'four'` |
| 490 | `'cc'` |
| 491 | `'('` |
| 492 | `'pb'` |
| 493 | `','` |
| 494 | `'"'` |
| 495 | `'en'` |
| 496 | `'ca'` |
| 497 | `'");'` |
| 498 | `'\n'` |
| 502 | `'}'` |
| 503 | `'else'` |
| 504 | `'{'` |
| 505 | `'\n'` |
