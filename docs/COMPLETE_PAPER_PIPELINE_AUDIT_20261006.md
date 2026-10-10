# Paper-facing pipeline audit — 2026-10-06

## Decision

**Historical SANER v2 real-data conclusions remain NO-GO for submission.** The audit confirmed three substantive pipeline defects, plus reporting/provenance weaknesses. The numerical AP implementation itself matched an independent implementation on every retained prediction population checked. Correct arithmetic does not repair wrong split membership or an incorrectly implemented experimental condition.

This audit covered source-to-split normalization, sample/component membership, rebuilt model inputs, graph construction and null/donor composition, model initialization/RNG, attention/adapter forward paths, optimizer grouping/loss/accumulation, checkpoint selection, inference interventions, seed summaries/intervals, and the paper-facing artifact trail. It is a comprehensive audit of the current evidence and implementation, not a guarantee that every possible future bug is absent or that unfinished experiments will pass.

Evidence: `artifacts/audits/complete_pipeline_audit_20261006.json`, `artifacts/release_gates/strengthening_20261006/rebuilt_population_audit.json`, CUDA seed probes, regression tests, and the preserved source/configuration/metric artifacts.

## 1. CRITICAL — historical split columns shifted

The legacy outlier generator removed five entries from `ordered_sample_ids` without filtering `roles`, `component_ids`, and `original_splits`. A subsequent `zip` joined the wrong role/component to samples, and the manifest retained the original identifier despite altered contents.

Verified consequences:

- ID column length: 186,893; the other row-aligned columns: 186,898.
- Role mismatches relative to the aligned original: 10,619.
- Incorrect component assignments: 33,761.
- Originally test-role samples assigned to training: 2,612.
- True original dependence components crossing historical train/tune: 605.
- Historical tune population: 9,092 original tune samples, 1,225 original train samples, 174 original test samples, and 75 original calibration samples.
- The malformed manifest's identifier does not match its contents.

The 38 historical real-data runs all report the 141,560/10,566 cohort and original manifest identifier associated with this preparation. The paper's clean-component-split and untouched-test conclusions cannot be supported by those runs. Their saved numeric results describe the executed population; do not substitute corrected metadata to make them appear clean.

Repair: the new manifest filters every aligned column, recomputes counts/identifier, and verifies original source role/component mapping. Join code rejects mismatched columns. The legacy generator now writes a separately named aligned manifest and refuses to overwrite preserved evidence. Existing legacy pipeline configs pointing to the compromised archived manifest are not a valid new reproduction entry point.

Corrected cohort: 141,560 train rows / 4,302 positives; 10,566 tune rows / 330 positives. New manifest identifier: `793ac1b2bcacb06aa19aef62ac575482dbb76a5307d026997ac239ce5157f5c2`.

## 2. HIGH — model construction overwrote the CUDA seed

`ASTGuardClassifier` initialized structural modules inside `torch.random.fork_rng(devices=[])` and called `torch.manual_seed(100000 + layer_index)`. That call reseeds CUDA too, whereas this fork restores only CPU RNG. For the study's final structural layer 10, the effective CUDA seed became 100010 instead of the requested run seed.

Reproduction on the SSH L40S: requested seed 42; CUDA seed before construction 42; after construction 100010. A CPU spy regression also observed calls `[17, 42, 100000, 100001]` for its two-layer fixture instead of only the two deliberate setup seeds.

Impact: attention/fixed structural models did not follow the documented full seed policy. CPU classifier initialization and data-loader seeds still varied, so the runs were not identical or fabricated; nevertheless CUDA dropout randomness was misconfigured. We cannot infer the direction or size of the performance change without rerunning. This defect affects historical attention-model results and six completed attention synthetic runs in the new campaign. Sequence-only models skip the structural initialization branch; graph-response adapters use a separate constructor. The original nine-run uncentered-adapter synthetic campaign is not affected by this defect.

Repair: structural initialization now seeds the CPU default generator only. Training asserts the actual CUDA seed after construction and records it. The same server probe after repair reports 42 before and 42 after. A fresh two-step CUDA attention training smoke completed and recorded actual seed 42, two optimizer steps, and unchanged start/end source identity.

The six new attention synthetic trials were moved intact into `quarantine/cuda_seed_bug_20261006T225625Z` within the remote campaign, with invalidation records. No results or checkpoints were deleted. Corrected replacements use the same frozen data, budgets, configurations, and requested seeds, and occupy the original logical job tags. Archived trials are excluded from final aggregation.

## 3. HIGH — centered shuffled training silently became authentic training

