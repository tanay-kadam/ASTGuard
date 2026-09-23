# ASTGuard

ASTGuard tests whether token-conditioned AST and approximate data-dependency attention biases improve function-level C/C++ vulnerability detection over a matched CodeBERT backbone. `IMPLEMENTATION_SPEC.md` is the protocol; software execution is not evidence that the hypothesis succeeds.

## Verified local status (2026-09-23)

On the original development host, Python 3.11.16, the research dependencies, and a tested environment lock were installed. Original PrimeVul (235,768 rows), standalone DiverseVul (330,492 rows), pinned CodeBERT and GraphCodeBERT checkpoints, and upstream baseline source files were acquired there with checksums in `sources.lock.json`; ignored raw data and checkpoints are not included in a fresh clone. The current 59-test suite passes on Python 3.11, upstream zero-bias CodeBERT equivalence passes, and both plumbing and neural training-only smoke pipelines produce checkpoints, predictions, tables, and figures. None of the 200 registered full jobs or official-test evaluations has run. The official test remains locked. Pre-test revision R1 (`protocol/revisions/R1_annotation_masking.md`) masks a fixed list of annotation macros for extraction only and sets the AST coverage gate to 89%: train-only AST coverage is 89.8% on both the registered 500-function pilot and a disjoint held-out sample (86.8% before R1), and DFG support is 74.4%/72.6% against its 60% gate. Manual dependency-edge quality review is still pending. See `IMPLEMENTATION_NOTES.md`.

## Environment

Use Python 3.11 and a machine with the required GPU capacity for full jobs. On Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[research,test]"
.venv\Scripts\python.exe scripts\resolve_environment.py --output requirements.lock
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

The original development workspace also contained a local Python in `.python/`; ignored environments are not part of a clone. CUDA was not available on that machine; the release-gate host (NVIDIA RTX 6000 Ada, 48 GB) is profiled in `artifacts/environment/local_rtx6000ada.json`. `requirements.lock` records the tested local environment, not a cross-platform bitwise guarantee.

Restore the checksum-locked development fixture and pinned checkpoint/tokenizer files before running the neural smoke and pretrained-equivalence checks. Omit `--weights` if only the tokenizer-backed neural smoke is needed.

```powershell
.venv\Scripts\python.exe scripts\acquire_development_sources.py --weights
```

## Data and release gates

```powershell
.venv\Scripts\python.exe -m astguard.data.download --dataset primevul
.venv\Scripts\python.exe -m astguard.data.download --dataset diversevul
.venv\Scripts\python.exe -m astguard.data.normalize
.venv\Scripts\python.exe -m astguard.data.normalize_diversevul
.venv\Scripts\python.exe scripts\audit_extraction.py --count 500 --output artifacts\audits\extraction_pilot_500.json
```

The manual edge-review pack and the baseline-overfit fixture are drawn from the P_clean train role in fixed hash order, so only that prefix needs preprocessing. Reviewers annotate the blind worksheets in `artifacts/audits/manual_review/` and fill a copy of `gold_template.json` as `gold.json`; `import` refuses incomplete or invalid edges.

```powershell
.venv\Scripts\python.exe scripts\prepare_release_subsets.py --checkpoint data\raw\checkpoints\codebert\3b0952feddeffad0063f274080e3c23d75e7eb39
.venv\Scripts\python.exe scripts\manual_extraction_audit.py prepare --records data\interim\primevul\records.jsonl --features data\processed\release_subsets\review_features.jsonl --manifest artifacts\audits\P_clean.json --output artifacts\audits\manual_extraction_pack.jsonl
.venv\Scripts\python.exe scripts\manual_extraction_audit.py worksheet --pack artifacts\audits\manual_extraction_pack.jsonl --output-dir artifacts\audits\manual_review
.venv\Scripts\python.exe scripts\manual_extraction_audit.py import --pack artifacts\audits\manual_extraction_pack.jsonl --features data\processed\release_subsets\review_features.jsonl --gold artifacts\audits\manual_review\gold.json --output artifacts\audits\manual_extraction_pack.reviewed.jsonl
.venv\Scripts\python.exe scripts\manual_extraction_audit.py evaluate --pack artifacts\audits\manual_extraction_pack.reviewed.jsonl --output artifacts\audits\manual_extraction_gold.json
```

