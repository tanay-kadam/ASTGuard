# Submission audit of the graph-reliance manuscript — 2026-10-09

**Decision: do not submit this PDF as-is. Revise it into a bounded empirical negative/mixed-results paper for SANER RENE. The corrected numerical evidence is credible; the current manuscript and artifact release are unfinished.** This is not a finding that the corrected campaign is invalid, and the historical manuscript's no-go decision must not be mechanically applied to the new results.

Audited file: `When_Do_Vulnerability_Detectors_Rely_on_Their_Graphs_Evidence_from_Attention_Biases__Adapters__and_ReGVD.pdf`, six pages, SHA256 `40c8ce85a4d719275bc7a49bc25f39b8e353b4b1f9e5bced84b738de619328e4`. All six pages were read and visually inspected. The source PDF was not modified.

## What this audit actually verified

- Independently recomputed selected tune AP with scikit-learn from raw predictions for all 42 canonical logical jobs on the SSH server. Every value matches the current campaign summary within absolute tolerance 1e-12.
- Independently recomputed AP, ROC-AUC, and mean absolute logit changes for **156 intervention-condition results** across those 42 jobs. Checked unique sample IDs, exact population/label membership, finite scores, and row alignment for paired differences. No checked discrepancy was found.
- Hashed the selected checkpoint for every job. For 33 local-model jobs the hash matches the intervention report; for nine ReGVD jobs it matches the checksum manifest. Also checked the retained ReGVD checksum-manifest entries. Hash agreement verifies artifact consistency, not a new forward pass of the weights.
- Checked selected AP against each run's best logged AP. For all 33 local-model runs, selected predictions equal the retained selected-epoch predictions. Checked resolved seeds and optimizer-step budgets: 1,536 synthetic steps; 22,120 real attention steps; 13,272 real adapter steps.
- Checked all 27 real-data selected-prediction populations and all real-data intervention populations against the current 10,566-row/330-positive tune stream. Checked all 15 synthetic selected populations against synthetic tune and all synthetic intervention populations against the separate 1,024-row/512-positive audit stream.
- Independently checked the synthetic 4,096/1,024/1,024 train/tune/audit partitions: balanced labels, opposite-label pairs with identical tokens, intended endpoint-label alignment, and zero sequence overlap between every pair of partitions.
- Recomputed the nine real-data group means/sample SDs and five matched-seed contrasts. The reported values in Tables I–II and the seed values in Tables IV–VI agree at their displayed precision. Table III agrees with raw audit predictions; tune and audit scores are correctly distinguished.
- Reviewed the attention/adapter forward paths, donor/null composition, training/selection/evaluation scripts, native ReGVD graph construction, upstream ReGCN/readout and classifier code, and current regression tests. **114 repository tests passed** after a Windows sandbox temporary-directory error was resolved by rerunning outside the sandbox.
- Compared 157 server Python files with local files. Only two differ: `scripts/prepare_strengthening_inputs.py` adds an archived-manifest fallback locally; `scripts/audit_paper_numbers.py` changes default input/output paths locally. The reviewed model/training/evaluation implementations agree. Record these variants in a release snapshot.

Machine-readable evidence: [independent remote audit](../artifacts/audits/submission_independent_remote_20261009.json), [synthetic integrity audit](../artifacts/audits/submission_synthetic_integrity_20261009.json). The read-only audit programs are retained at `tmp/submission_audit_remote_20261009.py` and `tmp/submission_audit_synthetic_20261009.py`.

Scope limits: this pass did not retrain models, rerun all checkpoint inference, independently rebuild all global near-clone components, or run a fresh full original-source/train-feature audit. For the latter it reviewed the preserved complete-pipeline and rebuilt-population audits. Numerical/hash consistency is distinct from independently reproducing a training run. The literature review is targeted, not systematic. No acceptance probability is estimated.

## Submission blockers and required corrections

### 1. High: the artifact section is an unfinished release instruction

Page 5 contains a visible **[VERIFY: Insert a tested, anonymous, publicly accessible complete artifact link ...]** placeholder. Pages 3–6 repeatedly state that key intervention values come from a writing handoff and remain unverified. A submission containing release instructions and pending central evidence reads as a draft.