The trainer first constructed `GraphDonorDataset` for length-matched shuffled training, then overwrote `train_view` with `MatchedNullGraphDataset(train_dataset, ...)`. The latter used the original dataset instead of the already shuffled view. The centered-shuffled condition therefore had authentic graphs, despite a shuffled config and donor-statistics artifact.

An execution-path probe intercepted the real training entry point before optimizer updates and confirmed that the wrapper's base was `_FeatureDataset`, not `GraphDonorDataset`.

Impact: the three planned centered-shuffled synthetic conditions would be invalid controls. This was caught before their full runs started; the initial computational smoke was insufficient to detect the semantic error. The historical real-data centered campaign did not use shuffled training, and the original successful synthetic campaign used the uncentered adapter, so this defect does not invalidate those results directly. Historical real-data results remain compromised by issue 1.

Repair: attach null graphs to `train_view`, preserving the donor wrapper. Record effective view chains and assert that declared length-matched shuffling retains `GraphDonorDataset`. A fresh CUDA smoke recorded:

```
train: MatchedNullGraphDataset -> GraphDonorDataset -> _FeatureDataset
tune:  MatchedNullGraphDataset -> _FeatureDataset
```

The repaired training smoke completed. No full centered-shuffled result from the defective path will be used.

## 4. HIGH reporting qualification — attention diagnostics used a biased prefix

The paper's strong-attention graph-removal/gate measurements use the first 512 tune rows (32 batches of 16), with 63 positives. That is 4.8457% of the historical tune population, with prevalence 12.3047%, rather than the full population's approximately 3.2841%.

The measured mean absolute graph-removal logit changes are reproduced correctly: seed 42, 0.03428708319552243; seed 123, 0.03555784813943319; seed 456, 0.016434331017080694. Equal batch sizes make the batch mean equal to the example-weighted mean for these reports. However, these are prefix diagnostics, not full-cohort averages.

Likewise, stored Spearman summaries average batch correlations, not one global population correlation. Gate SD flattens heads/relations/query positions and includes padding/special queries; it is not solely the SD of gates actively applied to program edges.

Required paper correction: state sample size, prefix selection, and aggregation definition. Do not extrapolate the operational graph-use rule to the full cohort from that prefix. The new real-data evaluator now records full-cohort removal statistics, legacy batch/layer gate SD for comparability, eligible nonspecial gate moments, and prespecified cutoff sensitivity. Capturing attention diagnostics was tested to leave logits exactly unchanged in the regression fixture and was smoke-tested on CUDA.

## 5. MEDIUM — numeric audit could succeed without evidence

The legacy audit used `all(...)` over collections that could be empty, so an empty runs/interventions directory returned exit code 0 and true aggregate flags. It also asserted `official_test_used: false` without verifying original source membership.

Reproduction: zero runs, zero intervention reports, exit code 0. This is an audit blind spot, not evidence that actual saved AP values were invented.

Repair: require evidence, reject duplicate/empty prediction populations, and explicitly label the audit as metric recomputation rather than split/test certification. Test-use status is unknown (`null`) in this metric-only helper. The separate rebuilt-population audit checks actual original roles. Final campaign summarization requires all 42 unique logical jobs and waits for the attention-replacement queue.

## 6. Numerical precision and missing raw evidence

Independent scikit-learn recomputation matched AP for all 18 root-level runs with retained selected predictions: nine historical adapter-campaign runs and nine original synthetic runs. It also matched every AP path in six retained intervention reports: three real-data and three original synthetic reports. No reported-AP mismatch above 1e-12 was found. Selected prediction files match their retained selected-epoch files where present, and selected values match the best logged AP.

Twenty-nine historical run directories lack retained per-example predictions. Their reported AP can be traced to checkpoint-selection/history metadata, but this audit cannot independently recompute those values from absent predictions. Do not describe all 38 historical AP values as independently verified from raw predictions.

Training/selection AP uses float32 sigmoid probabilities; intervention AP uses raw logits. Float32 sigmoid can merge distinct scores into ties. In the original synthetic shuffled conditions, the probability-score mean AP is 0.5035434502081249, whereas raw-logit mean AP is 0.5037981038122922. The largest per-seed difference is approximately 0.00060936. Both calculations match their respective saved scores; this does not explain the 1.0-versus-0.5 control separation. Declare score format and preserve the frozen selection protocol, rather than silently changing reported numbers or retrospectively selecting another checkpoint.

The paper's strong paired 95% t interval and centered-minus-sequence 95% interval recompute to their reported rounded values. The default-recipe interval is approximately [-0.298640, +0.266104]; Figure 2 in v2 clips it at the displayed axis boundary. Widen the plotting axis before submission. The generic hierarchical-bootstrap helper defaults to confidence 0.975; explicitly pass 0.95 if a future result is labeled a 95% interval. The current paper's independently recalculated t intervals use the correct 0.95 level.

