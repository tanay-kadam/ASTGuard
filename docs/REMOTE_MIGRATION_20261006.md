# SSH-to-local migration record (2026-10-06)

## Outcome

The remote project at `/home/tkadam/ASTGuard` was copied, audited, and then
permanently deleted at the user's request. The transfer staging files created
under `/tmp` were also deleted. A final remote check reported all of these paths
absent.

The older, separate directory
`/home/tkadam/ASTGuard_untracked_backup_20261001` was deliberately retained. It
contains 312 KB of pre-shuffle configs, scripts, diagnostics, and fixtures. Its
current equivalents or explicit `.bak_pre_shuffle` copies were present in the
audited project snapshot; it was outside the deletion target.

## Source-code reconciliation

- Remote Git HEAD: `e1bd9336236d9ccaa584af1b8eb995e1c6c5f6af`
- Local Git HEAD before this migration: `c97dd0623c491c2ccbda430d7130f454c7912199`
- The remote HEAD is an ancestor of the local HEAD.
- A complete remote source/config/docs/scripts/tests snapshot, excluding generated
  data, run outputs, artifacts, `.git`, and `.venv`, was downloaded and compared
  with the local tree.
- Current source/config/test files had no semantic content difference. Differences
  were generated `*.pyc`, line endings, and obsolete `.bak_pre_shuffle` copies.
- The remote source archive matched locally and remotely at SHA-256
  `399da3e78a6dae2fc0cbf942172c85663501c515684efd7cb6a6d5abe417f7e`.
- The remote stash `pre-shuffle-preprocess` changed
  `write_jsonl(args.output, features)` to `features()`. The corrected `features()`
  call was already present in both the current remote HEAD and local source, so no
  missing stash change remained to apply.

## Artifact transfer and verification

The complete final `artifacts/` tree was copied after all intervention jobs had
finished.

- Remote artifact files: 176
- SHA-256 mismatches after local copy: 0
- Final intervention reports: three JSON files, each with 10,566 tune examples
- Intervention report SHA-256:
  - seed 42: `92d6beae3b621c950e151bb6a629cb474c6fe203a1b78cf6ad86985f080c89e9`
  - seed 123: `f3fa3b32602fc3f910b258c15978f624b63436118de7a472173837a15d652db4`
  - seed 456: `1e31d814fda6ee45f640a47ceb20ae22083712977da4a7ffef40fb07c051aace`

The local paper-number audit recomputed AP from raw predictions for all nine
null-centered-campaign runs and all three final intervention reports. Every value
matched its saved report within absolute tolerance `1e-12`; all scores were
finite; the official test role was not used.

## Run transfer and verification

All 38 completed remote run directories were preserved under local `runs/`. The
portable archive includes resolved configs, commands, environments, provenance,
source locks, feature/split references, training logs, validation histories,
checkpoint-selection records, diagnostics/predictions where originally retained,
and all 38 selected `.safetensors` checkpoints.

Archive checksums matched the remote archives exactly:

- part 0, 4,996,280,320 bytes:
  `4951153adaa5495392ec0116a4ad81b8316fc10dd8a1368914377e1ce6e0612d`
- part 1, 5,002,833,920 bytes:
  `68adef44e0fb2865da5c36f714d37047fadc82215f6f30c08e0aca0cf3f2ca5d`
- part 2, 4,501,391,360 bytes:
  `4df32a26a5ecf283e9af944e82c061c89291024597118caa1f5c97ea291fadc0`
- part 3, 4,497,612,800 bytes:
  `3718dc6acf1f2e288970c0b04e7e2792677f1b9ba67f2b4018839b67c4746bef`

After extraction, 522 preserved files were independently rehashed against their
per-run `artifact_checksums.json` entries with zero mismatches. The 38 excluded
entries were the intentionally omitted `*.pt` optimizer/resume states.

## Deliberate exclusions

These were not copied into the repository because they are inputs, environments,
or transient restart state rather than evidentiary outputs:

- remote `data/`: approximately 196.8 GB; dataset manifests, feature hashes, and
  construction code are preserved;
- remote `.venv/`: approximately 9.4 GB; dependency locks and environment records
  are preserved;
- 38 `*.pt` optimizer/resume files: approximately 57.0 GB; every selected model
  checkpoint is preserved as `.safetensors`;
- remote `.git/`: local Git already contains the remote HEAD and subsequent local
  commits.

## Local deliverables

- Master numerical manuscript: `paper/ASTGUARD_NEGATIVE_RESULTS_DRAFT.md`
- Venue strategy: `paper/SUBMISSION_STRATEGY.md`
- Updated novelty audit: `docs/GRAPH_RELIANCE_FRAMEWORK_NOVELTY_AUDIT.md`
- Recomputed metric audit: `artifacts/audits/paper_number_audit_20261005.json`
- Recalculation script: `scripts/audit_paper_numbers.py`
- Complete preserved runs: `runs/` (ignored by Git because of their size)
- Paper-grade audit artifacts: `artifacts/`

## Local verification

- `tests/unit/test_graph_donors.py`, `test_null_graphs.py`,
  `test_null_centered.py`, and `test_metrics.py`: 14 passed.
- `scripts/audit_paper_numbers.py`: compiled successfully and completed with
  `all_run_ap_match_within_1e-12=true`, `all_run_scores_finite=true`, and
  `all_intervention_ap_match_within_1e-12=true`.
- The manuscript contains no unfinished result placeholder; its final intervention
  table is populated from the verified per-example reports.

## Remote deletion verification

The validated deletion target resolved exactly to `/home/tkadam/ASTGuard`, was
owned by `tkadam`, and had no running project process or tmux session. Immediately
before deletion its size was 282,259,364,216 bytes. After deletion, the following
paths were confirmed absent:

- `/home/tkadam/ASTGuard`
- `/tmp/astguard_transfer_20261005`
- `/tmp/astguard_code_20261005.tar.gz`
- `/tmp/astguard_run_metadata_20261005.tar.gz`
- `/tmp/astguard_artifacts_manifest_20261005.sha256`
- `/tmp/make_run_archives.sh`
