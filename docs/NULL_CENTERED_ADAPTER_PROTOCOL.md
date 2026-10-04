# Null-centered structural adapter: development protocol

Status: frozen design for development-only prototype. The official PrimeVul test
split remains locked. This protocol does not claim that the method works.

## Hypothesis and falsification

If a shared graph adapter is centered by its response to degree- and
position-matched null graphs, authentic AST/DFG topology will improve tune AP over
both sequence-only and the identical uncentered adapter, and replacing authentic
graphs at inference will reduce AP. The hypothesis is falsified if the advantage
does not replicate across all three development seeds or if the mean improvement
over either primary control is below 0.02 AP.

The independent variable is response centering. The centered and uncentered graph
models have identical trainable parameters, input features, backbone, classifier,
optimizer budget, and graph adapter; only subtraction of the matched-null response
changes. Sequence-only is the capacity-free reference.

## Data, splits, and leakage

Use the existing `P_clean` Stage-0 cohort, manifest
`e631d90d2f43ec09922bc2df806384d8b1aff091b58d2ae03a1c17e0052451e0`,
with the existing component-disjoint train/tune roles and preprocessing hash
`435aff72451638dae06492868e79a97c591178ea66ad2935799a61245bf0e869`.
No official test, calibration, or transfer data may be opened during development.
Before any confirmatory campaign, complete the pending manual edge-quality and
full split/leakage audits.

Each null graph permutes token identities only among tokens with equal incoming and
outgoing degree in the same one of four position blocks. It preserves sequence,
label, relation edge counts, every token's degrees, block-to-block edge counts, and
special-token exclusions. Four deterministic draws are used per example. The
achieved edge-change fraction must be reported; unchanged nulls are retained and
not silently replaced by a looser corruption.

## Models, budget, and metrics

Primary development conditions are:

1. sequence-only with classifier LR multiplier 10;
2. uncentered graph adapter with the same classifier and adapter LR multiplier 10;
3. null-centered graph adapter with identical parameters and four matched nulls.

Use seeds 42, 123, and 456, 4,424 optimizer steps, effective batch 32, the same
CodeBERT revision, weighted BCE, and tune AP checkpoint selection. Save every
per-example tune prediction. Report each seed, mean, standard deviation, paired
differences, and paired intervals; do not treat functions or seed predictions as
independent replicates.

Primary endpoints are tune AP for centered minus sequence and centered minus
uncentered. The mechanism endpoint is the within-checkpoint AP change when the
authentic graph is replaced by a matched null. Secondary endpoints are vulnerable/
patched pair discrimination, validation-calibrated low-FPR recall, correction
magnitude, extraction coverage, peak memory, and latency.

## Advancement and stopping rule

Advance to five-epoch confirmation only if both primary AP differences are positive
on all three seeds with means at least 0.02, authentic-to-null inference replacement
reduces AP on all three seeds, losses remain finite, and no major low-FPR or pair
regression appears. Otherwise record the negative result and stop this mechanism.
At most one preregistered redesign is permitted; post-hoc metric or subgroup
selection cannot rescue the hypothesis.

If the prototype advances, compare against shuffled training, empty graphs, fixed
structural bias, and an uncentered adapter; then evaluate five fixed seeds and five
epochs. The official test may be opened once only after configs, checkpoints,
metrics, exclusions, and analysis code are frozen.

## Artifacts and alternative explanations

Every run must retain resolved config, command, source identity, feature hashes,
environment, checkpoint-selection record, per-epoch predictions, checkpoint hashes,
null construction metadata, and intervention predictions. A positive result must
rule out lucky seeds, capacity, graph density/length shortcuts, extraction failures,
data leakage, tune overfitting, and increased compute as alternative explanations.
