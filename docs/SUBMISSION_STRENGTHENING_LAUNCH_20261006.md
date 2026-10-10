# Detached campaign launch record

> Audit update (2026-10-06): scheduling was temporarily held for a null/shuffle composition defect and a CUDA-seed initialization defect. Both were repaired and smoke-tested; the original workers resumed. Six completed attention synthetic runs are preserved in remote quarantine and are being replaced on GPU 3. See `docs/COMPLETE_PAPER_PIPELINE_AUDIT_20261006.md`. The logical valid matrix remains 42 jobs; historical invalid executions are not counted as valid evidence.

Full queue launch: 2026-10-06T21:25:31Z. SSH host: seeklab-01. Project: `/home/tkadam/ASTGuard`.

Session: `astguard_strengthen_20261006`. Campaign directory: `artifacts/release_gates/strengthening_20261006`.

The frozen protocol is `docs/SUBMISSION_STRENGTHENING_PROTOCOL_20261006.md`. Runtime-resolved configs and all 42 jobs are saved under the campaign directory. All 14 family/condition smoke gates passed on CUDA. Both full workers were confirmed active on GPUs 5 and 6. CPU preparation runs with 32 workers, and real/external jobs wait for verified preparation completion. Queues wait when their GPU is occupied; they do not terminate other users' processes. The detached session survives VPN disconnection and PC sleep.

The matrix contains 15 synthetic sensitivity jobs, nine external ReGVD jobs, nine corrected real-data five-epoch attention/control jobs, and nine corrected real-data three-epoch adapter/control jobs. Separate synthetic audit sequences are never used to select a checkpoint. The original real-data test role is not included in the restored development transfer.

Execution records: `started.json`, `smoke_gate.json`, `preparation_full.log`, `jobs/<tag>/status.json`, each job's command log and selected checkpoint, worker completion records, and final `summary.json`/`completion.json`. A failed job remains failed even when unrelated jobs finish. The final summarizer recomputes AP from saved predictions and refuses to mark the campaign complete with missing jobs. Initial ReGVD smoke failure evidence is preserved; the repaired retry passed.

Upload integrity:

- Initial source/protocol bundle SHA256: `9860ae2b29e0efcd4e6fab4a4ead71c9efdf7bcaac1320b4be7b7655abc4bc92`.
- Development-record gzip SHA256: `e29c262c4eb4bbc093d5e449f605e5280c4f53ea735569654ba02389f0ef1a92`.
- Both matched the remote uploads before extraction. Small smoke-discovered fixes were then transferred separately and tested; per-run source identity and command/config records identify actual execution.

Local tests: 14 targeted baseline/donor/null/manifest tests passed before launch; after the JSON-edge fix, four strengthening tests passed again, and the compact-feature/correction set passed five tests. The compact collator-equivalence test confirms zero-dropout model tensors are unchanged when optional extraction groups are omitted.

Timing estimate: roughly 2–4 days of compute on two L40S GPUs, followed by approximately 1–2 days to retrieve, audit, and integrate evidence and prepare a submission artifact. Provision about 3–6 days for an evidence-and-artifact handoff, with meaningful uncertainty. The measured attention probe with activation checkpointing used 1.0378 seconds per optimizer step; the centered-adapter probe used 0.9180 seconds. Each real-data epoch has 4,424 steps. These probes exclude full-cohort parsing/null-generation/I/O costs, and the ReGVD ceiling is 100 epochs with the frozen early-stop policy. Budget up to a week if the shared server is contended or convergence is slow. No throughput probe is a scientific result, and no estimate guarantees experiment or submission readiness.

Critical integrity status: the historical Stage 0 split was column-misaligned. Old numerical evidence must not support clean-split or untouched-test claims. Corrected source roles were verified, with 141,560 training functions/4,302 positives and 10,566 tune functions/330 positives. See `split_integrity_correction.json` in the local campaign directory. The historical manuscript has been explicitly placed on submission hold. Earlier prediction/hash audits missed the column-alignment problem; these new runs address that material gap.

There is no claim of 80% acceptance probability. GPU completion alone does not make a paper submission-ready. Corrected metrics, external-model fidelity, learning curves, positive-control outcomes, anonymous artifact access, and revised paper claims must all be reviewed before submission. Do not remove the SSH project or temporary access key while the campaign is running or before verified retrieval.
