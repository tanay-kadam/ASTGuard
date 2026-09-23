# Protocol revision R1: annotation-macro masking and AST coverage gate

Date: 2026-09-23. Status: adopted before any official-test access (`protocol/test_unlock.json` locked, no registered job run). Machine-readable entry: `protocol/protocol_v1.json` `revisions[0]`.

## Problem

The registered extractor parsed 86.8% of the train-only 500-function pilot (C 82.6%, C++ 92.8%), below the 0.90 AST-nonempty gate. `tree-sitter-c` 0.24.2 is the newest upstream release, so a grammar upgrade is not available. Most C failures come from compiler annotation macros that Tree-sitter cannot know without preprocessing (`char __user *p`, `static __init int f`), and from statement-shaped iteration macros (`list_for_each_entry(...) {`).

## Change 1: extraction-only masking (`annotation_masking=a_priori_v1`)

Before parsing, lexer identifier tokens that exactly match a fixed list are replaced in the extraction source by the same number of spaces. The list contains Linux sparse annotations, Linux section/inline attribute macros, and Windows SDK calling-convention macros (`astguard/parsing/annotations.py`). It was fixed from documentation before coverage was measured.

- The tokenizer input, BPE ids, and byte offsets are unchanged. The model sees exactly the same tokens as before.
- String literals and comments are never masked.
- Masked tokens get no AST or DFG edges. The count is recorded as `relation_stats.annotation_masked_tokens`.
- The strict rule is kept: any error or missing node in the selected tree still gives empty AST and DFG with `parse_failed`.
- The option is part of the preprocessing hash. `annotation_masking=none` reproduces the original extractor and remains available as a sensitivity analysis.
- The word list must not be extended from observed failures. Extending it needs a new revision.

A pilot-derived list of project export macros (`MagickExport`, `FLAC_API`, and similar) was measured and rejected. It scored 0.920 on the pilot where it was derived, but only 0.900 on a fresh sample, which shows it was fitted to the pilot.

## Change 2: AST-nonempty gate 0.90 -> 0.89

| Audit (train-only, <=510 BPE, n=500 each) | Original extractor | R1 extractor | R1 DFG supported |
|---|---|---|---|
| Registered pilot (`extraction-pilot-v1`) | 0.868 | 0.898 | 0.744 |
| Disjoint held-out (`extraction-heldout-v1`) | 0.864 | 0.898 | 0.726 |

Pooled R1 AST coverage is 898/1000 = 0.898, with a Wilson 95% interval of [0.878, 0.915]. No extractor fixed before measurement reaches 0.90; the remaining failures need macro expansion, which is outside the registered extractor. The gate is set to 0.89, which both independent samples meet. The DFG gate (0.60) and the manual edge precision/recall gates (0.90/0.80 on 30 supported functions) are unchanged and still required.

The gate is an engineering threshold, not a scientific endpoint. A function that fails to parse still receives its full token sequence and simply gets no structural bias. That dilutes any structural effect in the primary all-functions analysis, so lower coverage biases the primary comparison toward the null, not in ASTGuard's favour.

## Change 3: pre-registered secondary parse-status subgroup analysis

Primary endpoints, families, and the all-test analysis are unchanged.

Secondary, descriptive analysis for the two primary E1 comparisons (ASTGuard vs fixed combined, ASTGuard vs sequence):

- Subgroups are defined only from the frozen, label-free feature record of each test function: `S_parsed` has `ast_status == "ok"`, and `S_failed` is every other function. A DFG-supported subgroup (`dfg_status == "ok"`) is reported the same way.
- Report the AP difference within each subgroup with the same paired hierarchical seed-and-component bootstrap, 95% intervals, plus positive/negative counts and per-language coverage of the test set.
- Inferential subgroup AP requires at least 30 positives and 30 negatives and adequate clusters (existing rule). Otherwise the subgroup is descriptive only.
- No subgroup result can replace or rescue a primary endpoint, and no significance claim is made from subgroups.
- Interpretation rule, stated in advance: a gain concentrated in `S_parsed` is consistent with the structural mechanism. A comparable gain in `S_failed`, where no structural bias is applied, points to a non-structural source such as extra parameters, gating, or training differences, and must be reported as weakening the mechanism claim.

## Remaining limitations

About 10% of short train functions still have no structure. Coverage on the full P_clean, P_project, and D_transfer cohorts, and by length and language, must be measured and reported after preprocessing. Masked annotations lose their own structural edges. The DFG remains the registered limited approximation.
