# ASTGuard implementation specification

Protocol: 1.0, 2026-09-21. This is the standalone engineering contract extracted from `RESEARCH_MASTER_PLAN.md`. Implement this protocol; do not invent an architecture, choose a different dataset/split, change endpoints or select experiments from test results. This file specifies future work; no repository implementation or experiments have been completed during planning.

## 1. Deliverable and execution constraints

Build a reproducible C/C++ function-level binary classifier study with source acquisition, leakage auditing, syntax/data-dependency extraction, controlled CodeBERT models, external baselines, training, calibration, evaluation, repeated experiments, statistical analysis and generated paper artifacts. Implement the whole pipeline incrementally; scaffolding alone is not completion.

Use public/local tools only. No proprietary paid API, synthetic-data API, remote inference, or required credentials. Public downloads may use optional credentials for rate limits. If an official source cannot be acquired, fail with the expected resource and manual-import instructions; never silently replace the dataset or checkpoint.

The user has two execution resources, an SSH machine and a library PC, each with approximately 46 GB VRAM. Record actual GPU models, precision support, RAM, CPU, disk, drivers and available hours. Treat hosts as independent workers. Do not assume pooled memory or cross-host distributed training. Establish a Python3.11 environment on each; resolve tested dependency versions and create an exact lockfile. The planning workspace has not established CUDA and contains only the proposal documents and these plans.

Implementation completion requires tests, smoke pipeline, source/split manifests, trained runs or explicit blocked/omitted run statuses, and reproducible aggregation. A negative performance result is not an implementation failure. Report incomplete experiments explicitly.

## 2. Repository layout

```text
README.md  LICENSE  pyproject.toml  requirements.lock  sources.lock.json
.gitignore  RESEARCH_MASTER_PLAN.md  IMPLEMENTATION_SPEC.md
configs/
  base.yaml
  models/{sequence_only,ast_fixed,dfg_fixed,ast_dfg_fixed,astguard,
          astguard_dropout,fixed_adapter,linear_relation,function_gate,
          graphcodebert_c_adapted,linevul_function,regvd,devign_gnn,unixcoder}.yaml
  experiments/{main,relations,mechanism,layers,fractions,robustness,
               visibility,project_transfer,efficiency}.yaml
  hardware/{ssh,library}.yaml
protocol/{protocol_v1.json,experiment_manifest.jsonl,test_unlock.json}
astguard/
  __init__.py  config.py  train.py  evaluate.py
  data/{download,adapters,schema,audit,splits,subsets,preprocess,collate}.py
  parsing/{trees,lexical,scopes,cfg,reaching_defs,relations}.py
  alignment/{byte_spans,tokenizer,projection}.py
  models/{codebert,attention,bias,gates,heads,controls}.py
  baselines/{simple,graphcodebert,linevul,regvd,devign,unixcoder}.py
  training/{engine,optim,checkpoint,seeds}.py
  evaluation/{predict,metrics,thresholds,pairs,bootstrap}.py
  analysis/{__main__,gates,interventions,errors,efficiency,aggregate,tables,plots}.py
  utils/{hashing,provenance,atomic_io}.py
scripts/{run_smoke_test,run_experiment_suite,run_baselines,freeze_protocol,
         benchmark_hardware,verify_results,reproduce_tables}.py
tests/{unit,integration,golden}/
docs/{method,data,baselines,experiments,reproducibility,limitations}.md
third_party/{LICENSES,adaptation_notes}/
data/{raw,interim,processed}/
artifacts/{audits,preprocessing_failures,environment}/
runs/<run_id>/
results/{tables,figures,raw_aggregates}/
```

Use typed dataclasses with strict YAML validation, ordinary Python modules, PyTorch, Transformers/tokenizers, Tree-sitter C/C++ grammars, NumPy/SciPy/scikit-learn, Arrow/Parquet, matplotlib and pytest. Accelerate may support a local multi-GPU host, but independent single-GPU runs are the default. Pin actual tested versions and upstream revisions; do not insert speculative version numbers. Avoid unnecessary plugin frameworks or runtime monkey-patching of Transformer internals. Isolate compatibility code and adapted upstream code with notices.

Ignore raw datasets, caches, checkpoints and large run artifacts in git. Track source locks, protocol manifests, small synthetic fixtures, scripts and result provenance. Preserve upstream license notices; do not assert one new license covers third-party code or datasets.

## 3. Data sources and immutable acquisition

