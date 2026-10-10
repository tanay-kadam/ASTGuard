# INVALID HISTORICAL RESULTS — DO NOT USE FOR SUBMISSION

This folder is quarantine, not the main results folder.

The 38 historical real-data runs used a corrupted split/component manifest. Attention-model runs also had the CUDA initialization-seed defect. Their original measurements, checkpoints, logs, and superseded manuscript are preserved for investigation; they must not be presented as corrected, clean-split results.

`archive_manifest.json` records every original and archived path. Nothing was deleted. Original relative layouts are retained under `runs/`, `artifacts/`, and `paper/`.

The complete quarantine is retained locally. The public artifact includes this
notice and path manifest; historical active reports removed from the current
tree remain in Git history. Quarantined checkpoints and raw reports are not
part of the corrected 42-job release.

The archived v2 PDF is an invalid submission draft. The v1 PDF was not present on disk when this archive was created.

For current evidence, use [the current-results index](../../paper/current_results/README.md). The corrected SSH campaign is separate and was not moved or interrupted by this local organization.

The six invalid synthetic attention executions are already quarantined on the server under `artifacts/release_gates/strengthening_20261006/quarantine/cuda_seed_bug_20261006T225625Z`; their corrected replacements occupy the active job tags. Keep that server quarantine excluded from final aggregation when retrieving the campaign.
