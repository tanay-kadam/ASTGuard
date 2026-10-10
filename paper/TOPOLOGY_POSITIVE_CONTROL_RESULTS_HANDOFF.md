# Synthetic topology–token alignment positive control: audited results and LaTeX handoff

Date: 2026-10-06. Purpose: supplementary evidence for the graph-reliance/negative-results paper. This file concerns only the new synthetic control; retain the real-data results from `paper/ASTGUARD_NEGATIVE_RESULTS_DRAFT.md` separately. Do not replace real vulnerability-detection results with these synthetic numbers.

## Main finding and framing

The graph-response adapter learned the synthetic endpoint/token alignment task in all three seeds: tune average precision (AP) was 1.000000 for authentic graphs, versus 0.500000 for separately trained sequence-only baselines and 0.503543 ± 0.000821 for separately trained shuffled-graph adapters (mean ± sample SD, three seeds). For the same authentic checkpoints, deleting graph edges reduced AP to 0.500000, and substituting degree-matched null graphs reduced AP to 0.497907, 0.510578, and 0.531016. All five prespecified success criteria passed for each seed.

This is evidence that this adapter and these interventions can expose reliance on graph endpoint/token alignment when the task explicitly requires it. It addresses the alternative explanation that the evaluated adapter is inherently incapable of using structural inputs. It strengthens interpretation of the real-data negative results, but does not establish that graphs are useless for vulnerability detection, that every prior architecture is working correctly, or that the framework improves real-world detection.

## Experiment construction

Generation seed: 20261006. Training: 2,048 paired components / 4,096 rows. Tune: 512 paired components / 1,024 rows. Every split is exactly balanced (train: 2,048 negatives and 2,048 positives; tune: 512 of each). Sequences and component IDs are disjoint between train and tune.

Each sequence contains 24 nonspecial tokens: six occurrences each of token IDs 100, 200, 300, and 400, randomly arranged. Special tokens 0 and 2 give a total length of 26. Each component has two examples with identical token IDs, attention masks, special-token masks, and positions, but opposite labels and different AST-channel edges.

- Positive label: four directed cycles of six nodes, each within a token type; every edge joins equal token types.
- Negative label: four directed cycles of six nodes, alternating between types A/B or C/D; every edge joins different token types.
- Each eligible node has one incoming and one outgoing edge. Each graph contains 24 directed edges. DFG is empty.
- Both labels have identical unlabeled graph topology (four six-node cycles), size, density, degree, sequence length, and token counts. The predictive information is the alignment of graph endpoints with token types.

These are synthetic graphs placed in the AST relation channel, not ASTs parsed from real programs. Describe the task as **topology–token alignment** or **endpoint/token alignment**. Do not describe it as learning program semantics, distinguishing unlabeled graph topology, or solving vulnerability detection. Metadata identifiers are not model inputs.

## Conditions and optimization

Nine full training runs: three conditions × seeds 42, 123, and 456.

1. Authentic graph-response adapter with true synthetic AST edges.
2. Identical graph-response adapter with length-matched donor/shuffled graphs during training; authentic tune graphs at validation.
3. Sequence-only CodeBERT classifier, trained separately with the same optimization budget.

Backbone: `microsoft/codebert-base`, revision `3b0952feddeffad0063f274080e3c23d75e7eb39`. The graph adapter projects contextual token states to 64 dimensions, aggregates neighboring projected states, forms elementwise endpoint interactions, pools them, and predicts a scalar graph response. The classifier combines its sequence logit with the learned, beta-scaled graph response. The variant used here is **graph_adapter**, not **null_centered_graph_adapter**: it does not subtract an expected null response. Consequently normal and uncentered intervention AP are identical; they are not two independent experiments.

All runs: four epochs, 512 optimizer steps, effective and microbatch size 32, gradient accumulation 1, unweighted binary cross entropy, AdamW, backbone learning rate 0.00002, new-module multiplier 50 (nominal new-module LR 0.001), weight decay 0.01, betas (0.9, 0.999), epsilon 1e-8, linear scheduler, warmup fraction 0.10, gradient clip norm 1.0, head dropout 0.1, initial beta 1.0, no activation checkpointing. Evaluation occurs each epoch; the checkpoint selected by tune AP is reported. All runs reached the full 512-step budget even when the selected checkpoint was from epoch 1.