## 7. Metadata/provenance fixes and remaining qualifications

The seed-42 checkpoint SHA256 in the original positive-control Markdown handoff was truncated to 53 characters. It has been corrected from the actual intervention/checksum record. The metric values were unaffected.

The attention factory derives relations from `variant` and does not forward a `model.relations` override. In the new synthetic attention configs, declared relations are AST-only, while the actual model has AST and DFG gates. DFG inputs are empty, so the label signal still comes only from AST-channel alignment. Record the actual two-relation architecture; do not claim a one-relation attention implementation from that config field. New provenance/evaluation records expose actual relations. This metadata discrepancy does not require changing already defined contrasts or interpreting empty DFG as useful signal.

Source identity was formerly captured only at run end. New runs retain start/end source identities and a drift flag; a final filesystem hash alone does not prove which version a running process imported. Existing outputs remain preserved rather than having source claims rewritten.

The new final summary originally recomputed metrics but did not emit the frozen synthetic success rules or paired-effect checks. It now reports both. Execution completion is still distinct from hypothesis success: negative or mixed findings are not failed executions.

## 8. Full rebuilt-population checks

The server audit independently scanned all 141,560 corrected training examples and all 10,566 tune examples, plus their ReGVD input/cache streams. It checked original source membership, labels, component assignment, raw-source hashes, complete ID populations, feature/split identifiers, file hashes, sequence lengths/masks, graph endpoint bounds/special exclusion, native graph node ordering, and symmetric graph-cache structure. All checks passed; the scan took approximately 749 seconds. A separate comparison of 209,857 upstream train/validation records against normalized records found zero label/source/split mismatches.

Representation overlap remains: nine token-sequence fingerprints and eight full local-model-input fingerprints occur in both corrected train and tune. This can arise when distinct source functions collapse under truncation/projection; it is not the historical shifted-component bug. Disclose and quantify it in the final results, and avoid claiming strict model-input disjointness. A supplementary evaluation excluding overlapping tune inputs is a reasonable sensitivity analysis; no such AP is claimed here.

Normalized records do not persist their lexical fingerprints (152,126 corrected records have an empty lexical-hash field). The audit therefore does not treat an empty-field comparison as proof of zero lexical-clone overlap. Original frozen component membership was validated and raw-source disjointness checked; an entirely independent re-execution of the global near-clone component builder is outside this pass.

Extraction coverage is a limitation rather than a new silent-drop bug. Tune status counts: AST/DFG both OK 6,933; AST OK/DFG unsupported 2,231; parse failed for both 1,284; parse failed/lexical failed 80; AST OK/lexical failed 38. All examples remain in the cohort, with the extractor's declared empty/status policy. These features are not ideal complete program-dependence graphs.

## Checks and campaign state

After repairs, all 107 unit/audit tests passed. Specific regressions exercise actual dataset-wrapper composition, CUDA-seeding calls, empty-evidence rejection, unequal-size gradient accumulation, model/adapter gradients and zero-bias equivalence, upstream ReGVD graph/readout parity, checkpoint restoration, and diagnostic capture without a logit change. CUDA probes and training/evaluation smokes passed. This is evidence for the repaired implementation, not certification of unfinished real-data outcomes.

Original queue schedulers were temporarily held during the audit and then resumed on GPUs 5 and 6. The six invalid attention synthetic trials are preserved remotely, with corrected replacements detached on GPU 3 in `astguard_seed_repair_20261006`. The main session remains `astguard_strengthen_20261006`. The logical campaign still contains 42 planned valid training jobs; six invalid execution histories are kept separately. Source/budget/seed contrasts were not changed to favor an outcome.

## Supported claims now

- **SUPPORTED:** the original uncentered-adapter synthetic control's AP and graph-intervention values match saved predictions and its separate paired dataset. The three confirmed defects above do not invalidate that campaign.
- **UNSUPPORTED for submission:** the historical real-data results establish clean-split generalization or use an untouched official test. The split defect contradicts those claims.
- **SUPPORTED WITH CAVEAT:** historical checkpoints exhibited the stored intervention behavior on their executed populations; this is exploratory evidence, with the split and diagnostic-prefix limitations attached.
- **UNVERIFIED:** what the corrected longer-budget runs establish about authentic graph advantage, or whether the repaired attention/null-centered controls pass their frozen success rules. Wait for complete outputs and audit them.

Do not submit SANER v2 with the historical numbers relabeled as corrected results. Replace the affected real-data evidence, preserve contradictory outcomes, and review the resulting claims after the valid campaign finishes.