This audit now verifies the retained prediction metrics and checkpoint hash relationships, so those specific pending statements can be replaced with precise verified scope. Do not replace them with a claim of independent weight/training reproduction: that was not done. Assemble a tested anonymous package with the exact current source snapshot, resolved per-run configs, selection metadata, raw selected/intervention predictions, environments, manifests/checksums, and runnable audit commands. Make checkpoint access and size practical. Include the manuscript source: no active `.tex`/`.bib` file for this PDF was found in the repository inventory.

SANER RENE explicitly evaluates artifact availability and methodological rigor, and expects artifact links for public-data studies. Its new-study format allows up to 10 content/appendix pages plus two reference-only pages. This six-page PDF fits that ceiling, but uses little of the available space to establish the evidence. Mandatory abstract: **October 19, 2026**; paper: **October 23, 2026**, AoE. [Official RENE call](https://conf.researchr.org/track/saner-2027/saner-2027-reproducibility-studies-and-negative-results-rene-track).

### 2. High: the centered-adapter sensitivity control fails and its cause is unresolved

The failure is real, not a transcription error: synthetic centered-shuffled audit AP is 0.5429921, 0.9994329, and 1.0 for seeds 42/123/456. The authentic-minus-shuffled >=0.30 criterion fails in the latter two seeds. All three repaired runs retain the intended `MatchedNullGraphDataset -> GraphDonorDataset -> _FeatureDataset` training chain. The previously fixed wrapper-overwrite defect is therefore not evidence for the cause of this new result.

The synthetic partitions are sequence-disjoint and the paired labels have identical sequences. Direct donor-transplant alignment proportions are close between recipient classes: seed 42, 0.218831/0.218933; seed 123, 0.216268/0.216532; seed 456, 0.215210/0.216838. This simple diagnostic does not explain the near-perfect outcome and does not certify absence of every higher-order signal.

Keep the failed result in the paper. Do not tune the control until it passes. Diagnose the complete real/null input paths, prediction trajectories, and authentic-graph checkpoint-selection effect; if supplementary experiments are needed, label them post hoc. Authentic graphs are supplied for tune selection even after shuffled training, which is an alternative mechanism worth testing rather than assuming random-graph training must always yield chance authentic evaluation. Until resolved, the adapter is not a successfully certified mechanism control. An explicitly scoped empirical failure can still be publishable; the present protocol itself requires the sensitivity limitation to be understood before release.

### 3. High: related work omits the closest comparisons

All seven references are backbone/model/dataset references. The paper should directly distinguish its contribution from existing reliance/perturbation evaluations:

- **Are We Learning the Right Features? (ICSE 2025)** uses feature-preserving/eliminating perturbations to evaluate five vulnerability detectors. This is directly relevant to the distinction between prediction performance and feature reliance. [Primary paper](https://arxiv.org/abs/2501.13291).
- **Graph Neural Networks for Vulnerability Detection: A Counterfactual Explanation (ISSTA 2024)** introduces CFExplainer and graph perturbations across four GNN vulnerability models. Distinguish its local minimal explanations from this study's nuisance-preserving population controls and training contrasts. [Primary paper](https://arxiv.org/abs/2404.15687).
- **GraphFramEx** evaluates explanation fidelity and graph masks. It provides broader context for graph intervention evaluation. [Primary publication](https://proceedings.mlr.press/v198/amara22a.html).

The defensible contribution is the particular empirical combination of training controls, same-checkpoint intervention, matched nulls, and sensitivity checks on this cohort. Do not claim invention of graph perturbation, counterfactual vulnerability evaluation, or degree-preserving null graphs. The current PDF avoids explicit “first” language, which is good, but still needs these comparisons to substantiate significance.

### 4. High: the method recipe is incomplete and partly inaccurate

Page 2 describes K=4 and “block size four” as the frozen centered design. The implementation parameter means **four position blocks**, not blocks containing four tokens. Eligible tokens are partitioned into approximately equal positional quarters, and endpoint permutations are restricted jointly by exact incoming degree, outgoing degree, and positional block. The current sentence omits the degree restriction and misdescribes block size.

Separate the actual recipes:

- Real centered adapter: K=4, four position blocks, AST+DFG, three epochs, weighted BCE, new-module multiplier 10.
- Synthetic centered adapter: **K=8, one position block, AST only**, twelve epochs, unweighted BCE, new-module multiplier **50**.
- Synthetic attention: twelve epochs, unweighted BCE, multiplier 50; declared AST-only config, but the factory constructs **AST+DFG attention gates**, with empty DFG edges. The earlier audit already identified this architecture/config discrepancy. Record the executed architecture, not only the declared relation field.
- Real attention: five epochs, weighted BCE, multiplier 50, structural layers 2/5/8/10, maximum input length 512. Synthetic length is 26. ReGVD uses 400 tokens and its distinct loss/precision/optimizer recipe.

The generic claim that local CodeBERT models retain weighted BCE needs an explicit real/synthetic distinction. Include pinned CodeBERT revision, optimizer/warmup/precision, adapter dimension, actual graph relations, and null namespaces in a compact recipe supplement. These are reporting corrections; this audit does not recommend changing frozen results to match prose.

## Scientific strengths and remaining risks

### The corrected campaign is materially better than the quarantined manuscript

The PDF explicitly excludes historical results, discloses the split defect and historical official-test exposure, uses the corrected manifest `793ac1b2bcacb06aa19aef62ac575482dbb76a5307d026997ac239ce5157f5c2`, and does not claim an untouched final test. Current raw prediction checks agree with that tune population. The preserved rebuilt-population audit reports correct original roles/components/source mappings and no original-test use in the corrected cohort. It also reports nine sequence and eight full local-input fingerprints shared across train/tune and missing lexical fingerprints; the PDF discloses these limitations accurately. This audit did not independently rerun the full near-clone builder.

The nine ReGVD runs stopped after 20–26 epochs, with selected epochs 7–16; none hit the 100-epoch ceiling. Graph-construction and ReGCN-forward parity against pinned upstream pass the repository tests. Inspection also confirms the upstream-style classifier path, native graph intervention, and frozen embedding design. The paper correctly calls this a common-cohort adaptation, not reproduced upstream benchmark scores. A fresh complete upstream training reproduction was not performed.

### All real-data results remain selected development outcomes

Every real score is measured on the same tune population used for checkpoint selection. The PDF is candid about this. It is still the most consequential scientific limitation: there is no independent estimate of detector generalization or confirmation that intervention patterns persist on unseen vulnerability data. More seeds do not repair selection bias. A fresh, verified unexposed cohort or external dataset is the strongest additional evidence. Do not relabel or casually reuse the historically exposed official test.

Independent real-data evaluation is a strong recommendation for a convincing submission, not a universal claim that no venue can publish a carefully bounded development-set study. If it cannot be obtained, frame the submission as a developmental mechanism case study and retain a correspondingly narrow conclusion. The RENE call specifically warns that negative results caused by inadequate power or methodology are weak submissions.

### Prespecified thresholds failed; they are not equivalence tests

Attention authentic-minus-shuffled mean AP is -0.0112864, with paired values -0.0216083/-0.0487323/+0.0364813. A descriptive three-seed 95% t interval is [-0.119432, +0.096859]. This supports “no consistent advantage in this frozen recipe,” not “authentic topology has no effect.” Authentic-minus-sequence is +0.0147549, with two negative seed differences.

Centered-minus-sequence mean is +0.0079809; descriptive interval [0.0050278, 0.0109340]. ReGVD native-minus-permuted mean is +0.0154273, interval [0.0102330, 0.0206217]; native-minus-self is +0.0111471, interval [0.0049971, 0.0172971]. These are positive observations on this tune set, but all miss 0.02. These intervals describe seed variability on a fixed selected dataset, not dataset-level or deployment uncertainty. Preserve the paper's distinction between direction, threshold attainment, and inference.

Both attention seeds 123/456 select the final fifth epoch; all real adapter runs select epoch three. Budget-end selection keeps convergence unresolved. Report learning curves/epoch losses and the selection distribution; do not describe five epochs as proof of convergence.

### The fixed-checkpoint evidence is numerically supported

Attention empty-graph mean absolute changes are 0.00671951/0.01947779/0.03037982; empty-graph AP increases at all three seeds. The narrow operational statement in the PDF is supported.

Centered full-minus-base intervention AP is +0.00033628/+0.00031805/+0.00023949, mean **+0.00029794**, matching “approximately 0.00030.” The between-training +0.00798 is not this correction's AP contribution. The evaluator uses FP32 and a different null namespace from selection, while training/selection uses BF16 and probability-score AP. Full intervention AP minus selected tune AP is +0.00031828/+0.00020280/+0.00011570, comparable in scale to the small direct effect. Document all three differences—precision, score representation, and null namespace—and keep within-evaluation base/full comparisons paired. Do not attribute the whole drift to score ties.

ReGVD native-to-permuted same-checkpoint AP decreases are +0.02508936/+0.05088250/+0.02233777. Mean absolute logit changes are approximately 0.63180/0.68619/0.55055; approximately 57.9% of native edges change. These are strong input-sensitivity observations under this perturbation, not identification of security semantics. Real local nulls change approximately 18.6% AST and 9.1% DFG edges; the PDF's approximately 19%/9% wording is accurate. Empty, matched-null, sequence-path, and ReGVD self-only interventions answer different questions.

### Provenance is good but not uniformly complete

All 18 corrected real local-model runs and the nine repaired synthetic attention/centered-shuffled runs record unchanged start/end source identity and the requested CUDA construction seed. The six earlier synthetic sequence/centered-authentic runs lack these newer start/seed fields; the identified structural-constructor RNG defect does not affect their model branches, but their historical provenance cannot be retroactively upgraded. ReGVD retains run/checkpoint checksums and pinned architecture metadata, but its runner does not capture the same per-run start/end source identity or a full per-run environment snapshot. Freeze and package the actual source/environment evidence; acknowledge what is unavailable.

`paper/current_results/README.md` still says the campaign is running and has no approved corrected manuscript. Update that index only after integrating the audit and revised claims. Generic README reproduction paths still include historical stage-zero entry points; provide a tested corrected-campaign entry point so a reviewer does not accidentally reproduce the compromised population.

## Claim classifications

1. **SUPPORTED WITH CAVEAT:** attention fails to show a consistent authentic-over-shuffled advantage. Evidence: all nine current real attention selected predictions, paired contrasts, and full-cohort interventions. Caveat: one selected development cohort and bounded recipe; not equivalence or general uselessness.
2. **SUPPORTED WITH CAVEAT:** the centered adapter improves separately trained sequence tune AP by approximately 0.00798. Evidence: nine real adapter runs. Caveat: tune selection, architecture/capacity/training changes, and failed synthetic control prevent causal attribution to authentic topology.
3. **SUPPORTED WITH CAVEAT:** centered direct full-minus-base AP contribution is approximately 0.00030. Evidence: three full-population paired intervention reports. Caveat: AP ranking contribution is not a decomposition of training effects; evaluation differs from selection.
4. **SUPPORTED WITH CAVEAT:** ReGVD native graphs outperform these training controls and respond to endpoint perturbation. Evidence: nine real ReGVD runs and raw interventions. Caveat: below the frozen 0.02 threshold, adapted co-occurrence graph, selected tune set, no semantic-causality inference.
5. **SUPPORTED:** synthetic attention meets all five operational sensitivity checks at all three seeds. Evidence: raw independent synthetic audit predictions and separate sequence-disjoint populations. This does not validate real vulnerability detection.
6. **UNSUPPORTED:** the centered adapter passes the complete synthetic sensitivity validation. Raw shuffled audit AP contradicts it in two seeds. The PDF correctly reports failure rather than making this claim.
7. **SUPPORTED WITH CAVEAT:** the corrected population restores intended source/component roles and excludes historical test-role members from new training. Evidence: preserved full rebuilt-population audit plus current tune membership checks. Caveat: incomplete lexical-clone evidence, representation collisions, and no independent global component rebuild in this pass.
8. **UNSUPPORTED:** these results establish independent real-world generalization, universal graph irrelevance, or security-semantic causality. The PDF appropriately avoids these claims.
9. **UNVERIFIED:** the released artifact can independently reproduce this paper end to end. No tested anonymous release or fresh independent weight/training execution was established.

## Revision order and final gate

1. Correct the real/synthetic methods, positional-block definition, actual attention relations, precision, and null namespaces.
2. Integrate verified raw-artifact evidence and exact audit scope; remove all placeholders and stale “writing handoff/pending verification” prose that this audit supersedes.
3. Add the closest perturbation/counterfactual prior work and a precise contribution comparison.
4. Investigate the centered-shuffled sensitivity failure without selecting favorable reruns; retain the failure and scope restriction. Add concise intervention/threshold results and learning curves.
5. Obtain independent real-data confirmation if feasible; otherwise explicitly accept the reduced scope and associated reviewer risk.
6. Freeze one anonymous source/data/artifact package; test commands from that package, include manuscript source and an evidence index, then update `paper/current_results/README.md`.

**Recommendation:** this is a plausible SANER RENE negative/mixed-results paper after substantive revision, not a ready submission or a strong general methods/main-track claim. The numerical audit passed. Submission readiness did not.
