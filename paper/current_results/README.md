# Current results — start here

Only use evidence linked from this index when preparing a revised paper. Do not copy numbers from `archive/invalid_results_20261007`.

## Valid supporting evidence

[Original synthetic positive-control handoff](../TOPOLOGY_POSITIVE_CONTROL_RESULTS_HANDOFF.md): the audited uncentered-adapter synthetic control remains valid. This is supporting instrumentation evidence, not real vulnerability-detection performance.

Its canonical numeric summary is `artifacts/audits/topology_positive_control_v1_summary.json`; raw intervention reports are under `artifacts/release_gates/positive_control_v1_20261006/interventions/`. Its nine local run directories remain under `runs/`.

## Corrected main campaign — audited evidence

The 42-job strengthening campaign is complete. Its 42 selected APs and 156 intervention conditions were independently recomputed in the [submission audit](../../docs/PAPER_SUBMISSION_AUDIT_20261009.md). The retrieved source, predictions, configurations, checkpoints, and processed inputs are indexed by [the artifact package](../../artifact/README.md).

The revised manuscript is [main.pdf](../../main.pdf). All real results use the checkpoint-selection tune cohort; there is no independent real-test claim. The centered synthetic shuffled controls fail two seeds. Packaging and numeric agreement do not resolve those scientific limitations or automatically establish submission readiness.

Protocol: [corrected campaign design](../../docs/SUBMISSION_STRENGTHENING_PROTOCOL_20261006.md). Integrity findings: [complete pipeline audit](../../docs/COMPLETE_PAPER_PIPELINE_AUDIT_20261006.md).

## Archived evidence — not current results

[Invalid-results archive](../../archive/invalid_results_20261007/README.md) contains 38 historical real-data runs, legacy metrics/diagnostics/logs, the superseded Markdown manuscript, and the v2 PDF. These are excluded from the active `runs/` and paper-result locations.
