# Seven-day evidence-strengthening campaign

Authorization: the user requested a seven-day strengthening campaign using all eight GPUs. This authorizes compute and preparation, not an acceptance score, public posting, or submission. All results, including failures, will be retained. The previous 42 jobs remain unchanged and will be reported separately.

## Frozen training design

This is a follow-up designed after inspecting the original results, not a prospective preregistration. Freeze this document, resolved configs and source hashes before the new training starts. Do not inspect new holdout scores to change training, select architectures, or choose reported seeds.

H1: Under a doubled training horizon, authentic graphs improve real-data AP over the family-matched shuffled/sequence controls. Report paired seed differences and their uncertainty; negative, inconsistent, or small effects contradict a consistent useful benefit. Retain the earlier descriptive 0.02 AP rule for comparability, but do not treat failure of that rule as equivalence.

Real local matrix: attention sequence/authentic/shuffled (10 epochs); adapter sequence/uncentered/centered (6 epochs), each at seeds 42, 123, 456, 789, 2026. Thirty fresh jobs. Use the existing corrected 141,560 training and 10,566 tuning population, preprocessing and within-family hyperparameters. Cold starts, identical full linear schedules within each family; no resumption from a shorter schedule. These are bounded budget checks, not guaranteed convergence. Save all epoch losses and tune predictions. Report final-epoch selections and remaining learning trends.

ReGVD: add seeds 789 and 2026 for native/permuted/self using the unchanged 100-epoch ceiling, 20 minimum and patience-10 recipe. Combine these with the original three seeds only for this unchanged recipe. Six jobs; preserve the upstream fidelity/adaptation disclosures.

H2: Authentic attention and centered adapters learn endpoint/token alignment on a newly generated synthetic cohort, while shuffled training does not reliably transfer to authentic graphs. Regenerate train/tune/audit with generation seed 20261012, excluding every original synthetic sequence. Run sequence, attention authentic/shuffled, centered authentic/shuffled for all five seeds, 12 epochs/1,536 optimizer steps, unchanged recipes. Twenty-five jobs. Retain the original five sensitivity criteria. All synthetic audit outcomes are evaluated after checkpoint selection and never used to modify the recipe.

H3 (diagnostic, not confirmatory): authentic-graph tuning contributes to the shuffled adapter's apparent transfer. Add a centered-shuffled condition at all five seeds with a separately fixed length-matched donor graph view on TUNE, holding training and budget constant. Five additional jobs. This comparison changes selection/evaluation graph presentation and is explicitly a diagnosis of selection effects, not an improved baseline substituted for the old failure. Evaluate both selected checkpoints on the same new authentic synthetic audit, and report all outcomes. Inspect donor-label balance, same-pair donors, topology invariants and token/graph alignment before drawing causal conclusions. If inconclusive, say so.

Total new training: 66 jobs. Eight one-process-per-GPU workers claim jobs atomically, prioritize the longest jobs, preserve failures, and do not kill unrelated workloads. Record commands, source/config/protocol/data hashes, actual CUDA device, environment, selected checkpoints and predictions. Smoke every condition before its first full run. Insufficient disk, nonfinite results, wrong device/config, or smoke failure blocks the affected job. A deadline-truncated job is partial, never silently successful. Do not discard optimizer checkpoints without a separate recorded retention decision.

## Independent real evaluation gate

Independent evaluation is the highest-priority scientific addition. Inventory all historical input roles and experimental exposure before naming a holdout. Original official test is NOT presumed untouched: historical misalignment already exposed some rows. The repository's test-unlock record remains locked; do not silently unlock or present that population as certified test data.

First attempt an external DiverseVul cohort disjoint from all PrimeVul source records and known experimental inputs. Audit raw/normalized/lexical identity, repository/commit/CVE/pair linkage where available, model-input collisions, and near-clone similarity before freezing membership. Dataset names alone do not establish independence. Recompute missing fingerprints. Document rules, exclusions and residual uncertainty; do not certify exhaustive clone independence from approximate candidates.

If the external cohort has inadequate independent support, report that failure and investigate a separately audited, previously unexposed validation/calibration subcohort. Do not label an exposure-uncertain cohort untouched. Freeze cohort membership and its hash before computing model scores. Only original TUNE selects checkpoints; no threshold or model selection on the new evaluation cohort. New evaluation failures or inconvenient outcomes cannot trigger a more favorable cohort choice.

All models must share the same retained real cohort. Preserve labels and preprocessing failure policy. AP is primary; ROC-AUC, full-minus-base AP, graph-removal/null logit changes and edge-change fractions are diagnostics. Use consistent FP32 raw logits for paired intervention contrasts; identify BF16 tuning differences separately. Report prevalence, class counts and project coverage.

## Uncertainty, artifacts and interpretation

Report each seed, mean, sample SD and paired seed t intervals with their small-sample limitation. Five seeds do not establish equivalence or adequate precision automatically. When a cohort is available, add paired component-cluster bootstrap intervals with the same resamples across compared models; distinguish function-sampling from optimizer uncertainty. Predeclare analysis seed 20261012 and 10,000 resamples; report cluster counts and avoid claiming these intervals capture deployment or pretraining uncertainty.

Do not equate graph sensitivity with vulnerability-semantic reliance. Preserve nuisance-control limitations and report graph changes. The strongest justified contribution may be a mixed result identifying a control/selection failure rather than general graph irrelevance.

Days 1-2: freeze, smoke, launch eight workers, prepare/audit holdout and synthetic diagnostics. Days 3-5: finish training, verify predictions/checkpoints, evaluate frozen holdout. Day 6: update evidence/claims and anonymous artifact. Day 7: compile, visually inspect, independently recompute paper numbers and finalize the handoff. Reserve writing/verification time rather than spending all seven days on training. Public-PDF venue-policy clarification remains separate. No public push or chair communication is included in this campaign.
