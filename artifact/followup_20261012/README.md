# Anonymous saved-prediction supplement

This package accompanies the revised five-seed graph-utility study. It preserves numerical scores from 66 new training runs and 45 external evaluations on 56,571 functions (4,135 positive; 881 audit-rule components). IDs and component names are replaced consistently; no labels or scores are rounded, resampled, or selected for favorable outcomes.

## Execute from a fresh extraction

Use Python 3.11, the environment used for verification. Install requirements.txt in an isolated environment. Run:

    python verify.py --root .
    python reproduce.py --root . --output regenerated
    python verify.py --root . --bootstrap

The last command reproduces all five 10,000-resample component and hierarchical intervals and can take several minutes. Seed-only intervals and AP/AUC checks run in the first command. No network access, repository checkout, credentials, GPU, or author machine is required after dependencies are installed.

Integer IDs are namespaced by role: real TUNE, synthetic TUNE, synthetic AUDIT and external AUDIT. Compare IDs only within one role. External IDs align across all 45 files. Donor TUNE changes graph presentation, not example identities.

## Evidence roles and scores

predictions/selected contains the original checkpoint-selection score streams (local BF16 probabilities; ReGVD logits) on original TUNE, including donor-TUNE selection for that diagnostic. predictions/development contains post-selection intervention scores on real TUNE or the separate synthetic AUDIT. For ReGVD development intervention changes the reference is native, as in the saved execution; the selected self-only condition still selects on self graphs. predictions/external uses FP32 local logits or the pinned mixed-precision ReGVD forward and never selects checkpoints. The normal external view is authentic/native except for the self-trained baseline, which uses self-only. Keep selection scores distinct from post-selection FP32 scores.

The common external population file supplies labels and dependence-component assignments. Component names are remapped in sorted original order so seeded bootstrap resampling is numerically reproducible. Configs retain numerical settings but remove execution paths and identifying provenance. study.json supplies every seed, history, selection epoch, reported metric and contrast. Generated tables and plots are numeric replicas; journal fonts can differ from the manuscript.

## Reproducibility scope

These commands reproduce saved-score measurements, not retraining or new checkpoint inference. Benchmark function bodies and model weights are omitted. The text files under implementation_reference document anonymized execution logic; they are not an independently runnable training distribution and their names/imports are changed for review. A source/checkpoint hash audit was performed before anonymization; its author-only mapping is not in this ZIP. A complete runnable training implementation, dataset-recovery instructions, and model weights are not included. No release of the full implementation or checkpoints is currently committed; any future release would depend on access rights, reproducibility scope, and an appropriate hosting arrangement. Upstream dataset, model and implementation terms remain in force; this package grants no new rights to them.

The external population was frozen without inspecting model scores and excluded global components intersecting any PrimeVul source role, followed by model-input collision purging. Disjointness is only under the stated metadata/hash/lexical/near-clone rules, not proof of semantic, project, or pretraining independence. A five-seed hierarchical interval containing zero is not equivalence. Failed synthetic controls and the unchanged perfect donor-TUNE diagnostic seed are retained.