Other release gates (per-host resolved configs live under `artifacts/release_gates/configs/`):

```powershell
.venv\Scripts\python.exe scripts\validate_frozen_data.py --records data\interim\primevul\records.jsonl data\interim\diversevul\records.jsonl --p-clean artifacts\audits\P_clean.json --p-project artifacts\audits\P_project.json --d-transfer artifacts\audits\D_transfer.json --output artifacts\release_gates\data_integrity.json
.venv\Scripts\python.exe scripts\check_baseline_overfit.py --config artifacts\release_gates\configs\astguard.json --features data\processed\release_subsets\overfit_train.jsonl --output artifacts\release_gates\overfit_astguard.json
.venv\Scripts\python.exe scripts\combine_overfit_gate.py --result artifacts\release_gates\overfit_sequence_only.json --result artifacts\release_gates\overfit_ast_dfg_fixed.json --result artifacts\release_gates\overfit_astguard.json --output artifacts\release_gates\baseline_overfit.json
.venv\Scripts\python.exe scripts\warm_feature_cache.py --plan artifacts\release_gates\registry_plan.json --variants 0
.venv\Scripts\python.exe scripts\prepare_feature_registry.py --plan artifacts\release_gates\registry_plan.json
```

After final predictions exist, the R1 secondary parse-status subgroup analysis uses the same plan format as `statistical_comparisons.py`:

```powershell
.venv\Scripts\python.exe scripts\subgroup_analysis.py --plan PLAN.json --features FEATURES.jsonl --output artifacts\analysis\parse_status_subgroups.json
```

The acquisition commands validate registered checksums on repeat runs. Raw releases stay in `data/raw/`; normalized JSONL/Parquet and quarantine reports are in `data/interim/`. A full clone audit is potentially compute/memory intensive and has **not** been completed here. To build the source split on a capable host:

```powershell
.venv\Scripts\python.exe -m astguard.data.audit --records data\interim\primevul\records.jsonl --output artifacts\audits\prime_components.json
.venv\Scripts\python.exe -m astguard.data.splits --records data\interim\primevul\records.jsonl --components artifacts\audits\prime_components.json --view P_clean --output artifacts\audits\P_clean.json
.venv\Scripts\python.exe -m astguard.data.splits --records data\interim\primevul\records.jsonl --components artifacts\audits\prime_components.json --view P_project --output artifacts\audits\P_project.json
.venv\Scripts\python.exe -m astguard.data.audit --records data\interim\primevul\records.jsonl data\interim\diversevul\records.jsonl --output artifacts\audits\joint_components.json
.venv\Scripts\python.exe -m astguard.data.splits --records data\interim\primevul\records.jsonl data\interim\diversevul\records.jsonl --components artifacts\audits\joint_components.json --view D_transfer --output artifacts\audits\D_transfer.json
```

The transfer split excludes every DiverseVul component linked to *any* PrimeVul split. No target labels may be used to tune or calibrate. A split file is not a release-gate pass by itself.

Preprocess with the pinned local checkpoint (path in `artifacts/environment/development_sources.json`) and join labels only after a frozen split exists:

```powershell
.venv\Scripts\python.exe -m astguard.data.preprocess --records data\interim\primevul\records.jsonl --output data\processed\primevul.features.jsonl --checkpoint data\raw\checkpoints\codebert\3b0952feddeffad0063f274080e3c23d75e7eb39 --cache-root artifacts\cache --failures artifacts\preprocessing_failures\primevul.jsonl
.venv\Scripts\python.exe -m astguard.data.join --records data\interim\primevul\records.jsonl --features data\processed\primevul.features.jsonl --manifest artifacts\audits\P_clean.json --output data\processed\P_clean
```

