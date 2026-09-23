# ASTGuard: novelty audit and research direction

Audit date: 2026-09-23. This document concerns the preserved repository plus the
edge-gating extension. It separates implemented software from scientific evidence.
It does not supersede completed results or silently rewrite the frozen protocol.

## 1. Direct answer: is this enough for a main-track paper?

**No: replacing a query gate with an edge gate is not, by itself, a persuasive
main-track contribution.** It is a useful and testable architectural extension.
Whether it supports a strong paper depends on the results, the closest comparisons,
the realism of evaluation, and what new explanation the study establishes.
No venue was specified; this assessment assumes a competitive software-engineering
or security research track. It is not an acceptance prediction. A general ML-methods
claim would face even stronger architectural-novelty objections.

The strongest direction is a controlled study of **the granularity at which a
pretrained vulnerability detector should use imperfect program structure**:

> Does assigning different structural coefficients to individual neighbors improve
> realistic vulnerability detection beyond a shared query coefficient, with matched
> information, training budget, parameter controls, and audited extraction?

Do not sell a new sigmoid/MLP, the combination of AST and DFG, unrestricted attention,
or gate heatmaps as inventions. A defensible contribution would be a reliable empirical
finding about when edge selection helps, when it fails, and whether its benefit
survives removal of capacity, graph-density, information-access, and dataset artifacts.

## 2. Repository state found before modification

The repository was clean in Git at inspection. There were no applicable AGENTS.md
instructions in the workspace/ancestor locations inspected. The existing project is
well beyond scaffolding:

| Area | Existing implementation/evidence | Remaining distinction |
|---|---|---|
| Acquisition | Registered public sources/checksums; local PrimeVul, DiverseVul, CodeXGLUE development data and pinned checkpoints | Ignored files must be reacquired on another host |
| PrimeVul normalization | 235,768 records: 184,427 train, 25,430 valid, 25,911 test; zero quarantined in saved normalization report | Counts are acquisition evidence, not completed training |
| Structural extraction | Tree-sitter C/C++, byte/BPE alignment, annotation masking, cached sparse edge records, approximate reaching definitions | Manual edge-quality review and full-cohort audit still pending |
| AST semantics | Default `leaf_path_radius4`; optional anchored parent-child implementation | The pasted prompt's parent-child description is not the current default; preserve the existing default for this comparison |
| Models | Sequence, fixed AST, fixed DFG, fixed AST+DFG, query ASTGuard, dropout, relation/function/capacity controls | No published-quality performance established |
| External models | GraphCodeBERT C-adapted, LineVul function adapter, ReGVD adapter | Integration is not same-setting reproduced performance; Devign rich-graph pipeline remains unavailable |
| Training/evaluation | Weighted BCE, checkpointing, calibration/tune roles, AP/F1/MCC/ROC/FPR metrics, pairs and statistical infrastructure | Complete frozen feature registry and full experiments missing |
| Analysis | Topology/gate interventions, robustness, timing, gate plots, publication-table tooling | Most scientific analyses have not been executed |
| Experiment protocol | 200 registered jobs plus optional baseline jobs; official test locked | No full jobs or official-test results recorded before this extension |
| Hardware | Python 3.11.16, PyTorch 2.14.0+cpu, Transformers 4.57.6 | No local CUDA device; GPU memory/runtime cannot be measured here |

Existing R1 extraction audits reported 449/500 nonempty AST graphs on both the pilot
and a disjoint held-out training sample (89.8%), with DFG support 372/500 (74.4%) and
363/500 (72.6%). Empty graphs and unsupported analysis must remain in evaluation;
coverage must be broken down by class, truncation, project, and failure reason.
The release AST threshold was changed from 90% to 89% in R1 after a failed earlier
pilot. This history must be disclosed; an independent sample is useful but is not
a substitute for manual extraction validation.

Some older documents say neural dependencies were never run, while README and saved
artifacts describe subsequent runs. Those older passages are stale historical status.
Use dated run artifacts and the executed checks below as evidence. The existing
test-lock reason also retains the earlier coverage figure; its **locked** status
remains correct and has not been changed.

## 3. Targeted literature audit

This is a bounded search, not a proof that no identical method exists. Primary
sources were checked on the audit date. No code or published metric was imported.
Dates below refer to the cited paper/version, not search-engine crawl dates.