Actual training precision: bfloat16. Device: NVIDIA L40S / CUDA. Remote runtime: Python 3.10.12, PyTorch 2.5.1+cu121, Transformers 4.49.0, tokenizers 0.21.4, safetensors 0.8.0, Pillow 12.0.0, pyarrow 25.0.0. Exact environment records are in the campaign directory. This differs from the repository-wide lockfile; cite the recorded campaign environment for reproduction.

## Complete training results

AP is non-interpolated average precision with tied scores grouped. Values below are on the **tune** split used for checkpoint selection; they are not independent test results. ROC-AUC is a diagnostic recomputed locally from saved predictions.

- Authentic, seed 42: AP 1.000000000000000; ROC-AUC 1.000000000000000; selected epoch 1; training 60.204096 seconds; run `runs/20261006T170147Z-3f0f2aef6e-42-2ea86c`.
- Authentic, seed 123: AP 1.000000000000000; ROC-AUC 1.000000000000000; selected epoch 1; training 60.458099 seconds; run `runs/20261006T170147Z-b7be7512ab-123-d7973b`.
- Authentic, seed 456: AP 1.000000000000000; ROC-AUC 1.000000000000000; selected epoch 1; training 59.285129 seconds; run `runs/20261006T170147Z-5118506e37-456-b6947e`.
- Shuffled, seed 42: AP 0.5040312701040259; ROC-AUC 0.5010910034179688; selected epoch 2; training 60.735457 seconds; run `runs/20261006T170147Z-3dfe8c9ac7-42-e422de`.
- Shuffled, seed 123: AP 0.5040037567922085; ROC-AUC 0.5010681152343750; selected epoch 3; training 56.362218 seconds; run `runs/20261006T182614Z-ba94a366ee-123-61fc68`.
- Shuffled, seed 456: AP 0.5025953237281390; ROC-AUC 0.5004768371582031; selected epoch 4; training 56.507944 seconds; run `runs/20261006T182614Z-ac2077913e-456-ea62ca`.
- Sequence-only, seed 42: AP 0.500000000000000; ROC-AUC 0.500000000000000; selected epoch 1; training 48.067345 seconds; run `runs/20261006T182614Z-6521dba912-42-ad57e5`.
- Sequence-only, seed 123: AP 0.500000000000000; ROC-AUC 0.500000000000000; selected epoch 1; training 46.106745 seconds; run `runs/20261006T170256Z-290aaf815c-123-c831fe`.
- Sequence-only, seed 456: AP 0.500000000000000; ROC-AUC 0.500000000000000; selected epoch 1; training 44.124179 seconds; run `runs/20261006T182718Z-3df2ea9aa8-456-a0f799`.

Across-seed AP summaries (sample SD with denominator n−1):

- Authentic: mean 1.000000000000000, SD 0.000000000000000.
- Sequence-only: mean 0.500000000000000, SD 0.000000000000000.
- Shuffled: mean 0.5035434502081245, SD 0.0008212168484140304.
- Mean authentic-minus-sequence AP: +0.500000000000000.
- Mean authentic-minus-shuffled AP: +0.4964565497918755.

The sequence-only AP of exactly 0.5 follows from the paired construction: every sequence score occurs with both labels. Shuffled deviations slightly above 0.5 are small and are reported without interpreting them as meaningful gains.

## Same-checkpoint interventions: all numbers

Each authentic checkpoint was evaluated on all 1,024 tune examples at batch size 64. There was no retraining. For null construction, eight null graphs per example were generated with one position block; null-as-real substitutes the first draw. Reported edge-change fractions summarize the generated null draws. Empty substitution supplies zero relation masks. Sequence-path evaluation uses the same checkpoint's base logits, distinct from the separately trained sequence-only baseline.

Seed 42:

- Normal AP: 1.000000000000000.
- Sequence-path AP: 0.500000000000000.
- Uncentered AP: 1.000000000000000.
- Null-as-real AP: 0.49790734212591625.
- Empty-graph AP: 0.500000000000000.
- Normal-minus-null AP: 0.50209265787408375.
- Normal-minus-empty AP: 0.500000000000000.
- Mean absolute structural correction: 7.8188138185068965 logit units.
- Mean AST null edge-change fraction: 0.9569548964500427; DFG: 0.0 (empty).
- Evaluated checkpoint SHA256: `a72b035f1b7869036c690ee981dec23f91fdaaabccc335c3e069290bac3e9aa4`.

Seed 123:

