# Implementation notes and protocol deviations

## 2026-09-23 fresh-clone verification

- A clean clone was recreated on Python 3.11.9. The current 59-test suite, packaging build, dependency check, deterministic plumbing smoke, training-only neural smoke, and pinned CodeBERT zero-bias equivalence all pass on CPU.
- Fresh-clone source restoration now consumes the revisions and checksums already recorded in `sources.lock.json`. The CodeXGLUE/Devign training-only smoke fixture is registered there, and registered PrimeVul/DiverseVul payloads can be reacquired when their ignored local files are absent.
- This verification does not change scientific status: all 200 registered jobs remain missing, the protocol remains unfrozen, the test lock remains locked, the 86.8% AST coverage result still fails the 90% gate, and manual edge review remains pending.

## 2026-09-23 verified local state

- Environment: Python 3.11.16 and research dependencies are installed in `.venv`; the current suite has 57 passing tests. PyTorch is CPU-only, no Git executable is available, and this host cannot validate the specified ~46 GB GPU training/throughput. The local source-archive identity is used when Git is absent. No cross-GPU determinism claim is made.
- Data: exact original PrimeVul six-file release and standalone DiverseVul were checksum-registered. PrimeVul normalized 235,768 rows (6,968 positives; zero quarantine), including 5,077 unambiguous and 373 ambiguous official pair groups. DiverseVul normalized 330,492 rows (18,945 positives; zero quarantine). A complete exact/near-clone audit and frozen P_clean/P_project/D_transfer manifests have **not** been run on the combined population; full-cohort memory/runtime remains unverified.
- Checkpoint/source: the pinned original CodeBERT and GraphCodeBERT checkpoints/tokenizers and upstream CodeBERT/GraphCodeBERT, LineVul, ReGVD, PrimeVul, and CodeXGLUE source revisions are local. FP32 zero-bias equivalence passed every CodeBERT backbone hidden layer and logits (`artifacts/audits/pretrained_equivalence.json`). Pretraining contamination cannot be ruled out.
- Smoke: a public CodeXGLUE training-only neural smoke exercised Tree-sitter extraction, byte/BPE projection, sequence/fixed/adaptive Transformer forwards, gradients, checkpointing, tune/cal thresholding, predictions, aggregation, table and figure generation. It used a tiny randomly initialized RoBERTa-shaped backbone and is **not** a PrimeVul performance result.
- Registered work: `protocol/experiment_manifest.jsonl` contains 200 jobs and a dependency-aware launcher; no registered full job or official-test inference has completed. The test lock remains locked.

## Extraction coverage gate: failed, not revised

- Original requirement: nonempty AST token relation on at least 90% of nonempty train-only functions at most 510 BPE; DFG supported on at least 60% of that slice; manually annotated projected-edge precision at least 0.90 and recall at least 0.80 on 30 supported functions.
- Problem: the deterministic 500-function train-only pilot reports AST nonempty 0.868, DFG supported 0.724 (`artifacts/audits/extraction_pilot_500.json`). The smaller 50-function pilot reported AST 0.82, DFG 0.64. Parser failures include incomplete function fragments and project-specific macros. The protocol disallows a synthetic wrapper or silently retaining error-containing trees in the primary extractor. Manual edge-quality review has not been done.
- Change: no scientific gate was lowered and no official test access was unlocked. Rows with failed parsing retain empty relations and status; the registered model design remains intact. If parser improvements cannot pass the gate, the specified AST-only scoped revision requires an explicit pre-test freeze and may not answer the original AST+DFG question.
- Scientific impact: no confirmatory ASTGuard+DFG result is currently authorized; engineering tests and smoke scores cannot fill this gap.

## Baseline availability

- Original requirement: same-setting TF-IDF/prior, GraphCodeBERT C/C++ adaptation, LineVul function adapter, preferred ReGVD, optional faithful Devign/UniXcoder.
- Problem: GraphCodeBERT, LineVul, and ReGVD model paths are integrated and unit tested, but their full registered train/evaluate runs have not been executed. A faithful Devign rich-graph environment is not integrated. `run_baselines.py` writes honest integration status entries; neural methods train through the common runner and classical methods through `run_classical_baselines.py`.
- Change: the official ReGVD source was pinned and its ReGCN graph/readout was adapted to the common training contract. Unavailable methods are not substituted by generic architectures or published scores. Devign remains optional/unavailable with an explicit reason.
- Scientific impact: external breadth/SOTA claims are unavailable. Controlled same-backbone comparisons remain the primary planned inference once release gates pass.

## Split, preprocessing, and runner limitations

- Original requirement: full exact/near-clone leakage audit, P_clean/P_project/D_transfer freeze, visible-prefix structural sensitivity, and all 200 reproducible experiment jobs.
- Problem: the full clone join and feature cohort registry have not been executed; full-cohort audit runtime and memory on 566,260 combined records remain unverified. PrimeVul/DiverseVul provide a `project` name, not a canonical repository URL; the adapter preserves it as supplied project identity but no alias map is proven. The launcher requires a context with frozen feature cohorts and cannot run scientifically before those exist.
- Change: the CLI accepts multiple source files for a joint transfer audit, D_transfer excludes components touching any PrimeVul split, P_project uses supplied project identity, and preprocessing/joining stream records. Candidate clone pairs are no longer retained globally. Complete-statement-only visible-prefix DFG extraction is implemented and information-boundary tested. A3/E7 rewiring is deterministic with measured achieved rates; impossible rewiring is reported, not silently deemed successful. The official test lock remains enforced.
- Engineering: preprocessing has a content-addressed cache and failure ledger; feature registry construction reuses it. Training, evaluation, and inference sweeps validate and index JSONL once and load feature rows lazily. Token-only models avoid dense structural-mask allocation. Atomic best/resume checkpoints, exact optimizer-step resume tests, and measured preprocessing/inference/training benchmark utilities are present.
- Scientific impact: P_project and D_transfer analyses are not yet independently verified on full data; E10b is not confirmed. Do not interpret any currently generated smoke metrics as transfer or project-generalization results.

## Documentation and result policy

Source and environment version claims above are local, not claims of full experimental completion. `README.md` lists runnable setup, smoke, split, preprocess, training, launcher, evaluation and aggregation commands. Every paper number must originate from stored predictions and the frozen protocol. A pipeline run is not a hypothesis result, and an unavailable comparison stays unavailable.