Variant options on `astguard.data.preprocess` include `--ast-relation anchored_parent_child`, `--dfg-symmetry`, `--structural-context visible_prefix`, and `--topology degree_preserving_rewired`. Each receives a distinct preprocessing hash. Visible-prefix extraction is implemented with complete-statement-only dependency analysis and an information-boundary test; its full-cohort coverage must still be measured before interpretation.

## Smoke, training, and baselines

```powershell
.venv\Scripts\python.exe scripts\run_smoke_test.py
.venv\Scripts\python.exe scripts\run_neural_smoke.py
.venv\Scripts\python.exe scripts\check_pretrained_equivalence.py
.venv\Scripts\python.exe scripts\run_baselines.py --baselines graphcodebert_c_adapted linevul_function regvd devign_gnn --stage smoke
.venv\Scripts\python.exe -m astguard.train --config configs\models\astguard.yaml --features data\processed\P_clean\train.jsonl --tune-features data\processed\P_clean\tune.jsonl
.venv\Scripts\python.exe -m astguard.train --config configs\models\ast_dfg_fixed.yaml --features data\processed\P_clean\train.jsonl --tune-features data\processed\P_clean\tune.jsonl
.venv\Scripts\python.exe -m astguard.train --config configs\models\sequence_only.yaml --features data\processed\P_clean\train.jsonl --tune-features data\processed\P_clean\tune.jsonl
```

The model commands require resolved configs, frozen feature/manifest hashes, and sufficient compute. The smoke scripts use only development data and explicitly do not produce official results. GraphCodeBERT C-adapted, LineVul function, and the pinned official-style ReGVD/ReGCN adapter are runnable. Devign remains explicitly unavailable because a faithful rich-graph pipeline was not established; no generic substitute is reported. `scripts/run_baselines.py` reports integration status, while neural baseline configs train through the common runner. The prior and CodeBERT-budgeted TF-IDF baselines run with:

```powershell
.venv\Scripts\python.exe scripts\run_classical_baselines.py --records data\interim\primevul\records.jsonl --manifest artifacts\audits\P_clean.json --checkpoint data\raw\checkpoints\codebert\3b0952feddeffad0063f274080e3c23d75e7eb39
```

## Registered experiments and results

```powershell
.venv\Scripts\python.exe scripts\run_experiment_suite.py --manifest protocol\experiment_manifest.jsonl --dry-run
.venv\Scripts\python.exe scripts\run_experiment_suite.py --manifest protocol\experiment_manifest.jsonl --stage development_hpo_proxy --context artifacts\launcher\context.json --host GPU_HOST
.venv\Scripts\python.exe scripts\run_experiment_suite.py --manifest protocol\experiment_manifest.jsonl --stage development_hpo_full --context artifacts\launcher\context.json --host GPU_HOST
.venv\Scripts\python.exe scripts\run_experiment_suite.py --manifest protocol\experiment_manifest.jsonl --stage final_train --context artifacts\launcher\context.json --host GPU_HOST
.venv\Scripts\python.exe scripts\verify_results.py --manifest protocol\experiment_manifest.jsonl
```

The launcher requires a context JSON with registered checkpoint revisions, protocol hash, resources, and a feature registry for each split/preprocessing variant. Build it with `scripts/prepare_feature_registry.py --plan PLAN.json`; the plan names the frozen P_clean/P_project/D_transfer manifests and source record files. This full registry has not been generated locally because the combined clone/split audit and extraction gates are incomplete. The launcher resolves dependencies and HPO parents; do not launch official-test jobs or unlock `protocol/test_unlock.json` without all content-addressed stage evidence. `scripts/build_stage_evidence.py --help` and `scripts/freeze_protocol.py --help` describe that boundary.

