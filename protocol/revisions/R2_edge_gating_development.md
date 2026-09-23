# R2: edge-gating development extension

Date: 2026-09-23. Scope: implementation, software validation, and a bounded development pilot only.

The user's extension authorizes adding `edge_gated_astguard` while preserving the current
model as `query_gated_astguard`, and explicitly prohibits launching the full suite.
`astguard` remains a supported name with unchanged state-dict keys and computation.
Existing run directories, result files, dataset splits, the 200-job registered manifest,
and the official-test lock are preserved. This revision does **not** register a new final
experiment campaign or authorize official-test access.

## Development design fixed before execution

- Public pinned CodeBERT checkpoint: `3b0952feddeffad0063f274080e3c23d75e7eb39`.
- Existing AST leaf-path radius 4 and directed approximate DFG; no new relation types.
- Existing structural layers `(2,5,8,11)`, head, tokenizer, AdamW, weighted BCE,
  AP-based checkpoint selection, and calibration-only threshold selector.
- Main pilot: sequence, fixed AST+DFG, original query gate, edge gate. Additional
  parameter-count-matched query control uses the edge projection on `[hi;hi;hi*hi]`.
  This matches parameter count, **not** effective function-class dimension; the
  repeated linear `hi` terms are algebraically redundant.
- 96 training-partition records only, selected with fixed hash salts, balanced
  within four development roles: train 32, tune 16, calibration 16, validation 32.
  One representative per dependence component across roles in the candidate pool.
  No official validation or test record is a model input or calibration example.
- Max length 64, seed 42, microbatch/effective batch 4, FP32, two epochs (16
  optimizer steps/model), learning rate 2e-5, multiplier 1, weight decay .01,
  linear decay with one warmup step. No natural-prevalence claim from this pilot.
- Overfit diagnostic: eight training examples (four/class), same pretrained edge
  model, classifier dropout zero, LR 1e-4, weight decay zero, maximum 80 steps.
  Pass only if evaluation-mode training loss falls by at least 75% and accuracy
  reaches at least 95%. This diagnostic does not choose a pilot hyperparameter.
- Edge diagnostics: raw edge gates and effective coefficients; row-mean replacement,
  within-query/head/relation permutation, and zero-gate interventions. Freeze the
  original calibration threshold under intervention. No causal explanation claim.
- Record all pilot conditions even if the edge model loses. Stop after reporting.

## Implementation-level discovery

The unchanged CLS-only head and no-special-token-edge invariant make structural
bias in the last encoder layer irrelevant to the classification logit. Its task
gradient is zero. Preserve layer 11 for the matched development comparison;
before the final campaign, register a common active layer set, such as `(2,5,8,10)`,
for all structural conditions and separately report the historical placement.
Do not alter the head or give CLS structural edges to evade this finding.

## Required before final experiment registration

Use `docs/EDGE_GATING_NOVELTY_AUDIT_AND_DIRECTION.md` for the hypotheses,
literature comparison, experimental controls, audit results, and decision criteria.
Freeze a separately versioned manifest and protocol hash after the user reviews
the pilot. Historical results must retain their original names and provenance.