| Artifact | Official source / required behavior |
|---|---|
| PrimeVul | Original full release and official train/valid/test plus pair files linked at [DLVulDet/PrimeVul](https://github.com/DLVulDet/PrimeVul). Do not substitute metadata-enhanced v0.1 subset. |
| PrimeVul metadata | Optional left-join from v0.1 by verified function hash; preserve all primary rows and labels; count unmatched rows. |
| DiverseVul | Standalone release linked at [wagner-group/diversevul](https://github.com/wagner-group/diversevul). Do not use a merged-dataset split as standalone DiverseVul. |
| Legacy data | Optional official [CodeXGLUE defect-detection](https://github.com/microsoft/CodeXGLUE/tree/main/Code-Code/Defect-detection). Keep a separate setting. |
| Controlled encoder/tokenizer | `microsoft/codebert-base`, immutable resolved revision. |
| Graph baseline | `microsoft/graphcodebert-base` and [official graph logic](https://github.com/microsoft/CodeBERT). |
| LineVul | [Official replication package](https://github.com/awsm-research/LineVul); retrain from pretraining weights. |
| ReGVD | [Official implementation](https://github.com/daiquocnguyen/GNN-ReGVD). |

`sources.lock.json` entries: logical name, official landing URL, resolved download URL, release, upstream revision, retrieved UTC timestamp, bytes, SHA-256, license/access notes, local immutable path. Resolve actual hashes at acquisition. Validate JSONL schemas and counts; refuse an unregistered changed payload. Downloader supports `--manual-path` and checksum verification. Never execute code contained in dataset source strings. Do not download full-file context bundles unless needed for a registered analysis; they are not inputs.

## 4. Data schemas and information boundaries

Use JSONL for raw/diagnostic manifests and Parquet for normalized records and predictions. Data types below are contracts; nullable means null, not a fabricated default.

**SampleRecord:**

```text
sample_id: string (dataset:release:original_id or stable original row index)
dataset, release, original_split: string
original_id: nullable string
source_raw, source_canonical: string
label: int8 in {0,1}
raw_sha256, lexical_sha256, upstream_normalized_hash: string
project_id, repository_url, file_path, commit_id, timestamp: nullable string
language_metadata: nullable string
cwe_ids, cve_ids, pair_ids: list[string], empty when unknown
original_row_index: int64
component_id: string
view_membership: list[string]
```

Canonical source changes CRLF to LF only. Preserve original bytes. Validate label/source before locking manifests; quarantine invalid records with reason, original ID and row hash. Valid empty source stays.

**FeatureRecord:**

```text
sample_id, source_sha256, preprocessing_hash: string
input_ids: list[int32] (<=512)
attention_mask, special_tokens_mask: list[bool]
offsets_char, offsets_byte: list[pair[int32]]
original_bpe_length, retained_bpe_length: int32
language_selected: enum(c,cpp)
parse_status, ast_status, dfg_status, alignment_status: string
status_reasons, unsupported_constructs: list[string]
lexical_nodes: list[{id,kind,start_byte,end_byte,binding_id?}]
ast_tree_nodes, ast_tree_edges: sparse diagnostic data/cache references
lexical_ast_edges: undirected canonical pairs
lexical_dfg_edges: directed(query_occurrence,key_occurrence)
leaf_to_bpe: sparse mapping
ast_token_edges, dfg_token_edges: sorted unique int32 pairs
edge_projection_groups: lexical-edge -> projected-pairs mapping
relation_stats: edge counts, degree, span, eligible leaves, truncation/failure flags
```

Forward-pass feature records contain **no labels, CWE, CVE, project, filename, dates, commit message, pair identity, vulnerability description or patch flags**. Join labels only in the training/evaluation wrapper; join analysis metadata after predictions. Model.forward accepts token tensors and structural tensors, never SampleRecord.

**SplitManifest:** view/version, source hashes, rule hash, ordered sample IDs, component IDs, original split, role(train/tune/cal/test), exclusion reason/link evidence, counts and file hash. **PredictionRecord:** run_id, sample_id, dataset/view/split hashes, model_id, seed, logit, probability, label (evaluation join), t_f1/t_lowfpr/t_recall80 IDs and decisions, checkpoint hash, feature hash, optional metadata join reference. Oracle VD-S thresholds belong in metric diagnostics, not decision columns.

Store dataset/pair metadata once and reference it from predictions. A failed inference is a failed run or explicit per-sample error; do not drop rows and calculate flattering metrics on the remainder.

## 5. Leakage audit and split construction

Implement `LeakageAuditor.build_components(records)` and `SplitBuilder.freeze(records, components, rules)` as deterministic pure operations with stored inputs/outputs.

1. Exact raw SHA-256. Lexical fingerprint from a deterministic C/C++ lexer: discard comments/whitespace while retaining identifiers/operators/literal contents. Never delete whitespace inside strings. If lexical analysis fails, use raw hash and mark normalized hash unavailable; do not apply unsafe normalization. Upstream-style whitespace normalization is an additional diagnostic only.
2. Near clones: exact verified Jaccard >=0.90 between sets of lexical 5-token shingles, token-length ratio >=0.80. Shorter than5 tokens: exact normalized match only. Use a prefix-filtered exact similarity join and exact verification; record join implementation/hash. MinHash may screen additional identifier-normalized clone sensitivity but is not the complete primary detector.
3. Union exact/near-clone links, official vulnerable/patched pair links, same normalized repository+commit, same known CVE. Missing values create no links. Component ID is SHA-256 of sorted member sample IDs. Preserve giant components and link evidence; no label-based component editing.
4. Preserve official PrimeVul split files. Main view `P_clean`: retain all official test rows; remove training components intersecting original validation/test; remove validation components intersecting test. Never change a test label or remove a test row based on model results. If no purge is needed, mark equality with official setting.
5. Retained validation component hash `SHA256('validation-v1|' + component_id)` first64 bits divided by2^64 <0.5 -> V_tune, otherwise V_cal. No retries/label balancing. V_tune selects hyperparameters/checkpoints; V_cal selects thresholds only. If a partition has no member of a class, block this protocol and report need for a pre-test revision. If <50 positives per partition or <2,000 calibration negatives, mark rare-operating-point evidence descriptive.
6. Keep all valid parse/alignment/DFG failures in every model's evaluation population; zero only failed relation(s). Publish exclusion/failure manifest.
7. If P_clean differs from official, optional-to-budget but required-for-official-comparison sensitivity retrains sequence/fixed/adaptive on official splits, three seeds (9 extra runs), separate table with overlap flag. Never mix settings.

`D_transfer`: exclude DiverseVul components linked by the same checks to any PrimeVul split, including test. Freeze retained data before training. No target tuning/calibration. Require >=200 surviving positives and>=20 project clusters for confirmatory interpretation; otherwise descriptive, or unavailable if no credible independent cohort. Preserve conflicting labels as an audit finding, not a reason to select favorable labels.

`P_project`: project identity normalized repository URL host/path, strip `.git`, recorded alias map. Drop unknown-project samples from this view with reason. u from `SHA256('project-v1|' + project_id)` first64/2^64: train<.70, tune<.80, cal<.90, else test. Purge lower-priority overlapping components in order test>cal>tune>train. Never resample projects for better class balance. Same >=200 positive test/20 test project interpretation gate; no chronology claim. Tune/cal must each contain both classes or mark study infeasible.

Data fractions: from P_clean training components, u from `SHA256('fraction-v1|' + component_id)`; include u<f for f={.10,.25,.50,1}. Same nested sets for all seeds/models; report realized sample/positive/project counts. Do not redraw missing-class fractions. Recompute weights from each actual fraction.

Test labels are available only to integrity auditing and the locked evaluation path, not HPO/threshold selection or feature generation. Source/metadata-only overlap checks may inspect test inputs before training; this is an audit, not model adaptation. Document unresolved pretraining/unknown-clone contamination; do not claim a complete proof of independence.

## 6. Parsing, alignment and exact structural definitions

### 6.1 Tokens and parse selection

`CanonicalTokenizer.encode(s,max_length=512)` returns `<s>` + first510 BPE tokens + `</s>` with fast-tokenizer source offsets. Original BPE length counts source tokens before adding special tokens. No stripping, renaming, formatting, comment removal or new tokens in core input. Tokenizer is pinned to the same checkpoint revision for every controlled variant.

Build a character-index -> UTF-8-byte-index lookup and convert half-open offsets. Special/pad/zero-width tokens have no structural endpoints. Whitespace-only spans remain unaligned. A BPE token can map to multiple overlapping lexical leaves. A leaf is structurally eligible only when all its overlapping BPE pieces survived truncation; partial leaves have no edges. Use half-open interval overlap, deterministic sorted outputs and OR deduplication.

Tree-sitter C/C++: if language is missing/unreliable, parse both; select fewer error+missing nodes, then greater covered bytes, then C. Metadata may guide the first attempt but cannot make a failed parse acceptable. Core extraction uses the full canonical function without wrappers; revision R1 (`protocol/revisions/R1_annotation_masking.md`) masks a fixed a-priori list of annotation-macro identifiers with equal-length spaces in the extraction source only. Any error/missing node in the selected tree => empty AST+DFG, `parse_failed`; retain source tokens. Exclude comment leaves, retain punctuation/operator terminals and internal grammar nodes. Record grammar/parser revisions and language-selection diagnostics.

### 6.2 AST relation

For different eligible lexical leaves a,b, connect undirected if their shortest tree-edge path distance is1..4. For tokens i,j:

`M_AST[i,j] = (i != j) and exists a in leaves(i), b in leaves(j): a != b and distance_tree(a,b)<=4`.

Implement tree distances using ancestor/depth/LCA or bounded ancestor traversal, not dense all-tree matrices. BPE-project each lexical edge to all retained subword endpoint pairs, symmetrize, deduplicate, remove self/special/pad endpoints. Do not connect pieces merely because they belong to one leaf. Save the lexical graph to support group dropout and corruption.

Alternative for A4 only: anchor every tree node to its leftmost noncomment terminal descendant. Project each parent-child edge between different anchors, symmetrize/deduplicate, then BPE-project. Name it `anchored_parent_child`; default is `leaf_path_radius4`.

### 6.3 Approximate data dependencies

Official GraphCodeBERT parser code is not a ready C/C++ DFG implementation. Implement `ScopeResolver`, `StructuredCFG` and `ReachingDefinitions` locally, adapting only licensed applicable upstream logic. Never call a Java or C# extractor on C/C++ and label it correct.

Scope resolution:

- Bind function parameters and local scalar declarations to `(scope_id,declaration_occurrence_id)`; nested blocks shadow outer bindings.
- Identifier uses resolve to the nearest visible binding. Unknown global reads have no invented definition.
- Exclude type names, function names and member-name selectors from scalar variable bindings.
- Initializers read their RHS before generating the declaration's definition; declaration without initializer is represented as a declaration occurrence with no value-derived RHS links. Parameter definitions enter at CFG entry.
- Scope lifetime removes unavailable bindings, but graph nodes retain unique binding IDs; outer definitions are not killed by inner shadowing.

CFG events: reads and definite scalar writes in source-defined sequencing order. Support nested blocks, scalar assignments, if/else, while/do/for, break/continue and return. Conditions contain reads; for init/condition/update and continue targets have the language-correct edges. Back edges participate in a finite reaching-definition fixed point. Break exits the nearest loop; return has no normal successor. Branch joins union definitions. Short-circuit boolean and conditional expressions require explicit branch lowering; if not implemented correctly, mark DFG unsupported for the function rather than treating both branches as unconditional writes.

For CFG node v, `IN[v]=union OUT[pred]`, `OUT[v]=GEN[v] union (IN[v]-KILL[v])`; KILL contains earlier definitions of the same definitely assigned binding. Solve by a deterministic worklist to convergence. A resource timeout is a failure with empty DFG and logged limits; it is not convergence.

Each read u links `(u,d)` to all reaching definitions of its binding. Each new assigned occurrence d_new links `(d_new,u)` to scalar RHS reads. Compound assignment/increment reads old binding before writing. Pointer/array/member expressions record scalar base/index reads only; do not invent memory/alias edges. Calls record scalar argument reads, no callee effects, return provenance or interprocedural relations. Unsequenced modifying expressions, unsupported binding, goto, switch/fallthrough, exceptions, lambdas/captures, coroutines and preprocessor conditional control => empty DFG for the whole function with explicit reason. AST may remain usable. This is a limited dependency approximation, not sound C/C++ program analysis.

Project directed lexical dependencies with query=consumer/read/new assignment, key=source definition/RHS read. Cartesian-product all eligible BPE pieces; deduplicate and remove self/special/pad edges. Empty successful graph is distinct from failed/unsupported graph. Store parser/DFG coverage and raw failure reasons by language and length; labels are joined only for audit summaries.

Full-function graph construction occurs before induced-token truncation. Record it as `structural_context=full_function`. For E10b only, replace omitted suffix after the last retained lexical byte by spaces (preserve newlines), parse the visible prefix with error recovery, retain only error-free subtrees wholly within visible bytes, and perform DFG analysis on complete supported statements only, without facts from omitted suffix/back edges. Store a distinct preprocessing hash and changed extraction coverage. No suffix information may enter this control.

### 6.4 Caches and collation

Cache key: source canonical hash, lexer/version, canonicalization, parser+grammar revisions, DFG/CFG/scopes version, relation projection+radius, tokenizer revision, max length, structural context and cache schema. Do not reuse stale caches. Use atomic writes and per-shard locks; both hosts can reuse only verified identical caches.

Disk stores sparse lexical/token edges. Collator produces token tensors `[B,L]`, attention mask `[B,L]`, relation masks `[B,2,L,L]` Boolean, labels `[B]` separately, and metadata IDs outside model.forward. Construct masks per batch; no `[B,R,H,L,L]` persistent copies. Padding changes neither real-token relations nor logits. Vectorize gate computation and broadcast one relation at a time into scores; avoid retaining all attention matrices unless analysis requests them.

## 7. Model contract

### 7.1 Backbone and common head

Load identical pinned `microsoft/codebert-base` weights for all controlled models. Verify d768/H12/layers12/head64. Implement an explicit compatible attention module retaining exact pretrained Q/K/V, positional embeddings, residuals, output projections, layer norms, attention dropout and feed-forward blocks. Follow pinned upstream operation order. No unpredictable runtime monkey-patching. Use an eager reference path for equivalence tests and controlled cost comparisons.

Active zero-based structural layers `[2,5,8,11]`. Source cap512 positions including specials. Shared classifier:

`u = final_hidden[:,0,:]`

`z = Linear_768_to_1(Dropout(tanh(Linear_768_to_768(Dropout(u)))))`

Both dropouts0.1; output shape `[B]`; `p=sigmoid(z)`. Save one common head initialization per paired seed. Parameter additions use separate RNG streams so they do not perturb backbone/head initialization or training sample order.

### 7.2 Attention equations and shapes

For one active layer, Q/K/V `[B,12,L,64]`, hidden states `[B,L,768]`, gates `[B,12,L,2]`, beta `[12,2]`:

```text
q_ij = Q_i dot K_j / sqrt(64)
g_i,r = sigmoid(W_r h_i + b_r)                 # W per head/relation, 1x768
c_i,r = beta_r * g_i,r                       # signed beta
scores_ij = q_ij + sum_r c_i,r*M_r[i,j] + pad_key_mask_j
attention = softmax(scores, dim=keys)
head_output_i = sum_j attention_dropout(attention_ij)*V_j
```

Pad key mask is -infinity for padding,0 otherwise. Structural relations are soft biases only. All special tokens retain normal attention but have no structural edges. Every sequence contains specials, so no all-masked key row. Ignore padded query outputs. Use float32 stable score/softmax operations under autocast as needed; return the appropriate model dtype. Dropout is disabled in eval.

Per active layer, implement `nn.Linear(768,24)` reshaped into12 heads x2 relations. Gate W and b initialize0, beta initializes0.10 => gates0.5 and effective coefficients0.05. Fixed beta initializes0.05. beta is unrestricted signed FP32 parameter; no positivity transform, no gate normalization across relations, no gate sparsity loss. Exclude beta from weight decay. If structural terms are disabled or zero, the same model weights must reproduce the sequence forward pass.

Model variants:

| ID | Structural rule |
|---|---|
| sequence_only | No relation masks or extra modules in active computation. |
| ast_fixed | AST coefficient beta constant across queries. |
| dfg_fixed | DFG coefficient beta constant across queries. |
| ast_dfg_fixed | Both constant coefficients; no gates. |
| astguard | Both adaptive coefficients. |
| astguard_dropout | Same with training lexical edge dropout q=.10. |
| astguard_ast_only / astguard_dfg_only | Adaptive single-relation E2 variants. |
| linear_relation | `c_i,r = a_r + U_r*h_i/sqrt(768)`, a=.05,U=0; no gate/beta product. |
| function_gate | Same gate weights applied to mean of real source-token hidden states and broadcast; empty source mean=zeros. |
| fixed_adapter | Fixed combined bias plus `h + U_up GELU(U_down h + b_down)` before Q/K/V in each active layer; rank12, no up bias, up weights0, down initialized with saved seed. |

Keep `fixed_adapter` input to residual/remaining Transformer path consistent: the adapter replaces the attention sublayer input for Q/K/V only; the original residual stream remains the unmodified h. Record this exact placement. Gate params total73,824 across four layers; adaptive beta96. Fixed adapter extra weights+biases73,776 (four x18,444) plus fixed beta96. These are near matched, not equal-FLOP architectures. Count actual parameters and time them.

### 7.3 Structural dropout

At each training sample presentation, independently retain each lexical edge group with probability.90; AST reverse directions share one draw, directed DFG edges use one draw. Expand retained groups to BPE pairs and OR duplicate projections. Share mask across layers/heads. No inverted-dropout rescaling. Use a dedicated augmentation RNG keyed by run seed, epoch, sample ID and presentation count so resume is reproducible. Eval default q0. Requested robustness corruption is a separate explicit inference transform, not accidental train-mode dropout.

### 7.4 Loss

Actual training view has N examples, N0/N1 class counts; w_c=N/(2*N_c). Missing class => invalid config/run. Per-example loss:

`w1*y*softplus(-z) + w0*(1-y)*softplus(z)`.

Average over examples, not sum of weights. Gradient accumulation correctly weights partial microbatches and last batch. No balanced sampler/focal loss in main protocol. `unweighted_bce` A4 uses both weights1. Raw sigmoid scores are not asserted calibrated probabilities.

## 8. Configuration and training

Strict config fields (reject unknown keys):

```yaml
protocol_version: '1.0'
experiment_id: E1
dataset:
  name: primevul
  view: P_clean
  manifest_hash: resolved_at_freeze
  train_fraction: 1.0
  tune_role: tune
  calibration_role: cal
preprocessing:
  max_length: 512
  canonicalization: crlf_to_lf
  ast_relation: leaf_path_radius4
  ast_radius: 4
  dfg_version: resolved_tested_version
  structural_context: full_function
  cache_hash: resolved_at_preprocess
model:
  variant: astguard
  checkpoint: microsoft/codebert-base
  revision: resolved_immutable_revision
  structural_layers: [2, 5, 8, 11]
  relations: [ast, dfg]
  gate_mode: token
  beta_init: 0.10
  gate_init: zero
  head_dropout: 0.1
  structural_dropout: 0.0
training:
  seed: 42
  epochs: 5
  effective_batch_size: 32
  microbatch_size: 4
  gradient_accumulation: 8
  pretrained_lr: 0.00002
  new_module_lr_multiplier: 1
  optimizer: adamw
  adam_betas: [0.9, 0.999]
  adam_epsilon: 0.00000001
  weight_decay: 0.01
  warmup_fraction: 0.10
  scheduler: linear
  grad_clip_norm: 1.0
  loss: weighted_bce
  precision: bf16_if_supported
  activation_checkpointing: true
  validation_frequency: epoch
  selection_metric: average_precision
  min_epochs: 3
  patience: 2
  min_delta: 0.0001
evaluation:
  thresholds: [max_f1, fpr_0.005, recall_0.80]
  threshold_fit_role: cal
  bootstrap_replicates: 10000
  analysis_seed: 20260921
resources:
  host_profile: ssh
  max_vram_gb: measured_device_limit_minus_4
provenance:
  hpo_parent: null
  protocol_hash: resolved_at_freeze
```

Values written as `resolved_*` in this documentation are required runtime-resolution fields, not acceptable final config values. Resolver must fill immutable strings and reject unresolved values before a run. Hardware memory uses measured bytes, not a guessed decimal/binary capacity.

Main recipe: full fine-tuning, effective batch32,5 maximum epochs, AdamW settings above; weight decay on matrices, excluding all biases/layer norms/beta. LR multiplier applies to classification head plus structural/control modules; backbone gets pretrained_lr. Evaluate V_tune each epoch; no early stopping before epoch3, patience2 thereafter, minimum AP improvement.0001. Checkpoint selection: highest AP, ties earlier epoch. Handle FP16 scaler state if BF16 unavailable. Record nondeterministic ops and do not promise exact cross-GPU reproducibility.

HPO for each of eight main neural models and each A1 control: four cells `{LR1e-5,2e-5} x {new_lr_multiplier1,5}`. Sequence-only multiplier applies to its new head so cells are distinct. Each cell: same25% nested training subset,3 epochs,seed42; select top2 by V_tune AP (ties lower LR then lower multiplier), train those on100% up to5 epochs; choose V_tune AP, same tie rule. All final seeds restart from pretraining at the selected config; reuse a byte-identical promoted seed42 run only with provenance. Record failed trials in the budget; do not grant ASTGuard extra trials to rescue it.

Primary defaults (layers/radius/q) are fixed. Development ablations cannot replace the primary model after looking at test. For A5, shared recipe LR2e-5/multiplier1 for all core models. Microbatch starts4/accum8 on both hosts; profile and only change resource settings preserving effective batch32. Pair data order/initialization seeds. Assign comparable models across hosts evenly and record actual precision so method is not confounded with hardware.

## 9. Baseline adapters

`BaselineAdapter` needs only `prepare_features`, `fit`, `predict_to_common_schema`, `provenance`, `status`; avoid forcing external models into the controlled model.forward API. Common evaluator must use their exported predictions on exact same IDs.

**Prior:** constant training prevalence, default majority at threshold.5, additionally common threshold policy. **TF-IDF LR:** case-sensitive C/C++ lexical1/2grams, train-fit vocabulary/IDF, max100k features,min_df2,L2,C={.01,.1,1,10},balanced train weights,max_iter2000. Use first510 CodeBERT source-token window for matched-input main baseline; full-source optional result separate. Select C by V_tune AP, deterministic fixed solver seed42. Treat it as a legitimate classical competitor.

**GraphCodeBERT C/C++ adaptation:** pinned official checkpoint; preserve official graph-node input initialization, position IDs and graph-guided attention mask. Code budget384 positions including two specials; graph budget128 nodes, total<=512. Nodes are supported lexical dependency occurrences sorted by byte position, keep first128, retain edges among retained nodes. Average mapped code-token embeddings to initialize graph nodes as upstream. Use this spec's C/C++ extractor, not a falsely named official C/C++ parser. Declare `graphcodebert_c_adapted`. Classification head can use common function head; record adaptation. Empty/failed graph leaves code tokens and no graph nodes. Compare also with a three-seed controlled trio at max_length384. A sequence-only GraphCodeBERT checkpoint run is separately named and never substitutes for the graph model.

**LineVul function adapter:** pin official code; preserve function architecture and supported tokenization; remove localization/patch inputs from forward data. Retrain from CodeBERT pretraining, not upstream BigVul-fine-tuned weights. Four screening candidates: official published recipe, common LR1e-5 weighted, common LR2e-5 weighted, common LR2e-5 unweighted. Same proxy->top2 full schedule and V_tune AP selection. Preserve official recipe details in config/provenance. If harmonized forward is identical to the sequence baseline, show equivalence and don't count it as independent architectural evidence.

**ReGVD preferred:** pin official architecture/readout, token graph and CodeBERT embeddings; screen window{3,5} x LR{1e-4,1e-3},same proxy/promotion protocol; use three final seeds. **Devign optional:** require a faithful architecture, licensable reproducible rich-graph pipeline, recorded dependency versions and declared original hyperparameter grid before launch. If that cannot be established, `unavailable` with reason; do not implement a generic GNN and call it Devign. **UniXcoder optional:** public checkpoint, common classifier/protocol and four-cell HPO.

Each adapter status entry records upstream URL/commit/license, environment, preprocessing, input context budget, supervised history, labels used, changes, seed count, success/failure coverage and comparability. Any missing source/implementation is an explicit status, never invented results or published numbers placed into same-setting tables.

Also create `source_not_verified` status entries for recent relevant methods K-ASTRO,TNA-CAF,DualGraphVulD. Their papers/previews were located in the planning audit,but no runnable repository was verified. Stage0 has a fixed two-hour total public-artifact verification budget for these three entries. A faithful public/local implementation may enter a separately budgeted pre-test extension;otherwise retain the status and restrict claims to the controlled study. Do not invent a model from an abstract or silently substitute proprietary embeddings. The registered200-job budget excludes these extensions.

## 10. Thresholds and metric implementation

Implement one metric module shared by all models. Primary: scikit-learn-compatible noninterpolated `average_precision_score`; don't label trapezoidal PR area as AP. Save per-seed metrics, never average seed probabilities for main results. ROC-AUC, confusion counts, accuracy, precision, recall,F1,MCC,FPR,FNR secondary. Zero positive predictions -> precision/F1=0 with flag; missing class -> AP/ROC-AUC null+reason. Undefined MCC null; optional conventional0 under a separate key.

`ThresholdSelector.fit(calibration_predictions, calibration_manifest)` rejects any split other than cal. Candidate thresholds: all distinct scores plus+infinity. Decisions `p>=t`.

- max F1: maximize F1, tie lower FPR then larger t.
- FPR.005: among candidates with FPR<=.005, maximize recall, tie lower FPR then larger t.
- recall.80: largest t with recall>=.80.

Store threshold value (explicit JSON encoding for+infinity), rule, calibration-ID hash, calibration counts and checkpoint hash. Apply unchanged to clean test, pairs, subgroups, corruption and DiverseVul transfer. Report achieved test FPR/recall with counts; never call a validation-targeted threshold “matched test recall.” If calibration lacks a class, fail threshold fitting instead of consulting test labels.

Official VD-S: pin and parity-test [upstream evaluator](https://raw.githubusercontent.com/DLVulDet/PrimeVul/main/calc_vd_score.py). Output `official_vds_oracle`, FNR at evaluated ROC FPR<=.005, lower better. Its test-label-derived threshold is diagnostic only, never emitted as t_lowfpr or reused for inference. Expose oracle and calibrated metrics in visibly separate columns. If evaluated set lacks a class, return null regardless of an upstream undefined-case convention.

Pairs: use official membership, exactly one vulnerable and one patched member; validate ID joins, don't infer from row ordering. `pair_order=mean(1[pv>pb]+.5*1[pv=pb])`; logit margin zv-zb. At both t_f1 and t_lowfpr report PC(1,0),PV(1,1),PB(0,0),PR(0,1), summing1. Count same-visible-token pairs, same-full-model-input pairs and visible changed spans. Invalid/incomplete pair records get separate counts; do not fabricate matches.

Raw-score Brier score and ECE15 equal-width bins are optional descriptive diagnostics. Do not assert posterior calibration from weighted BCE; no post hoc calibration fitting on test.

## 11. Statistics and reportable decisions

Core seeds `[42,123,456,789,1024]`; other final runs `[42,123,456]`; corruption seeds `[1001,1002,1003,1004,1005]`; analysis seed20260921. Always retain individual values, mean and sample SD.

Primary family: AP(ASTGuard)-AP(fixed combined), AP(ASTGuard)-AP(sequence). For each,10k paired hierarchical bootstrap draws: sample core seed indices with replacement; independently sample test dependence-components with replacement shared across seeds/models; compute metric per seed on sampled rows, then mean paired difference. Retain paired records and multiplicities. Percentile97.5% two-sided CIs implement a Bonferroni family of2. Also output component-only CI conditional on fitted seeds and adjusted paired seed-t interval,df4. Strong positive claim requires mean gain>=.01 and lower bounds>0 in both adjusted hierarchical and seed-t intervals. Smaller positive effect is small, interval crossing0 is inconclusive,90% CI entirely within[-.01,.01] is practical equivalence at that margin. No endpoint substitution.

If bootstrap sample has one class, skip and count;>1% invalid => no confirmatory interval for that slice. Cluster-count<20 => descriptive. Project/superproject cluster bootstrap and leave-one-largest-project-out are sensitivity checks; union linked projects if a dependence component crosses them. Do not resample functions independently. Seed count is not multiplied by test rows or corruption repeats.

Threshold metrics: conditional bootstrap uses saved t; calibration-aware sensitivity independently resamples calibration components, refits thresholds for fitted models, and resamples test components. Official oracle VD-S refits only its diagnostic threshold on each test replicate. Pair metrics resample entire pair-containing dependence components. No HPO/training is rerun inside these CIs; label that limitation.

A1's three AP comparisons are a secondary family: Holm-adjusted paired seed t tests (n3,df2), bootstrap effect intervals and explicit low-power caveat. Every paired comparison uses the intersection of planned seed IDs: compare the first three core seeds to a three-seed control, never a five-seed mean against a three-seed mean in a paired test. Other exploratory rows report effects/95% CIs without uncorrected significance claims. Subgroup inferential AP requires30 positives+30 negatives and adequate clusters. Revision R1 pre-registers a secondary, descriptive parse-status subgroup analysis of both primary comparisons (label-free `ast_status`/`dfg_status` subgroups); it cannot replace a primary endpoint. CWE overlaps are descriptive. Corruption averages five stochastic repeats before method-level comparisons and area calculation.

Before test unlock, simulate approximate detectable AP effects from V_tune predictions and available seed/cluster variability. Use a target80% power diagnostic. Any seed expansion applies to all three core models and is frozen before test access; do not add seeds until a test p-value becomes favorable.

## 12. Registered experiments and launcher manifest

All rows inherit P_clean train/V_tune/V_cal/official test, Sections6-11 preprocessing/training/metrics and declared seeds unless stated. Each run has experiment/model/seed/config/split/preprocessing hashes and status. Model inference can be reused across experiments without duplicating training. No primary results selected from development-only runs.

| ID | Required runs and settings | Required artifacts |
|---|---|---|
| E1 | Eight main neural models (sequence,AST fixed,DFG fixed,combined fixed,ASTGuard,dropout,GraphCodeBERT,LineVul)x3; extra seeds789/1024 for core sequence/combined/adaptive. Prior+TF-IDF. | main_results.csv, seed_summary.csv, full predictions, baseline_status.csv. |
| E2 | Reuse E1; adaptive AST-only and DFG-only x3, holding selected ASTGuard recipe. | structural_ablation.csv. |
| A1 | fixed_adapter,linear_relation,function_gate x3,each same four-cell HPO. | mechanism_controls.csv, params/timing. |
| A2 | Five-seed ASTGuard inference with original gates, training mean clamp, function mean clamp, degree-bin query permutation, zero AST,zero DFG. | intervention_results.csv, paired logits, gate_statistics.csv. |
| A3 | Fixed/adaptive train with frozen degree-preserving rewired graphs x3, selected clean recipe. | topology_controls.csv, rewiring rates/degrees. |
| E3 | Five layer settings on25% train,seed42,3epochs:early[0,1,2,3],middle[4,5,6,7],late[8,9,10,11],distributed[2,5,8,11],all12. Choose best nondistributed four-layer by V_tune,train x3. Primary distributed remains unchanged. All-layer development-only unless expansion frozen. | layer_ablation.csv with development/final distinction. |
| A4 | Fixed/adaptive x4 single-change variants,25%train,seed42,3epochs:anchored AST,degree normalization,DFG symmetry,unweighted loss. | representation_sensitivity.csv,development-only. |
| A5 | Core3 models x3,LR2e-5,multiplier1; reuse identical E1 run configs. | shared_recipe.csv. |
| A6 | Adaptive model,25%train,seed42,3epochs: separately tie gate W/b across heads,active layers,or relations; fourth variant freezes beta=.10. Four proxy runs,no extra HPO. | gate_granularity.csv,development-only. |
| E4 | Core3 x3 seeds x fractions.10,.25,.50;reuse100% E1. No fraction-specific HPO. Additional development-only10% repeat for core3 at full-data optimizer-step count. | data_efficiency.csv and AP/examples/compute curves. |
| E5 | D_transfer,E1 sequence/fixed/adaptive/GraphCodeBERT,first3 seeds,no fitting. | cross_dataset.csv and overlap waterfall. |
| E6 | All applicable E1 checkpoints,official test pairs,no fitting. | paired_results.csv. |
| E7 | Fixed/adaptive/dropout x3 model seeds x5 corruption seeds;rates0,.05,.10,.20,.40,1;deletion and swaps separately;AST,DFG,both separately. Sequence invariance check. | robustness.csv,achieved rates,curves/area. |
| E8 | sequence/fixed/adaptive/dropout and valid externals,seed42,fixed host/sample. | efficiency.csv and raw timing. |
| E9 | E1 gates/effective coefficients,eligible rows;detailed fixed2k test-ID sample. | gate_statistics.csv and plot input tables. |
| E10 | E1 core5 seeds,length/degree/DFG-span/coverage strata. | failure_strata.csv. |
| E10b | Fully visible E1 subset;prefix-only fixed/adaptive x3 with distinct caches. | visibility_controls.csv. |
| E11 | Core3 x3,P_project,selected E1 recipe;project tune/cal checkpoint/threshold fitting. | project_transfer.csv. |
| E12 | At first seed t_f1:20 hash-selected examples per four sequence/adaptive correctness cells plus20 pairs. | error_review.csv,raw annotations,category counts. |
| INPUT384 | Core3 x3,max_length384 to contextualize GraphCodeBERT code budget. | input_budget_controls.csv. |

`A4 degree normalization`: replace each M[i,j] by M[i,j]/sqrt(max(1,row_degree_i)) for both fixed/adaptive; retain no-self/special/pad rules. `A4 DFG symmetry`: union graph with its transpose, OR deduplicate; unchanged AST.

`A6 sharing`: head-shared retains layer/relation indices; layer-shared retains head/relation indices; relation-shared retains layer/head indices. Tie only gate W/b and retain all independently learned beta values. Frozen-beta condition retains untied original gates and excludes beta from optimizer at.10. All initialize effective coefficients.05. Record parameter reductions. No test-time superiority/necessity claim for these development-only ablations; a test extension requires a pre-test protocol amendment and three seeds per condition.

`A2 training mean`: fit layer/head/relation means in eval mode on a fixed10k training-ID hash sample after fitting. `A2 function mean`: average eligible query gates per relation/head/layer and broadcast. `A2 permutation`: permute eligible BPE query gates within function/layer/head/relation and projected token-degree bins{1,2-4,5-16,17+}; deterministic Fisher-Yates with a hash of corruption seed/sample/layer/head/relation, count singleton/ineligible groups. Preserve the gate multiset per bin exactly; this token-level intervention may separate subword pieces. Use five corruption seeds for permutation only; deterministic clamps need one inference each. Gates for zero-degree rows never appear in claimed usage statistics.

`A3 swaps`: lexical directed edges(a,b),(c,d)->(a,d),(c,b),reject self/duplicate/ineligible endpoints and any changed edge-distance bin{1-4,5-16,17-64,65+ lexical positions}. AST undirected swap preserves symmetry. Freeze per-sample/relation graph using hash seed1001. Stop at10*edge_count successful swaps or100*edge_count attempts; log achieved rate. Preserve lexical degrees; projected BPE degrees may differ and must be measured. Apply the same frozen rewiring in train/tune/cal/test for A3.

`E7 deletion`: nested hash-ranked lexical-edge groups at requested fraction;rate1 removes all. `E7 swaps`: attempt requested fraction of original edges under A3 constraints, log actual touched fraction and rejections; never claim rate1 is unconstrained randomization. Source tokens unchanged, threshold unchanged, same corruptions for all models. Corrupting an already empty graph is a no-op. Compute trapezoidal area of AP over actual recorded corruption rates; for cross-model comparison use shared realized graphs/rates. Aggregate repeats before testing.

Achieved corruption means fraction of original lexical edges absent in final graph,not just ever touched;AST undirected pairs count once. For each requested swap rate,restart clean with the same seeded proposal stream;stop upon achieved fraction>=target or100*edge_count attempts. Log overshoot/unattained targets. Curve x is edge-count-weighted achieved fraction across the evaluation cohort;identical graphs give identical x for all compared models. Deduplicate repeated x and integrate only the common achieved range,no extrapolation to1. Zero-edge cohorts have no robustness-area claim. A2 interventions recompute gates from the current intervention forward's hidden states at each layer before clamping/permuting;do not reuse clean-run hidden states silently.

E10 bins: original BPE length<=128,129-256,257-510,>510; successful-empty/failed/nonempty graph status; lexical degree bins; DFG span quartile boundaries fitted on training only. Fully visible subset is original BPE<=510; no test-fitted boundaries. Plot counts and null metrics for inadequate slices.

E12 records source, decisions, visible patch/extraction status and blinded annotation categories:truncation,missing structure,unsupported context/alias/call,lexical shortcut,wrong relation,label ambiguity,threshold tradeoff,both confidently wrong,unresolved. Two human reviewers preferred; record if only one/no human review is available. Never fabricate annotations or inter-rater agreement. Flag disputed labels but retain benchmark labels. Examples in the paper selected by fixed hash within categories, including losses.

### 12.1 Finite scheduling and job counts

Generate the complete dependency manifest before test unlock. Planned upper bound before optional baselines and official-split sensitivity:

```text
E1 final                         30 jobs
E1 HPO (8 x [4 proxy+2 full])    48
A1 final                         9
A1 HPO                          18
A3 final                         6
E2 added final                   6
A5 at most                       9
E4 new fractions                27
E3 proxy+final                   8
A4 proxy                         8
A6 proxy                         4
E4 fixed-step diagnostics        3
INPUT384                         9
E10b                             6
E11                              9
TOTAL upper bound              200 training jobs
```

Approximate full-run equivalents128.8 under5epochs/full P_clean; the main final+HPO protected tier is78 jobs/50.8 equivalents. Reusing identical seed42/HPO/A5 runs reduces jobs, recorded explicitly. Inference sweeps are additional tasks, not training jobs. Optional ReGVD/Devign/UniXcoder or additional datasets get separate budgets; no unbounded Cartesian search. If budget only covers protected tier, report restricted claims and unrun mechanism tests, not a full causal claim.

Launcher state machine: planned -> queued -> running -> complete, or failed/blocked/omitted; all transitions append events. Each job lists dependencies,estimated hours,host requirements,max retries and claim IDs. Retry hardware interruption from checkpoint; do not reroll a scientific seed. Concurrent hosts claim exclusive manifest tasks through a single coordinator or disjoint exported job manifests; no shared training process writing one run directory. Verify artifact hashes after transfer.

## 13. Stage gates and test access

1. **Sources/resources/data:** actual source hashes, schemas, counts, licenses and GPU profiles; immutable split manifests. Block on unexplained missing IDs or wrong releases.
2. **Extraction/tests:** independent gold fixtures, no systematic byte/span mistakes in50 train-only samples (25 C/25 C++ where available); AST nonempty>=89% of nonempty<=510BPE training slice (revision R1; originally 90%); DFG supported>=60%; on30 manually annotated supported functions edge precision>=.90 and recall>=.80 against defined limited semantics. If gates fail, fix extractor/version caches before expensive runs. An infeasible DFG scope requires explicit pre-test protocol revision, not silently removing DFG from claims.
3. **Baseline sanity:** train overfits a balanced32-example training fixture to>=95% accuracy; AP prior behavior, labels and class weights correct; external status known. Low validation AP by itself is not a bug.
4. **Adaptive sanity/HPO:** finite nonzero gradients, matched initialization/zero-bias tests pass,no leak/OOM growth,measured per-run budget; complete fixed HPO.
5. **Freeze:** save protocol,selected configs,experiment list,seed lists,source/split/cache hashes,metric version,threshold procedure and planned claims. `test_unlock.json` records these hashes; evaluation refuses mismatch. This is a machine-enforced protocol action, not a new request for user permission.
6. **Final fitting:** finish required seeds, preserve failures; never select favorable seeds. Complete precommitted core even if validation mechanism gain is null; trim only optional scope by budget.
7. **Evaluation:** locked clean/paired/corruption/transfer predictions; no retuning. A discovered evaluator bug invalidates all affected outputs and triggers global corrected regeneration with incident log.
8. **Audit:** generated tables match predictions/configs; claims satisfy evidence rules. Missing results remain marked missing. Exploratory post-test ideas are labeled and cannot replace primary experiments.

## 14. Required tests

**Data/splits:** source checksum/schema validation;stable IDs;invalid-record quarantine;exact/near-clone example and nonclone;strings containing spaces;commit/CVE/pair component unions;missing metadata not grouping unrelated rows;primary test unchanged;no train/tune/cal/test component leaks in derived views;fixed hash partition;fractions nested;cache invalidation;no label-derived features;TF-IDF/class weights trained only on train.

**Parsing/alignment:** C/C++ syntax and grammar selection;AST leaf distances;anonymous terminals/comments;shadowed bindings;parameters;declarations/assignments;RHS use-before-def;branches;loop fixed point;break/continue/return;compound update;unsupported-control failure;global reads;pointer/array/member limits;UTF-8 multibyte/CRLF/leading-space offsets;BPE identifier pieces;partially truncated leaves;special/pad exclusion;empty source;prefix-only information boundary. Independently authored expected graphs, not snapshots created by the tested extractor.

**Model release blockers:**

- Upstream sequence versus structural model at identical weights and zero beta:eval/dropout-off,FP32;logits and all hidden layers. CPU atol1e-6,rtol1e-5;GPU FP32 atol1e-5,rtol1e-4. Mixed precision gets a separate measured tolerance and cannot relax FP32 tests.
- Fixed/adaptive identical at matched initialization (beta_fixed.05,beta_adaptive.10,g.5).
- Shapes,finite scores/gates in[0,1],signed beta behavior,no hard graph mask,nonedge attention remains nonzero where expected.
- Constant relation row cancels under softmax;directed DFG orientation changes only intended bias entries.
- Nonzero finite beta/gate gradients at nonzero initialization;zero-beta gate-gradient limitation documented.
- Empty graphs equal same-weights zero-bias forward;pad batching invariance;edge order/dedup invariance;train dropout reproducibility;eval dropout disabled;rate1 deletion equals own zero-bias model.
- Adapter placement,linear/function controls,checkpoint save/load and exact interrupted-versus-uninterrupted tiny-run resume where determinism supports it.

**Metrics/statistics:** AP ties and known hand-calculated example;all-negative prior;single-class null;threshold inequalities,ties and+infinity;calibration-only API;official VD-S parity and namespace isolation;pair ties and four outcomes sum1;incomplete pair reporting;clustered paired bootstrap preserving members;seed aggregation without ensembling;table provenance join guards.

**System:** run IDs never overwritten;partial writes atomic;stale cache rejected;checkpoint config mismatch refused;launcher no duplicate claims;source code never executed; test unlock protocol-hash checks;unavailable external baseline has status not dummy output.

Smoke test: synthetic fixtures plus deterministic public training-only subset, split locally into smoke train/valid/test. Never use official test data for development smoke. Run import/acquisition -> parse -> relations -> alignment -> loaders -> a few sequence/fixed/adaptive training batches -> thresholds -> inference -> common metrics -> predictions -> gate summary -> one table/plot. CPU smoke can use a tiny randomly initialized RoBERTa-shaped model, explicitly marked plumbing-only; full CodeBERT equivalence integration test remains required separately.

## 15. Checkpointing, provenance and artifacts

Run ID combines UTC time,canonical config hash,seed and uniqueness suffix. Refuse an existing directory except explicit verified resume. Each run contains:

```text
config.resolved.yaml   provenance.json   command.txt
environment.json      sources.lock.snapshot.json
split_manifest.ref    preprocessing_manifest.ref
events.jsonl          train_log.jsonl   validation_history.parquet
checkpoints/best.safetensors
checkpoints/last_resume.pt
checkpoint_selection.json
calibration_predictions.parquet   thresholds.json
predictions/<view_condition>.parquet
metrics/<view_condition>.json
analysis/{gates,interventions,timing}/
status.json           artifact_checksums.json
```

Provenance: code git commit+dirty diff hash,or source archive hash if not git;Python/package lock,Torch/Transformers/CUDA/driver/GPU;hostname/hardware profile;all seeds/RNG algorithm;data/source/view/cache hashes;HPO parents;input lengths;class weights/counts;precision/backend;checkpoint/config hashes;actual steps/examples/wall time/peak memory. Never fabricate a git commit for an unversioned directory.

Resume checkpoint includes model,optimizer,scheduler,scaler,Python/NumPy/Torch CPU/CUDA RNG,augmentation RNG,sampler order/position,epoch/step,best metric,patience and partial accumulation state (or checkpoint only at optimizer-step boundary). Saving at optimizer boundaries is preferred. Keep one best weights and last resume state;archive/delete resumable states only under explicit retention policy after verified best/prediction backups. Never delete the only artifact needed for a reported result.

Preprocessing failure JSONL:sample_id,dataset,stage,exception/reason,source length,language,cache version. Training/adapter failure events:traceback,config,seed,resource state,partial artifacts. Preserve NaN/failure runs in summaries. Never substitute guessed metrics for missing outputs.

## 16. Efficiency and resource planning

On each ~46GB host, benchmark100 warmed training steps for sequence/fixed/adaptive at microbatch4,512tokens,effectivebatch32;record throughput,peak memory and I/O. Reserve>=4GB measured VRAM headroom. BF16 if supported;otherwise recorded FP16+scaler/FP32. Activation checkpointing allowed consistently. Do not infer speed from VRAM capacity.

Planning numbers, replace with measurements:~125M encoder parameters;~0.5GB float32 weights;~1.5-2.5GB resumable checkpoint;12-30GB microbatch4 BF16 memory,possibly20-40+GB with inefficient attention. One `[4,12,512,512]`FP32 score tensor~48MiB;two Boolean relation masks~2MiB. Dense disk relations forbidden. Sparse source/features across primary+secondary may occupy10-50GB plus1-10GB raw data;full campaign archive300-700GB,working storage100GB/host. Pilot actual edge volume before extrapolating.

Time estimator: `epochs * actual_N_train / measured_examples_per_second / 3600 + measured_eval_io_hours`. Illustrative20-100functions/sec ->3-15GPUh/full5epoch run. Full128.8 equivalents~385-1935GPUh plus10-20% inference/analysis;protected50.8 equivalents~150-760GPUh. Two fully available resources reduce wall time;actual access schedule controls completion. Cost report uses actual billing rate supplied by user,not guessed cloud pricing.

E8 benchmark: fixed1000 test IDs chosen by hash and predeclared length strata,label-independent;one fixed host;batch1 and16;warmup50batches,timing200batches x3repeats;CUDA synchronize before/after measured segments;record model-only,transfer,extraction cold/warm and uncached end-to-end. Report mean/median/p95,throughput,peak allocated/reserved VRAM,CPU RSS,parameters,disk size. Same eager backend for controlled overhead;also optimized sequence-only backend for practical comparison. Document padding/precision/cache and exclude warmup. Do not compare pooled timings from dissimilar hosts.

## 17. Analysis, aggregation and paper output

Gate analysis:eligible queries with degree>0;g mean/median/std,saturation<.05/>.95;beta,signed beta*g;pre-attention-dropout edge mass `sum_j A_ij M_r[i,j]`;training gradient norms. Keep zero-degree/unmapped counts. Relation masses overlap and need not sum1. Local zero-bias attention recomputes softmax from the same layer Q/K;full-forward zero-relation intervention is separate. Do not describe g as probability an edge is correct.

Stream full-data summaries,save detailed tokens/heads for fixed<=2000 hashed test IDs. CWE plots:up to10CWEs selected by highest training positive support,never test performance;adequate-count gates,overlap caveat. Stratify label/correctness comparisons by length and degree. Save underlying raw tables before plotting. Full attention tensors for every test sample are unnecessary.

Aggregator verifies prediction completeness,labels/IDs,split/config hashes,seed sets,threshold provenance and metric version. Recompute metrics from saved predictions;generate CSV,Markdown,LaTeX tables and PDF/SVG/PNG figures. Each cell includes source run IDs/checkpoint/prediction hashes via a companion provenance map. Development-only results and unavailable/failed baselines remain separated. No handwritten numeric table entries.

Required outputs:

- T1:data versions,counts/prevalence,exclusions,duplicates,pairs,extraction coverage.
- T2:main AP/seed uncertainty and calibrated recall/FPR,F1/MCC;oracle VD-S separate.
- T3:relation/mechanism/shared-recipe/input-budget/visibility ablations and params/cost.
- T4:pair order,margins and PC/PV/PB/PR at both thresholds.
- T5:decontaminated DiverseVul and held-out-project results with cohort composition.
- T6:measured training/inference/preprocessing/memory/parameter cost.
- F1:architecture/score formula;F2:data/compute curves;F3:PR and pair margins;F4:gate/effective/intervention plots;F5:corruption curves;F6:length/span/coverage failures.

Claim guards in report generation:adaptivity requires primary gain over fixed;structure-only gain cannot substitute. Mechanism attribution requires A1/A2/A3,not just gate plots. Low-FPR claim requires achieved test compliance and recall improvement. Dropout tradeoff requires clean AP loss<=.01 and favorable corruption-area difference. Pair-order gain doesn't imply PC gain. Transfer requires frozen decontaminated cohort. “Modest overhead” requires measured batch1 end-to-end median and peak VRAM<=1.25x sequence on the same host. No SOTA,first-ever,semantic-understanding or security-guarantee claims are generated.

## 18. CLI contracts

Implement runnable interfaces equivalent to these;the following are intended commands,not claims they currently exist:

```text
python -m pip install -e .
python scripts/benchmark_hardware.py --output artifacts/environment/ssh.json
python -m astguard.data.download --dataset primevul --release original
python -m astguard.data.download --dataset diversevul
python -m astguard.data.audit --config configs/base.yaml
python -m astguard.data.splits --protocol protocol/protocol_v1.json --freeze
python -m astguard.data.preprocess --dataset primevul --view P_clean
python scripts/run_smoke_test.py
python scripts/run_baselines.py --baselines graphcodebert_c_adapted linevul_function --stage smoke
python scripts/run_experiment_suite.py --manifest protocol/experiment_manifest.jsonl --stage development
python scripts/freeze_protocol.py --manifest protocol/experiment_manifest.jsonl
python scripts/run_experiment_suite.py --manifest protocol/experiment_manifest.jsonl --stage final_train --host ssh
python -m astguard.train --config configs/models/astguard.yaml --seed 42
python -m astguard.evaluate --run runs/RUN_ID --fit-thresholds --split cal
python -m astguard.evaluate --run runs/RUN_ID --split test --require-protocol-lock
python -m astguard.analysis --run runs/RUN_ID --analyses gates pairs
python scripts/run_experiment_suite.py --manifest protocol/experiment_manifest.jsonl --stage evaluation
python scripts/reproduce_tables.py --manifest protocol/experiment_manifest.jsonl
python scripts/verify_results.py --manifest protocol/experiment_manifest.jsonl
pytest
```

CLI model configs inherit base settings and must resolve all required fields;never run an unresolved snippet. Provide `--dry-run` to show finite jobs/budgets,`--resume` with exact validation,`--manual-path` for public data import and actionable dependency/download errors. No command may turn missing runs into fabricated metrics.

## 19. Implementation order and handoff acceptance

1. Inspect environment/repository;pin sources and suitable dependencies;write resource profiles.
2. Build normalized records,audits,components,views and immutable manifests before modeling.
3. Implement lexical/C/C++ scopes/CFG/relations/alignment with independent gold tests and coverage report.
4. Implement sparse cache/collator and sequence classifier/trainer;validate tiny learnability.
5. Implement fixed relations,adaptive gate,dropout and controls;pass equivalence/gradient tests.
6. Implement metrics,calibration,pairs,statistics,provenance,checkpoints and smoke pipeline.
7. Integrate valid external baselines;record availability and input-budget differences.
8. Generate finite experiment ledger;profile;complete budgeted development HPO and diagnostics.
9. Freeze protocol and settings;run all protected seeds,then prioritized mechanism/generalization training.
10. Evaluate once under locked rules;run paired/intervention/robustness/transfer/failure analyses.
11. Aggregate,generate tables/figures and independently verify every claimed result from predictions.

Final implementation report must state actual acquisition/version/coverage,model/baseline status,tests/smoke results,measured resource use,completed run IDs,missing/failed experiments,deviations,remaining limitations and exact reproduction commands. Distinguish a pipeline that works from a scientific hypothesis that succeeds. Do not claim unrun results,complete data independence,or bitwise reproduction on untested hardware.