Preprocessing is content-addressed and resumes from its cache; training/evaluation index JSONL byte offsets instead of retaining all structural features in memory. Before the GPU campaign, measure cold/warm preprocessing and model/end-to-end inference on the target host:

```powershell
.venv\Scripts\python.exe scripts\benchmark_preprocessing.py --records data\interim\primevul\records.jsonl --checkpoint data\raw\checkpoints\codebert\3b0952feddeffad0063f274080e3c23d75e7eb39 --output artifacts\benchmarks\preprocessing.json
.venv\Scripts\python.exe scripts\benchmark_inference.py --config artifacts\launcher\E1-sequence_only-42-final.resolved.yaml --checkpoint runs\RUN_ID\checkpoints\best.safetensors --features data\processed\cohorts\P_clean\CLEAN_KEY\joined\test.jsonl --output artifacts\benchmarks\sequence_inference.json
```

On each GPU host, first record hardware and measure 100 warmed optimizer steps for sequence, fixed, and adaptive resolved configs:

```powershell
.venv\Scripts\python.exe scripts\benchmark_hardware.py --output artifacts\environment\GPU_HOST.json
.venv\Scripts\python.exe scripts\benchmark_training.py --config artifacts\launcher\E1-sequence_only-42-final.resolved.yaml --features data\processed\cohorts\P_clean\CLEAN_KEY\joined\train.jsonl --output artifacts\benchmarks\sequence.json
.venv\Scripts\python.exe scripts\benchmark_training.py --config artifacts\launcher\E1-ast_dfg_fixed-42-final.resolved.yaml --features data\processed\cohorts\P_clean\CLEAN_KEY\joined\train.jsonl --output artifacts\benchmarks\fixed.json
.venv\Scripts\python.exe scripts\benchmark_training.py --config artifacts\launcher\E1-astguard-42-final.resolved.yaml --features data\processed\cohorts\P_clean\CLEAN_KEY\joined\train.jsonl --output artifacts\benchmarks\adaptive.json
```

Evaluation and publication tables are gated on complete predictions and the protocol lock. After a selected run and P_clean feature cohort exist:

```powershell
.venv\Scripts\python.exe -m astguard.evaluate --run runs\RUN_ID --features data\processed\P_clean\cal.jsonl --manifest artifacts\audits\P_clean.json --split cal --fit-thresholds
.venv\Scripts\python.exe -m astguard.evaluate --run runs\RUN_ID --features data\processed\P_clean\test.jsonl --manifest artifacts\audits\P_clean.json --split test --require-protocol-lock
.venv\Scripts\python.exe scripts\reproduce_tables.py --manifest protocol\experiment_manifest.jsonl --predictions runs\RUN_ID\predictions\test.json --output-dir results\tables
.venv\Scripts\python.exe -m astguard.analysis --run runs\RUN_ID --analyses pairs failures --pairs artifacts\audits\official_pairs.jsonl --features data\processed\cohorts\P_clean\CLEAN_KEY\joined\test.jsonl
.venv\Scripts\python.exe scripts\build_pr_pair_rows.py --predictions runs\RUN_ID\predictions\test.json --pairs artifacts\audits\official_pairs.jsonl --output-dir results
.venv\Scripts\python.exe scripts\reproduce_paper_outputs.py --plan configs\paper_outputs.example.json --output-dir results\paper
.venv\Scripts\python.exe scripts\verify_results.py --manifest protocol\experiment_manifest.jsonl --require-complete
```

Outputs live under `data/`, `artifacts/`, `runs/`, and `results/`; large generated files are Git-ignored. `EQUATION_CODE_MAP.md` and `CLAIM_EXPERIMENT_MAP.md` trace mechanisms and claims. DFG edges are a limited intraprocedural approximation, not sound static analysis; pretraining contamination cannot be ruled out.