- Normal AP: 1.000000000000000.
- Sequence-path AP: 0.500000000000000.
- Uncentered AP: 1.000000000000000.
- Null-as-real AP: 0.5105776390842538.
- Empty-graph AP: 0.500000000000000.
- Normal-minus-null AP: 0.4894223609157462.
- Normal-minus-empty AP: 0.500000000000000.
- Mean absolute structural correction: 7.812410932499915 logit units.
- Mean AST null edge-change fraction: 0.95635986328125; DFG: 0.0 (empty).
- Evaluated checkpoint SHA256: `facee53be576c3021054d7f0b0daba340058d2d4eeffe5147dc7339930cc0bb8`.

Seed 456:

- Normal AP: 1.000000000000000.
- Sequence-path AP: 0.500000000000000.
- Uncentered AP: 1.000000000000000.
- Null-as-real AP: 0.5310157609603830.
- Empty-graph AP: 0.500000000000000.
- Normal-minus-null AP: 0.4689842390396170.
- Normal-minus-empty AP: 0.500000000000000.
- Mean absolute structural correction: 7.782182178925723 logit units.
- Mean AST null edge-change fraction: 0.9566243886947632; DFG: 0.0 (empty).
- Evaluated checkpoint SHA256: `96d500f0c45a67057be9d3f7c89c93d3ca1edad648bc51e4ae505fc93b18d4d7`.

## Frozen success rules

Every seed had to satisfy all five rules: authentic AP ≥ 0.90; authentic minus separately trained sequence AP ≥ 0.30; authentic minus shuffled AP ≥ 0.30; normal minus empty AP ≥ 0.30; normal minus null AP ≥ 0.20. All 15 seed/rule checks passed. Thresholds are recorded in `docs/POSITIVE_CONTROL_PROTOCOL.md`; no threshold was changed after results were obtained. The official PrimeVul test split was not used.

## Local audit and evidence trail

Audit script: `scripts/audit_topology_positive_control.py`. Machine-readable audit: `artifacts/audits/topology_positive_control_local_audit.json`. Remote machine summary: `artifacts/audits/topology_positive_control_v1_summary.json`.

The local audit recomputes all nine selected-checkpoint AP values and all 15 intervention AP values independently with scikit-learn, recomputes diagnostic ROC-AUC and mean absolute structural correction, verifies seed means and sample SD, checks dataset hashes against run provenance, checks complete status and all 512 optimizer steps, checks resolved condition/seed/backbone/optimization settings, checks saved selected predictions against the selected epoch's predictions, checks available artifact SHA256 values, and matches intervention checkpoint hashes against the training checksum manifests. Metric differences from the repository implementation were below 1e-12 (floating-point summation only).

The downloaded dataset was independently checked for exact pairing, opposite labels, disjoint sequences, exact row counts, degree equality, four six-node cycles, empty DFG, and homophilic/heterophilic edge alignment. No split overlap or metric transcription discrepancy was found.

Additional checks: prediction IDs and labels match the tune dataset exactly; every selected AP matches the best recorded epoch AP; the fixed shuffled-donor assignment can be regenerated from each seed and matches its saved donor hash. All five success thresholds were independently rechecked, rather than accepting the summary's `passed` flag alone.

Checkpoint integrity: an independent `sha256sum` pass on the server hashed the saved checkpoint binaries. Both `best.safetensors` and `last_resume.pt` matched each run's original checksum manifest for all nine runs. The downloaded hash record is `artifacts/audits/topology_positive_control_remote_checkpoint_sha256.txt`. The evaluated authentic checkpoint hashes also match the intervention reports.

**Transfer status at handoff:** all numerical results, per-example predictions, logs, configs, provenance, synthetic data, and checksum records are local. The roughly 19 GB copy of checkpoint/resume binaries is still running separately; its local completeness has not yet been certified. The audit was run with `--metadata-only` to avoid reading partially downloaded checkpoint files; it verifies remote binary hashes and local numerical evidence. `unchecked_artifacts` in the machine audit refers to local binary verification still pending, not a failed experiment. Do not delete the remote repository or rely on the partial local binary copy as a complete backup. This transfer status does not change the verified numerical results above.

Data SHA256:

- Train: `aeebb03ab0950ef42c4d23a5832e2b79a7b319c2a5757c1e670b048188921921`.
- Tune: `6b16a5e793518de9d6aac5b0d56b0ded5075f4416a0183a8a11128ca7a88501c`.
- Split/manifest identifier: `725e6dc910b29f6771435f28865c8692f9bf35dfa421318741ccf2820f5c02c8`.
- Preprocessing identifier: `9846b0032e74b70b976ab1d361064ce8c1888b5b952b4f5adc693d5789803adc`.
- Compact downloaded archive SHA256: `d952103ef8f6551d0625ac70a71d35d02a19bb6111c95a0e57a1de48d9087567` (matched the remote hash).

Each training number maps to its run directory above, specifically `checkpoint_selection.json`, `selected_tune_predictions.jsonl`, and `provenance.json`. Each intervention number maps to `artifacts/release_gates/positive_control_v1_20261006/interventions/pc_authentic_s<seed>.json`, including every example's label and intervention logits. The campaign status log preserves the initial failed evaluations and subsequent successful retries. The failure was a script import-path issue; saved training checkpoints were reused. Completion was recorded at 2026-10-06T18:28:09Z, with summary exit code 0.

## Caveats that must survive LaTeX editing

- **Tune selection:** the same synthetic tune split selects checkpoints and supplies these reported numbers. There is no additional untouched synthetic test split. Report tune AP explicitly; do not write held-out test AP. Train/tune sequences are disjoint, but that does not remove checkpoint-selection bias.
- **Task scope:** this intentionally simple control supplies its target through graph endpoint/token alignment. Perfect synthetic AP is expected to be attainable and does not establish real-data performance or broad generalization.
- **Three seeds:** sample SD is descriptive. Zero SD here is not proof of zero population uncertainty. No confidence intervals or significance tests are claimed.
- **Architecture scope:** these results validate the graph-response adapter in this configuration, not every prior ASTGuard configuration. They do not validate a null-centering advantage because the trained variant is uncentered.
- **Intervention scope:** graph replacement shows model dependence under this constructed distribution. It is not causal evidence that AST structure improves real vulnerability detection.
- **Reproduction:** training logs record CuBLAS deterministic-workspace warnings. Seeds were set, but bitwise replay is not guaranteed. Training used bf16; intervention evaluation used its script's ordinary model precision. The normal intervention AP agrees with selected-checkpoint AP for all seeds.
- **No weight rerun:** the audit independently recomputes metrics from saved predictions and checks artifact hashes; it does not reproduce full training locally.

## Claim classification and recommended paper paragraph

- **SUPPORTED:** all three authentic seeds reached tune AP 1.0 and passed the frozen five-rule control; source: selected predictions, per-seed interventions, and machine summary.
- **SUPPORTED WITH CAVEAT:** the adapter can exploit graph endpoint/token alignment and the interventions can detect this reliance; evidence is confined to this synthetic task and configuration.
- **SUPPORTED WITH CAVEAT:** this control strengthens interpretation of the real-data negative results by demonstrating detectable reliance is possible in the implemented adapter; it does not resolve every explanation for the real-data results.
- **OVERSTATED:** the control proves the absence of useful structural information in vulnerability detection. The control does not test that claim.
- **UNSUPPORTED:** the campaign establishes a new state-of-the-art vulnerability detector or superior null-centered training. Neither was tested.

Suggested text for ChatGPT to adapt without changing scope or numbers:

> To check whether our adapter and intervention procedure can reveal structural reliance when it is present, we constructed a paired synthetic endpoint–token alignment control. Each token sequence occurs with both labels; graphs share token counts, degree, density, and unlabeled topology, while labels depend on whether edges connect equal or unequal token types. Across three seeds, the authentic graph adapter achieved tune AP 1.000 ± 0.000, compared with 0.500 ± 0.000 for sequence-only training and 0.5035 ± 0.0008 for shuffled-graph training. At the same authentic checkpoints, removing edges reduced AP to 0.500 in every seed, and degree-matched null substitution yielded AP 0.4979, 0.5106, and 0.5310. All prespecified success criteria passed. These results show that the implemented adapter can use endpoint–token alignment and that the interventions detect that reliance in a controlled setting; they do not imply a benefit on real vulnerability data. Results use a train-disjoint tune split also used for checkpoint selection.

For the LaTeX file, use one compact training-results table and one intervention-results table, with seed-level values in the appendix if space is limited. Preserve the caveats above. Integrate this as a diagnostic positive-control subsection supporting the existing negative-results framing, not as the paper's main detection benchmark.
