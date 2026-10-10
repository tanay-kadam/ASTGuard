# Corrected-split submission-strengthening campaign

Frozen design date: 2026-10-06. This campaign improves scientific evidence; it does not promise an acceptance probability. Do not select or suppress outcomes according to whether they support a negative-result story.

## Mandatory integrity correction

The historical `P_clean_stage0.json` removed five entries from `ordered_sample_ids` without filtering `roles`, `component_ids`, or `original_splits`, and retained the original manifest identifier. Compared with the correctly aligned original `P_clean.json`, 10,619 surviving samples change role, including 2,612 original test-role samples assigned to train. The prior numerical recomputations remain correct for their executed inputs, but they did not establish the intended split integrity. Earlier clean-split and untouched-test claims must not be carried into a submission without correction. Preserve all historical files; identify old results as compromised exploratory evidence.

Build a new manifest from the aligned original, remove the same five outliers across every row-aligned column, recompute counts and identifier, and validate source split and original component membership for every retained sample. Transfer and preprocess only corrected train/tune records. Original calibration/test examples remain excluded from the new campaign. Because earlier training already consumed some intended held-out samples, do not represent the historical official test as pristine; no final-test claim is made here.

## Hypotheses and falsification

H1: Longer paired training reveals a consistent authentic-topology AP benefit and a nontrivial graph-removal response. Falsified under the operational rules if authentic-minus-shuffled AP is not positive at all three seeds with mean at least 0.02, or removal has mean absolute logit change below 0.05. Report actual magnitudes and threshold sensitivity at 0.01, 0.02, 0.05, and 0.10; these cutoffs are not equivalence tests or universal constants.

H2: The published ReGVD ReGCN configuration depends on its native token-co-occurrence graph beyond graph-independent node-feature pooling. Compare native and equal-degree endpoint-permuted training with authentic tune evaluation; the self-only baseline uses identity adjacency at both training and evaluation. Also perform same-checkpoint native/null/empty/self-only interventions. Falsification of a positive effect uses paired signs and mean AP difference >=0.02; nulls must actually change edges to be informative. ReGVD is not an AST/DFG detector. No AST swap is substituted for a native-graph intervention.

H3: The attention-bias model and the null-centered adapter can learn a task requiring endpoint/token alignment. Train sequence, attention-authentic, attention-shuffled, centered-authentic, and centered-shuffled conditions with identical data and budget. Success requires authentic AP >=0.90, authentic minus sequence and matching shuffled AP >=0.30, and same-checkpoint normal-minus-empty/null AP >=0.30/0.20 for every seed. A failed sensitivity control limits interpretation for that architecture and is reported.

## Matrix and budgets

Seeds: 42, 123, 456 for every condition. Three seeds provide descriptive variability and paired direction checks; they do not support narrow equivalence intervals. No HPO follows inspection of final outcomes.

- Corrected real-data attention campaign: strong sequence, authentic attention, length-matched shuffled attention; three seeds; five complete epochs each. Save every epoch's tune predictions and training loss to inspect whether a plateau is reached. Five epochs are a bounded longer-budget check, not an assumed convergence guarantee.
- Corrected real-data adapter campaign: multiplier-10 sequence, uncentered, centered K=4/block=4; three seeds; three complete epochs each. Save every epoch and evaluate selected authentic checkpoints with matched interventions. The longer budget also reruns the compromised original rescue finding on valid splits.
- External ReGVD campaign: native, equal-degree endpoint-permuted, self-only; three seeds; up to 100 epochs, minimum 20, patience 10 tune-AP improvements (minimum delta 0.0001). This ceiling follows the upstream training scale. Selection and early stopping use tune AP, explicitly differing from upstream accuracy selection. Report learning curves and ceiling hits.
- Synthetic sensitivity campaign: five conditions listed in H3; three seeds; twelve complete epochs/1,536 steps. Generate new balanced train/tune/audit sets (4,096/1,024/1,024 rows), sequence-disjoint. Only tune selects checkpoints; synthetic audit outcomes are evaluated once after selection and are never used to modify budgets or architecture. The audit role is a synthetic holdout, not the PrimeVul official test.

Total: 42 training jobs (27 real/external and 15 synthetic), plus evaluations. All new real-data conclusions must use corrected-split runs. Historical results are not mixed into seed aggregates.

## Controls, fidelity, and data

Attention and adapter comparisons hold corrected cohort, preprocessing, CodeBERT revision, batch/optimizer/loss, within-family schedule, seed, selection role, and budget constant. They retain the previous family recipes except for corrected split and increased epochs. Weighted BCE and natural class prevalence are retained for the local detector family.

ReGVD follows pinned upstream `b5e6657b003ada704b7c75e4bd237c1eee1d8138`: GraphCodeBERT frozen word embeddings, whitespace-normalized source, fixed 400-token inputs including padding as upstream does, unique-token undirected window-5 graphs, normalized adjacency without self-loops, two-layer residual ReGCN/128 hidden units, sigmoid soft-attention with sum-times-max readout, unweighted BCE using classifier column 0, learning rate 0.0005, batch 128, weight decay 0, clipping 1. The harness retains upstream GNN FP64 arithmetic and classifier FP32. A node-order permutation is computationally invariant; verify normalized graph and GNN-forward parity against upstream before any full run. Common-cohort adaptation and AP selection must be disclosed, not presented as reproduction of upstream benchmark scores. Self-only training preserves the architecture and node embeddings and replaces adjacency with identity, isolating inter-node messaging. Fixed equal-degree permutations retain every node's degree and change endpoint identity; record changed-edge fractions and stationary cases. All external conditions use the same schedule and seeds.

Source records retain original labels and source hashes. Validate exact and component/source-hash disjointness, original source role, ID uniqueness, and absence of label metadata in model inputs. The new features contain the exact model-required token/edge fields; optional explanatory extraction metadata can be omitted only after collator-equivalence checks. Do not silently exclude additional functions on parse failure: existing extractor empty/status policy applies, and any exception blocks that cohort.

## Metrics, uncertainty, and artifacts

Primary metric: non-interpolated AP with ties grouped. Diagnostics: ROC-AUC, full-minus-base AP, mean/max absolute logit change, rank correlation, edge-change fractions, and epoch losses. Store every seed; report arithmetic mean and sample SD. Paired three-seed Student-t intervals are descriptive and explicitly wide. Evaluate prespecified cutoffs as sensitivity analysis without choosing a favorable cutoff afterward.

Save protocol/hash, commands, resolved configs, source snapshot identity, dataset/input hashes, environments, GPU identity, logs, all epoch predictions, selected checkpoint, checkpoint-selection metadata, status, failure evidence, and checksum manifests. Validate completion and metrics from raw predictions before claiming results. GPU scheduling uses currently idle GPUs only, in detached queues that survive VPN disconnect. Failures block the affected job and are preserved; unrelated jobs continue. Preparation and smoke gates must pass before a family executes full jobs.

## Interpretation and submission gate

Positive, negative, and mixed findings all qualify as evidence. Published-model coverage does not guarantee acceptance. A second dataset is deferred to avoid combining a hurried reproduction and uncontrolled extra scope. The submission remains blocked until corrected-split results are audited, synthetic sensitivity limitations are understood, the external fidelity check passes, and an anonymous runnable artifact is assembled. Manuscript corrections and independent artifact execution are separate from GPU completion.