| Primary source | Mechanism/overlap | Consequence for ASTGuard | Inspection depth |
|---|---|---|---|
| [Shaw et al., 2018](https://aclanthology.org/N18-2074/) | Relation-aware self-attention, including graph-labeled inputs | Explicit relations in attention are established | Paper/abstract |
| [GREAT, ICLR 2020](https://vhellendoorn.github.io/iclr2020.pdf) | Source-code graph relations modify global attention; multiple relations combine | Particularly close code-model precedent; a simplistic fixed-only comparison is insufficient | Full-text attention equation |
| [GraphCodeBERT](https://arxiv.org/abs/2009.08366) | Data-flow-aware code pretraining and graph-guided attention | Required strong external structural comparator, with C adaptation labeled | Primary paper record; local adapter/source audit |
| [Graphormer, 2021](https://arxiv.org/abs/2106.05234) | Structural/edge information in transformer attention | Additive structural priors are established | Paper record plus published structural-bias description |
| [XLM-E, ACL 2022, Section 3.3](https://aclanthology.org/2022.acl-long.427.pdf) | Query-conditioned gates modulate relative-position biases | Direct precedent for the old gate family; relation/task specialization remains | Full-text equations |
| [GATv2, ICLR 2022](https://arxiv.org/abs/2105.14491) | Distinguishes static from query-dependent neighbor ranking | Endpoint-dependent selection is established; dynamic-ranking controls are necessary | Primary paper record and argument |
| [Relational Attention](https://arxiv.org/abs/2210.05062) | Transformers that use and update edge vectors | Pair/edge-aware transformer reasoning is established | Primary abstract; no equation-equivalence claim |
| [i-Align, 2023](https://arxiv.org/abs/2308.13755) | Edge-gated attention in a graph transformer for alignment | Even the broad phrase “edge-gated attention” has precedent | Primary abstract; no exact-method equivalence claim |
| [K-ASTRO, cited v3](https://arxiv.org/html/2208.08067v3) | AST-derived attention bias for vulnerability detection, with graph augmentation | Must be discussed as a close task-specific comparator; its adaptation differs | Full-text bias and implementation sections |
| [Gated Tree Cross-Attention, 2026](https://arxiv.org/abs/2602.15846) | Checkpoint-compatible gated syntax injection in decoder-only LMs | “Preserves pretrained model while injecting gated syntax” is also insufficient as a broad novelty claim | Primary abstract |
| [DualGraphVulD, 2026](https://www.sciencedirect.com/science/article/pii/S0950584926002508) | Semantic/structural integration, gated propagation, diagnostic analyses, realistic PrimeVul setting | Recent comparator requiring artifact/equation review before strong positioning | Publisher preview only; implementation equivalence not established |
| [PrimeVul evaluation paper](https://arxiv.org/abs/2403.18624) | Realistic chronology, label quality, duplication, difficult vulnerability evaluation | Benchmark realism and pair discrimination are central, not optional cosmetic analyses | Primary abstract and existing local protocol |

Search families included: query-gated relative bias; edge-conditioned structural
attention; graph relational attention in source code; AST/DFG gated vulnerability
detection; exact titles of GREAT, XLM-E, K-ASTRO, GATv2, and recent structural detectors.
Newer publisher results about edge-conditioned GNNs are leads, not verified equivalence
evidence. Follow-up must inspect available full texts and reproduction artifacts.

**Novelty classification:** query ASTGuard is an application/combination of established
ideas. Edge ASTGuard is a limited methodological extension: a bounded, endpoint-conditioned
structural coefficient inside matched pretrained CodeBERT. The most promising novelty
is the demonstrated empirical behavior and controlled mechanism analysis, if supported
by experiments. No “first,” SOTA, security guarantee, or semantic-understanding claim
is currently justified.

## 4. Exact implementation

The old model is preserved as `astguard` and its exact alias `query_gated_astguard`:

\[
g_{i,r}^{l,h}=\sigma(W_r^{l,h}h_i^{l-1}+b_r^{l,h}),\qquad
S_{ij}^{l,h}=Q_iK_j^T/\sqrt{d_h}+\sum_r\beta_r^{l,h}g_{i,r}^{l,h}M_{ij}^r.
\]

The new variant uses a **single affine projection**, not a hidden MLP:

\[
z_{ij,r}^{l,h}=w_{q,r}^{l,h\,T}h_i+
w_{k,r}^{l,h\,T}h_j+w_{\times,r}^{l,h\,T}(h_i\odot h_j)+b_r^{l,h},
\quad g_{ij,r}^{l,h}=\sigma(z_{ij,r}^{l,h}),
\]
\[
S_{ij}^{l,h}=Q_iK_j^T/\sqrt{d_h}+
\sum_{r\in\{AST,DFG\}}\beta_r^{l,h}g_{ij,r}^{l,h}M_{ij}^r,
\quad A_{ij}=\operatorname{softmax}_j(S_{ij}),\quad O_i=\sum_j A_{ij}V_j.
\]

Here `hi` and `hj` are incoming layer hidden states, not Q/K projections. The product
term is a diagonal bilinear interaction. Gates lie in [0,1]; beta is learned and signed,
as in the original implementation. A gate is not a calibrated trust probability.
The edge coefficient cannot independently change sign within a fixed layer/head/relation;
it scales the sign of beta. Report beta and `beta*g`, not just the sigmoid.

Gates start at .5 with all affine weights/biases zero. Adaptive beta starts at .10;
fixed beta starts at .05. Their initial effective biases match. Normal semantic
attention stays dense/unrestricted among nonpadding tokens, including pairs without
structural edges. No structural hard mask or graph-token architecture is introduced.

Disk records remain sparse. The existing collator still creates boolean `[B,R,L,L]`
masks. The new attention finds edges per relation and creates `[E_r,H]` gates, using
1024-edge feature chunks with activation recomputation during backpropagation.
It scatters coefficients into the existing `[B,H,L,L]` score layout and never builds
`[B,H,R,L,L]` gate tensors. Ordinary dense attention remains quadratic; this is **not**
a sparse-attention algorithm or a claim of computational routing. Dense score copies
and boolean-mask scans remain costs to benchmark.

The gate module is relation-indexed without AST/DFG-specific branches, so typed
relations can reuse it. Adding typed relations later still requires an explicit
schema/collator/relation-registry extension; the current data pipeline remains the
original two-relation pipeline.

## 5. What edge conditioning can actually change

For two keys j and k with identical structural relation signatures from i,
query gating adds the same structural amount to both scores. With hidden states,
Q/K, and all other conditions held fixed:

\[
\log\frac{A_{ij}}{A_{ik}}=s_{ij}^{seq}-s_{ik}^{seq}
\quad\text{under query gating},
\]

whereas edge gating contributes

\[
\sum_r\beta_r(g_{ij,r}-g_{ik,r})M_{ij}^{r}.
\]

Thus edge gates can alter within-relation relative preference directly. This is an
algebraic characterization, **not** a theorem that the trained model is better.
Query-gated and fixed models already have content-dependent semantic attention;
their neighbors do not receive equal final attention. Earlier structural layers also
change hidden states, so this fixed-state identity is not a whole-model invariance.

A useful additional boundary: without the product term, a scalar affine gate logit
has form `a(hi)+b(hj)`. Because sigmoid is monotone, gate ranking across keys is
independent of the query when key states are held fixed. The product term permits
query-dependent rank reversals. This motivates a **trained no-interaction ablation**
later; it is not a claim that an affine concatenation alone solves dynamic ranking.

## 6. Newly discovered final-layer limitation

`FunctionClassificationHead` reads only hidden state at position zero. Special tokens
receive no structural edges. In the last encoder layer, its query row therefore has
zero structural bias. Values depend on incoming states, and the subsequent feed-forward
and normalization operations do not mix tokens. There is no later layer to transfer
changes from other tokens to CLS. Therefore the final-layer structural module has
**zero effect on classification logits and zero task gradient**, even though other
token states can change.

The default `(2,5,8,11)` placement includes this inactive layer. The pilot preserves
it for fair comparison with the existing model. Before final registration, choose a
shared active placement such as `(2,5,8,10)` and retain the historical configuration
as an explicit ablation. Do not change pooling or permit special-token edges mid-study.
Final-layer gate plots must not be interpreted as learned vulnerability evidence.

## 7. Files changed and preservation boundary

Only these pre-existing model files required modification:

- `astguard/models/bias.py`: variant alias and routing for the two additional gate paths.
- `astguard/models/codebert.py`: select the new attention class and expose edge interventions;
  reject unsupported sharing settings explicitly.

Added: `models/edge_gates.py`, `models/edge_attention.py`, three model configs,
`tests/unit/test_edge_gating.py`, `scripts/run_edge_pilot.py`,
`scripts/benchmark_edge_pilot.py`, this audit, and R2.
The README links to the extension. Original attention/gate implementations, baseline
code path, data files, extraction, alignment, training engine, metric functions,
threshold code, full experiment manifest, test lock, and existing results remain intact.
Old query checkpoints load strictly through the alias with identical outputs.

The additional `query_capacity_matched` control has exactly the edge model's parameter
count but observes `[hi;hi;hi*hi]`. The first two blocks are algebraically redundant;
it matches nominal parameter count and adds nonlinear query features, not effective
function-class dimension or FLOPs. A later independently specified nonlinear query
MLP control is appropriate if a capacity-independent claim hinges on this comparison.

## 8. What is still missing for a strong paper

| Missing evidence | Required action | Status after this extension |
|---|---|---|
| Reliable benefit beyond query gating | Five paired seeds for edge/query/fixed/sequence under frozen chronology and budgets | Not launched |
| Added-parameter explanation ruled out | Parameter-count-matched query control; matched-budget nonlinear query control if needed | First control implemented and included in pilot |
| True query-dependent edge preference | Trained no-product and simpler linear/GREAT-style controls | Existing linear control preserved; no-product trained control pending |
| Structural identity matters | Existing degree-preserving rewiring; relation removal; corruption with achieved rates | Existing infrastructure preserved; full results pending |
| Edge assignment matters | Replace edge gates by within-query mean; shuffle gates among that query's neighbors while preserving their multiset | Implemented and piloted; full inference pending |
| Extraction is credible | Independent human edge review, supported-construct tests, failure/coverage strata, full leakage audit | Software exists; human/full audit pending |
| Ranking gain has practical use | AP primary, low-FPR calibrated recall, achieved FPR and uncertainty, patch-pair ordering/decisions | Metric infrastructure exists; main evidence absent |
| Benefit is not extra source visibility | Full-function vs visible-prefix extraction, complete-function subset with fixed tokenizer budget | Existing visibility controls preserved; execution pending |
| Generalization | Untouched chronological PrimeVul; held-out projects; decontaminated DiverseVul | Full manifests/audits and runs pending |
| Strong contemporary comparisons | Same-setting GraphCodeBERT/LineVul; verify K-ASTRO and recent public artifacts; frozen public/local model where feasible | Existing adapters available, closest-method reproduction unresolved |
| Efficiency | GPU batch/length sweeps, edge density, peak memory, preprocessing-inclusive latency, confidence over repeats | CPU pilot measured; target GPU pending |
| Explanations supported | Effective coefficients and interventions; independently reviewed successful and failed examples | Gate statistics are descriptive only |

Do not respond to a weak pilot by adding more graph types, auxiliary objectives,
contrastive learning, counterfactual generators, or larger backbones all at once.
Each would obscure the primary question. Typed dependencies are a follow-up only
if current relation selection proves useful and manual extraction review supports them.

## 9. Proposed final hypotheses and decision rules

Freeze these in a new manifest after reviewing this development pilot. Keep the
existing protocol's primary AP endpoint and practical margin (.01 absolute AP)
unless a documented power analysis motivates a revision **before test access**.

1. **H-edge:** edge minus query AP has a positive multiplicity-adjusted paired interval
   and mean gain at least .01. This is the primary claim introduced by this extension.
2. **H-value:** edge improves beyond fixed structure and sequence under the same rule.
   Edge beating sequence but not query/fixed does not establish edge selection's value.
3. **H-assignment:** within-query permutation/mean replacement reduces the edge model's
   advantage; compare original and intervened predictions on the same functions.
   Report degree-1 queries separately, because their permutation cannot change anything.
4. **H-capacity:** the gain survives parameter/budget controls. Report uncertainty and
   limitations of nominal-count matching rather than claiming perfect capacity matching.
5. **H-operation:** improvements persist at validation-calibrated low false-positive rates
   and in vulnerable/patched discrimination. AP alone cannot substantiate this claim.
6. **H-cost:** any benefit is accompanied by measured memory/latency tradeoffs and
   meaningful behavior under extraction failures and structural noise.

Use paired seeds `[42,123,456,789,1024]` for the central comparison if the registered
compute budget permits; never fewer than three for a main improvement claim. Reuse
the project's dependence-aware/component bootstrap and multiplicity controls; do not
treat correlated functions or multiple seed predictions as independent observations.
Confidence intervals conditioned on selected hyperparameters must be identified as such.
The .01 margin is a research decision, not a venue acceptance criterion.

**Proceed:** active-layer gradients, overfit, clean equivalence, correct data checks,
and a resource-feasible natural-prevalence development experiment justify a final
campaign. A tiny balanced pilot cannot establish H-edge or eliminate it.
**Simplify:** if edge and query are practically equivalent across powered comparisons,
prefer the simpler query model and report the boundary of edge conditioning.
**Stop claiming adaptivity:** if fixed matches both, make the empirical result explicit.
Do not select a favorable metric or subset after seeing the official test.

## 10. Execution and results

The bounded pilot, its actual measurements, test record, and reproduction commands
are reported in the execution appendix below. No full multi-seed suite or official-test
evaluation is authorized or launched by this extension.

## 11. Full-run resources and practical limits

CodeBERT is approximately 125M parameters. FP32 weights, gradients, and two Adam
moment tensors alone require about 2 GB (decimal), before activations, optimizer
temporaries, allocator overhead, and input tensors. One FP32 attention-score tensor
at B=4, H=12, L=512 is 48 MiB; training retains additional tensors across layers.
Dense AST/DFG masks at B=4, R=2, L=512 are about 2 MiB as booleans. Edge feature chunks
bound transient projection features but do not remove dense attention costs.

For four structural layers, D=768, H=12, R=2, query gate plus beta adds 73,920
parameters; edge gate plus beta adds 221,376. The increment over query is 147,456,
roughly .12% of the backbone. Low parameter overhead does not imply low runtime.

An engineering planning range is 12–24 GB GPU memory for modest microbatches at
length 512, with substantial dependence on precision, checkpointing and graph density;
this is **not a measured bound**. The previously mentioned ~46 GB GPU hosts need an
actual hardware/throughput check. This CPU host cannot verify their availability.

Estimate runtime only after 100 warmed optimizer steps on the target GPU:
`hours ≈ epochs * ceil(N_train/effective_batch) * seconds_per_optimizer_step / 3600`,
then add validation, checkpoint I/O, cold preprocessing, calibration, and analysis.
At 184,427 training records and effective batch 32, an epoch is 5,764 steps; five
epochs are 28,820 steps/model/seed before early stopping. At an **illustrative**
1–4 seconds/step, that is 8–32 GPU-hours/run, not a forecast. Twenty central runs
would take 160–640 GPU-hours at those assumed rates, before extras. Never extrapolate
the length-64 CPU pilot as a full-length GPU estimate.

## 12. Scientific limitations and intended paper direction

- Approximate intraprocedural DFG cannot resolve general aliasing, macros, external
  calls, types, or interprocedural vulnerability context.
- AST coverage does not equal relation correctness. Empty/unsupported relations and
  alignment failures can be associated with labels and projects.
- Full-function extraction can use information beyond the token window. Declare it.
- Chronological and duplicate-controlled splits reduce leakage but do not rule out
  pretraining contamination or inherited label noise.
- Balanced small-subset performance and successful memorization are software
  diagnostics, not evidence of realistic vulnerability detection.
- Gate/beta scaling and correlated structure preclude reading sigmoid values as
  semantic importance. Interventions perturb a trained model and are not causal
  identification of vulnerability mechanisms.
- Mainstream relation-aware and graph-attention precedents limit architectural
  novelty. Missing recent same-setting baselines constrain competitive claims.

Suggested working title: **When Does Edge-Specific Structure Help Pretrained
Vulnerability Detectors? A Controlled Study of Structural Attention Granularity.**
Lead with the empirical question, not a claim to have invented graph attention.
The architecture is the instrument for the study. A strong paper requires the study's
answer and supporting evidence; this implementation alone does not supply either.

## Appendix A. Completed execution record

Run: [`runs/edge-pilot-20260923`](../runs/edge-pilot-20260923/).
All reported classifier results use the pinned **pretrained full CodeBERT**, not
a randomly initialized tiny encoder. The separate existing neural smoke uses a tiny
encoder and is labeled accordingly. No prior run/result directory was overwritten.

### Tests and smoke

| Check | Actual outcome |
|---|---|
| Initial regression attempt | 62 tests passed and two temporary-directory setup errors; Windows sandbox denied pytest's private temp directory. No pass claimed for this attempt |
| Full suite after extension | **78 passed**, no failures or skips; includes the 64 pre-existing cases plus 14 new cases |
| New cases alone | 14 passed |
| Original zero-bias test | Preserved and passed |
| New pretrained edge zero-bias test | All encoder hidden states and logits match at atol=1e-6, rtol=1e-5 |
| Gate/attention tests | Sparse computation vs direct formula; shape/range; chunked gradient equivalence; endpoint dependence; overlapping relation addition; unrestricted nonedge attention; padding/special rejection |
| Compatibility tests | Strict old-query checkpoint alias, exact output agreement; save/load path exercised by real pilot; activation-checkpoint backward; empty graph and padding invariance |
| Mechanism tests | Product-term rank reversal; within-query gate multiset preservation; inactive final structural layer; evaluation-only intervention guard |
| Existing plumbing smoke | Completed: `runs/smoke-20260923T212328Z-54bf182d`, 60 records, three models |
| Existing neural smoke | Completed: `runs/neural-smoke-55ccebcba628`, three models and public training-only data |
| Tiny pretrained edge overfit | **Passed**, eight examples, 18/80 optimizer steps; loss 0.697714 -> 0.083755 (88.0% reduction), accuracy 100% |
| Pilot integrity audit | Matching prediction IDs, seeds and budgets; checkpoint hashes verified; no component overlap in candidate cohort; no special/padding edges; official test locked |

The complete suite succeeded outside the sandbox after the diagnosed temp-directory
permission issue. The pilot exited successfully. Matplotlib emitted a cache-directory
permission/cleanup warning after producing its figure; future runner invocations set
a run-local cache. These environmental issues were not model-performance failures.

Test evidence: [`edge_final_tests.xml`](../artifacts/edge_final_tests.xml).
Integrity evidence: [`verification.json`](../runs/edge-pilot-20260923/verification.json).

### Pilot setup and training behavior

Exactly the same 32 training examples, 16 tune examples, 16 calibration examples,
and 32 development-validation examples were used for all five conditions. Every
role is balanced and drawn from **official train only**. Seed 42, length 64, two
epochs, 16 optimizer steps, batch 4, LR 2e-5, FP32 and common weighted-BCE/AdamW
recipe. Training-derived weights are 1 for both classes because this cohort is balanced.
AP-based selection chose epoch 1 for all five models. Thresholds were fit only on
the separate calibration role, then applied unchanged to development validation.

| Model | First -> last epoch training BCE | Evaluation-mode train BCE, initialization -> final epoch | Selected epoch | Tune AP |
|---|---|---|---:|---:|
| sequence_only | 0.698105 -> 0.680231 | 0.702550 -> 0.671604 | 1 | 0.738381 |
| ast_dfg_fixed | 0.698120 -> 0.679763 | 0.702545 -> 0.671747 | 1 | 0.738381 |
| query_gated_astguard | 0.698120 -> 0.679763 | 0.702545 -> 0.671747 | 1 | 0.738381 |
| edge_gated_astguard | 0.698120 -> 0.679762 | 0.702545 -> 0.671746 | 1 | 0.738381 |
| query_capacity_matched | 0.698120 -> 0.679762 | 0.702545 -> 0.671746 | 1 | 0.738381 |

The final-epoch training loss and selected-checkpoint validation metric refer to
different epochs; they are intentionally distinguished. Raw precise values and all
gradient norms are in each run's `train_log.jsonl` and `metrics.json`.

### Actual development-validation results

| Model | AP | ROC-AUC | F1 | MCC | FPR | Calibration-selected threshold | Parameters (all trainable) |
|---|---:|---:|---:|---:|---:|---:|---:|
| sequence_only | 0.742588 | 0.675781 | 0.666667 | 0.107211 | 0.875 | 0.54790628 | 124,646,401 |
| ast_dfg_fixed | 0.753004 | 0.679688 | 0.666667 | 0.107211 | 0.875 | 0.54837942 | 124,646,497 |
| query_gated_astguard | 0.753004 | 0.679688 | 0.666667 | 0.107211 | 0.875 | 0.54837936 | 124,720,321 |
| edge_gated_astguard | 0.753004 | 0.679688 | 0.666667 | 0.107211 | 0.875 | 0.54837954 | 124,867,777 |
| query_capacity_matched | 0.753004 | 0.679688 | 0.666667 | 0.107211 | 0.875 | 0.54837942 | 124,867,777 |

All conditions had accuracy 0.53125, precision 0.517241, recall 0.9375, FNR 0.0625,
and confusion counts TN=2, FP=14, FN=1, TP=15. These very high false-positive rates
make the selected operating point unsuitable for realistic use. Low-FPR claims are
not estimable with only 16 development-validation negatives; one FP is 6.25% FPR.

**Finding:** no observed AP advantage for edge over query or fixed structure in this
pilot (difference exactly zero). This is not statistical equivalence or evidence
against a well-trained method: there is one seed, 32 validation examples, only 16
optimizer steps, and severe truncation. Conversely, the .010417 AP difference from
sequence does **not** establish a real improvement, and it cannot be attributed to
edge adaptation because all structural controls match it.

### Inference cost and memory

Original per-run timings are retained. Because some checks overlapped with the
initial campaign, an additional serial inference-only pass loaded the same selected
checkpoints, with no retraining. It used the same first validation batch, batch size
4, padded length 64, CPU FP32, two Torch threads, three warmups and ten timed repeats.

| Model | Mean / median / p95 batch latency, ms | Peak GPU memory |
|---|---:|---|
| sequence_only | 584.20 / 583.85 / 605.33 | Not measured: CPU-only host |
| ast_dfg_fixed | 595.97 / 596.76 / 621.01 | Not measured: CPU-only host |
| query_gated_astguard | 617.35 / 622.79 / 646.80 | Not measured: CPU-only host |
| edge_gated_astguard | 698.96 / 707.92 / 747.14 | Not measured: CPU-only host |
| query_capacity_matched | 345.39 / 351.33 / 370.52 | Not measured: CPU-only host |

The unexpectedly low capacity-control timing and differences from original per-run
timings indicate uncontrolled host/order variability. These are observed measurements,
**not a stable speed ranking**; do not publish speedup claims from them. Repeat on a
dedicated GPU with randomized run order, multiple batches, length/edge-density sweeps,
and uncertainty. CUDA synchronization is implemented for GPU use. Collation/extraction
are excluded from these forward timings and must be measured separately.

Training-loop wall times were 45.08, 39.61, 35.30, 26.84, and 45.92 seconds in the
table's order. They include tune inference/checkpoint I/O and were collected under
changing host contention; they are not training-throughput comparisons.

Source: [`serial_inference.json`](../runs/edge-pilot-20260923/serial_inference.json).

### Extraction and gate diagnostics

| Development role | N | AST nonempty | DFG status ok | DFG nonempty | Parse failures | Alignment failures |
|---|---:|---:|---:|---:|---:|---:|
| Train | 32 | 25 | 18 | 10 | 7 | 0 |
| Tune | 16 | 15 | 10 | 5 | 1 | 0 |
| Calibration | 16 | 14 | 10 | 7 | 2 | 0 |
| Development validation | 32 | 28 | 18 | 12 | 4 | 0 |
| Total | 96 | 82 | 56 | 34 | 14 | 0 |

DFG statuses total: 56 ok, 26 unsupported, 13 parse_failed, one lexical_failed.
Forty records have preprocessing reasons logged. No records were removed after
preprocessing. 87/96 functions were truncated at length 64. The low nonempty-DFG
coverage is especially important when interpreting an edge-selection experiment.
These figures are specific to the balanced, short-window cohort, not estimates of
whole-PrimeVul coverage. The candidate-pool dependence audit is not the still-pending
full-release clone audit.

On the selected edge checkpoint, active-layer/head/relation mean gates ranged from
0.493211 to 0.507416; the largest within-group gate standard deviation was 0.001029.
The final-layer gates remained .5. The tiny run learned very little differentiation.
Row-mean replacement, within-query permutation, and zeroing all edge coefficients
all left AP, ROC-AUC and the reported threshold decisions unchanged in this sample.
This provides **no positive evidence that edge assignment is currently useful**.
It does not mean the numerical probabilities were necessarily identical.

Artifacts include raw edge gates, effective coefficients, layer/head statistics,
intervention predictions, and a [gate heatmap](../runs/edge-pilot-20260923/edge_gated_astguard/gate_heatmap.png).
Only sparse eligible edges are included; descriptive edge averages weight high-degree
queries more heavily. A full paper also needs equal-query and equal-function summaries.

### Metadata transparency

The first executed pilot script inherited the pilot LR/weight-decay labels in the
overfit diagnostic's generic `resolved_config.json`; it actually used LR=1e-4,
weight decay=0 and no scheduler, correctly recorded in `result.json` and source.
The original file was retained and a separate
[`recipe_clarification.json`](../runs/edge-pilot-20260923/edge_overfit/recipe_clarification.json)
records the actual overrides. The current runner records the correct values plus
explicit diagnostic overrides on future runs. This metadata fix did not change or
rerun the completed experiment. Likewise, the capacity-control gate type is determined
by its variant, despite an inherited `gate_mode` label in the first saved config.
The current runner corrects that descriptive field.

The exact executed model files and pilot script were archived under
`source_snapshot/` with SHA-256 hashes. New runs also hash implementation files explicitly,
including untracked new Python files that a Git diff alone would omit.

## Appendix B. Exact reproduction commands

From the repository root in PowerShell, using the existing research environment:

```powershell
$env:OMP_NUM_THREADS = '2'
$env:MKL_NUM_THREADS = '2'

.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.venv\Scripts\python.exe scripts\run_smoke_test.py
.venv\Scripts\python.exe scripts\run_neural_smoke.py

# New directory only; never point --output at an existing run.
.venv\Scripts\python.exe scripts\run_edge_pilot.py --output runs\edge-pilot-reproduction --include-capacity-control

# Read-only checkpoint evaluation; output filename must be new.
.venv\Scripts\python.exe scripts\benchmark_edge_pilot.py --run runs\edge-pilot-reproduction --output runs\edge-pilot-reproduction\serial_inference.json
```

The pilot requires `data/interim/primevul/records.jsonl` and the local checkpoint
registered in `artifacts/environment/development_sources.json`. For a fresh clone,
use the existing acquisition commands; they need no paid API:

```powershell
.venv\Scripts\python.exe scripts\acquire_development_sources.py --weights
.venv\Scripts\python.exe -m astguard.data.download --dataset primevul
.venv\Scripts\python.exe -m astguard.data.normalize
```

The Windows sandbox used here required the pytest command to run with permission
to access private temporary directories. A normal local terminal may not have that
restriction. Do not delete inaccessible old temporary directories to work around it.

For forensic reproduction of the first run, consult `source_snapshot/`; the current
runner has equivalent model/training behavior with improved metadata/cache handling.
CPU package/version differences can change floating-point results. This is not a
promise of bitwise reproduction across platforms.

## Appendix C. Next actions, in order

1. Review this **non-winning edge pilot** and the closest-method comparison. Do not
   treat implementation success as a reason to promise a main-track acceptance.
2. Complete independent manual AST/DFG edge review and the full leakage/split audit;
   retain official splits and explicit exclusions in derived analysis views.
3. Freeze a development-only active-layer comparison, preserving the old model:
   historical `(2,5,8,11)` versus shared active `(2,5,8,10)`. Keep all other factors fixed.
4. Run a bounded, adequately trained **natural-prevalence** development experiment
   on a GPU, with longer token windows and the same fixed/query/edge controls.
   Check effective-coefficient learning and edge-neighbor diversity before scaling.
5. If justified, add the trained no-product control and a nonredundant query-capacity
   control; verify/reproduce the closest public structural methods. Do not invent
   their implementations from abstracts or mix published cross-split numbers.
6. Register a new immutable manifest with H-edge, multiple-comparison handling,
   power/compute analysis, calibrated operating points, and failure criteria.
7. Only after explicit review of the pilot and completed release gates should the
   final multi-seed campaign be launched. The current task stops here.

Pending scientific runs include main multi-seed comparisons, trained mechanism/layer
ablations, paired evaluation, data efficiency, full robustness curves, project and
cross-dataset transfer, target-GPU efficiency, and publication-ready statistical tables.
Existing GraphCodeBERT, LineVul, and ReGVD adapters were preserved and regression-tested;
their expensive campaigns were not rerun. Devign remains explicitly unavailable.
