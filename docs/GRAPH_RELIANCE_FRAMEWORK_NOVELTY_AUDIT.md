# Graph-reliance audit framework: novelty and paper-readiness audit

Audit date: 2026-10-05. Scope: the implemented ASTGuard graph-reliance audit,
not a claim that the null-centered adapter improves vulnerability detection. This
is a bounded primary-source search and repository audit, not an exhaustive
systematic review or an acceptance prediction.

## Decision

**There is a defensible workshop/negative-results paper here, but the repository
is not submission-ready as a general evaluation framework today.** The strongest
near-term paper is an empirical negative-result study:

> Apparent gains from adding graph machinery to a neural vulnerability detector
> do not establish reliance on authentic program topology; capacity-matched,
> training-time, and inference-time controls can distinguish those effects.

Do not claim to introduce the first perturbation or counterfactual evaluation
framework for vulnerability detectors. That territory is occupied by prior work.
The plausible narrower contribution is a **topology-specific audit using
degree/position-matched null graphs, paired with capacity controls and both
training- and inference-time interventions under a leakage-controlled realistic
split**. The targeted search found no exact prior package of all these controls in
graph-based vulnerability detection, but a broader search and citation-neighbor
audit are required before using any “first” language.

For the current calendar, the best fit is the
[SANER 2027 Reproducibility Studies and Negative Results track](https://conf.researchr.org/track/saner-2027/saner-2027-reproducibility-studies-and-negative-results-rene-track),
whose call explicitly welcomes rigorous null findings. Its mandatory abstract is
due 2026-10-19 and paper 2026-10-23. This is a better intellectual fit than
forcing the work into a generic workshop. A later EASE empirical/negative-results
track or a testing/trustworthy-ML workshop remains a fallback if the minimum
evidence below cannot be completed without rushing.

## What is actually implemented

The repository currently provides:

1. deterministic AST/DFG extraction with source, split, preprocessing, and
   checkpoint provenance;
2. sequence-only, fixed-structure, learned-gate, shuffled-training,
   uncentered-adapter, and null-centered-adapter controls;
3. per-example degree- and position-matched graph nulls that preserve each token's
   incoming/outgoing degree, relation edge count, position-block edge count,
   token sequence, label, and special-token exclusions;
4. real, matched-null, empty-graph, uncentered, and sequence-logit inference
   comparisons for the new adapter family;
5. multi-seed, natural-prevalence development evaluation with AP, frozen stopping
   criteria, retained predictions, and a locked official test;
6. artifact hashes, resolved configs, selected checkpoints, environments, and
   per-example prediction files sufficient to recompute the reported AP values.

The evaluator is **not yet model-agnostic**. The matched-null intervention script
currently accepts only the local `graph_adapter` and
`null_centered_graph_adapter` variants. ReGVD, GraphCodeBERT, and LineVul adapters
exist and have unit tests, but have not been subjected to the same topology audit.
Devign/IVDetect rich-graph reproduction remains unavailable. Therefore the current
artifact supports a careful case study, not a general claim about graph-based
vulnerability detectors.

## Current evidence

All nine null-centered-probe training jobs completed without failure at 4,424
optimizer steps, using the same train/tune hashes and 10,566-example tune set. AP
was independently recomputed from every retained prediction and matched the saved
checkpoint-selection value exactly.

| Condition | Seed 42 | Seed 123 | Seed 456 | Mean | Sample SD |
|---|---:|---:|---:|---:|---:|
| Sequence only | 0.2373 | 0.2196 | 0.2390 | 0.2320 | 0.0108 |
| Uncentered graph adapter | 0.1404 | 0.1643 | 0.2152 | 0.1733 | 0.0382 |
| Null-centered adapter | 0.2259 | 0.1304 | 0.2558 | 0.2040 | 0.0655 |

Centered-minus-sequence differences were -0.0115, -0.0892, and +0.0168
(mean -0.0279; 95% paired t interval -0.1643 to +0.1084). Centered-minus-
uncentered differences were +0.0855, -0.0339, and +0.0407 (mean +0.0308;
95% paired t interval -0.1190 to +0.1806). Neither comparison satisfies the
pre-registered all-seeds-positive rule.

The mean absolute centered structural correction was 0.00034, 0.00262, and
0.00059 logits. Removing the correction from the retained predictions changed AP
by only +0.000024, +0.000321, and +0.000062. This directly supports the narrow
observation that the evaluated checkpoints' final predictions barely use the
added structural correction. It does not prove that topology is irrelevant to all
vulnerability detectors or that graph-dependent gradients had no training effect.

The three full matched-null intervention evaluations are now complete on all
10,566 tune examples per seed. Normal centered AP was 0.2259007300,
0.1299683881, and 0.2558310067; the same checkpoints' sequence-path AP was
0.2258503600, 0.1301088081, and 0.2557719976. Normal-minus-sequence differences
were +0.0000503701, -0.0001404200, and +0.0000590091 (mean -0.0000103469).
Substituting a matched null as the real graph changed AP by only +0.0000473928,
+0.0001441807, and +0.0000396316 relative to normal. Emptying the real graph
changed AP by +0.0007604785, -0.0109614400, and -0.0038677107 (mean
-0.0046895574). All reported intervention AP values were recomputed from the
stored per-example predictions and matched within absolute tolerance 1e-12.

## Closest work and novelty boundary

### Direct vulnerability-detection overlap

- [Are We Learning the Right Features? (ICSE 2025)](https://arxiv.org/abs/2501.13291)
  is the most important conflict. It provides a perturbation-based framework with
  feature-preserving and feature-eliminating transformations and evaluates five
  vulnerability detectors. Our work cannot claim the first general feature-
  reliance or perturbation framework. Its distinction must be the controlled
  isolation of **graph topology** from degree, position, tokens, capacity, and
  training dynamics.
- [Interpreters for GNN-Based Vulnerability Detection: Are We There Yet?
  (ISSTA 2023)](https://doi.org/10.1145/3597926.3598145) evaluates six explainers
  on four graph vulnerability detectors using effectiveness, stability, and
  robustness. Our audit is not an explainer benchmark, but it shares the goal of
  testing whether evidence attributed to graphs is trustworthy.
- [CFExplainer (ISSTA 2024)](https://arxiv.org/abs/2404.15687) applies
  counterfactual graph perturbations to four GNN vulnerability detectors to find
  minimal prediction-changing explanations. Our matched nulls answer a different
  global question—whether authentic topology contributes beyond preserved
  nuisance statistics—but “counterfactual graph evaluation for vulnerability
  detection” is not new.
- [NatGVD](https://arxiv.org/abs/2510.04987) changes code with semantics-preserving
  transformations and measures evasion across graph-based detectors. It is an
  adversarial robustness study rather than a nuisance-matched topology audit, but
  it prevents a broad novelty claim around graph perturbation sensitivity.
- [PrimeVul](https://arxiv.org/abs/2403.18624) establishes realistic prevalence,
  de-duplication, chronological splits, and security-relevant evaluation. Those
  are necessary foundations used here, not our novelty.
- [Deep Learning Based Vulnerability Detection: Are We There Yet?](https://doi.org/10.1109/TSE.2021.3087402)
  already shows that vulnerability detectors can exploit dataset artifacts and
  collapse under realistic evaluation. Our result can extend this concern to
  claimed structural mechanisms, but cannot claim to discover shortcut learning
  in vulnerability detection generally.

### General graph-method overlap

- [GraphFramEx](https://proceedings.mlr.press/v198/amara22a.html) systematically
  evaluates GNN explanations using graph masks and fidelity criteria. The present
  work should be framed as a domain-specific mechanism audit, not a general GNN
  explainability framework.
- Degree-preserving null graphs are established methodology. For example,
  [Should We Really Use GNNs for Transcriptomic Prediction?](https://pmc.ncbi.nlm.nih.gov/articles/PMC10939369/)
  explicitly retrains models on configuration-model graphs with the same degree
  distribution to test whether the biological input graph is useful.
- [Feature Distribution on Graph Topology Mediates the Effect of Graph
  Convolution (ICML 2024)](https://proceedings.mlr.press/v235/lee24m.html)
  develops controlled random graph models to study topology-feature dependence.
  Null-graph controls and topology/feature confounding are therefore established
  graph-learning ideas.

### Defensible novelty candidate

The potentially publishable unit is not any individual ingredient. It is the
application-specific experimental design:

1. preserve code tokens and labels exactly;
2. preserve per-token in/out degrees and coarse positional edge counts separately
   for AST and DFG relations;
3. compare authentic and matched-null topology during training;
4. intervene within the same checkpoint at inference;
5. include capacity-free sequence and parameter-matched uncentered controls;
6. audit prediction-level correction magnitude, seed replication, low-FPR and
   vulnerable/patched behavior under a realistic, leakage-controlled split.

This is **plausibly incremental-but-sufficient workshop/negative-results
novelty**, not main-track ML methods novelty. It becomes credible only if the same
audit works across independent model families and passes sensitivity controls.

## Claim audit

| Candidate claim | Classification | Evidence or gap |
|---|---|---|
| The framework is the first perturbation audit for vulnerability detectors. | **UNSUPPORTED** | ICSE 2025, ISSTA 2023/2024, and NatGVD directly overlap. |
| The framework introduces degree-preserving null graphs. | **UNSUPPORTED** | Configuration-model and degree-preserving controls predate this work. |
| The implemented matched null preserves the stated token-level nuisance statistics. | **SUPPORTED** | Construction assertions and unit tests check per-token degrees and block-pair counts; tokens and labels are not modified. |
| The current ASTGuard family barely uses its structural path at inference. | **SUPPORTED WITH CAVEAT** | Multi-seed correction magnitudes, base-vs-final AP changes, matched-null substitution, and empty-graph intervention effects are near zero or small; scope remains limited to this model family and tune cohort. |
| Authentic topology improves the evaluated detector. | **UNSUPPORTED** | Real/shuffled and centered/sequence comparisons fail the registered replication gates. |
| Graph topology is unhelpful for vulnerability detection generally. | **UNSUPPORTED** | One dataset and closely related local model families cannot support this scope. |
| The framework is ready as a general public benchmark. | **UNSUPPORTED** | It lacks a generic model adapter, independent published detector results, positive-control sensitivity, and a second dataset. |
| A rigorous negative-results or workshop paper is feasible. | **SUPPORTED WITH CAVEAT** | The design and artifacts are unusually strong, but minimum breadth and sensitivity experiments remain mandatory. |

## Minimum evidence for a credible submission

The shortest defensible path is:

1. **Completed: intervention audit.** Authentic, matched-null, empty, uncentered,
   and sequence AP plus per-example predictions are retained for all three seeds.
2. **Add a positive control.** Construct a synthetic or label-independent task
   whose target provably depends on AST/DFG topology. The audit must detect strong
   reliance there; otherwise a null finding could reflect an insensitive test.
3. **Audit at least two independent published graph-model families.** ReGVD plus
   one true program-graph model is the minimum. The existing local adapters are a
   starting point, but custom ASTGuard variants do not count as independent
   families.
4. **Use at least one realistic held-out evaluation and preferably two datasets.**
   PrimeVul should remain primary. A Devign/CodeXGLUE-style dataset can test
   generality, clearly labeled with its known limitations. Keep official test use
   one-shot and frozen.
5. **Complete extraction and leakage audits.** Manually inspect AST/DFG edge
   quality, report coverage and unchanged-null rates by relation/class/length, and
   finish the component-overlap audit.
6. **Report operational metrics.** AP is primary; include vulnerable/patched pair
   ordering, validation-calibrated recall at low FPR, latency, memory, and graph
   extraction failure strata. Do not rescue the finding with post-hoc subgroups.
7. **Make the evaluator model-agnostic.** Define a small adapter contract for
   obtaining predictions under real, empty, shuffled, and matched-null graphs;
   emit a common artifact schema and one-command reproduction manifest.
8. **Freeze claims before the official test.** The paper should specify exactly
   which hypotheses are confirmatory, which analyses are exploratory, and what a
   failed sensitivity control means.

For a four-to-six-page workshop paper, items 1–3 and the core parts of 5 and 7 are
the minimum. For a SANER RENE paper, include all feasible items and make the
negative result—not the framework brand—the center of the contribution.

## Recommended paper framing

Working title:

> **Do Neural Vulnerability Detectors Use Program Graph Topology? A
> Capacity-Controlled Matched-Null Audit**

Recommended research questions:

- **RQ1:** Do graph-augmented detectors outperform capacity-free sequence controls
  under a realistic split and natural prevalence?
- **RQ2:** Does authentic AST/DFG topology outperform nuisance-matched topology
  during training?
- **RQ3:** Within a fixed checkpoint, how much do predictions change when authentic
  topology is replaced by matched nulls or removed?
- **RQ4:** Are these conclusions stable across seeds, model families, datasets,
  low-FPR operation, and vulnerable/patched pairs?
- **RQ5:** Can the audit recover known topology dependence on positive controls?

The central contribution should be an evidence-backed warning: **component
ablation is not a topology-use test when the component also changes capacity,
optimization, or graph nuisance statistics.** The matched-null audit operationalizes
a stronger test for graph-based vulnerability detectors.

## Go/no-go rule

**Go for a negative-results/workshop submission** if the positive control passes
and at least one independent published
graph detector can be audited with the common protocol. A second independent model
showing the same no-topology pattern would make the empirical story much stronger;
a disagreement is also publishable if the audit explains when graph structure is
used.

**Do not submit a general framework paper** if only custom ASTGuard variants are
evaluated, the positive control is absent, or null graphs frequently remain
unchanged without a clear estimand. In that case, retain the work as a strong
technical report and portfolio artifact while preparing the broader study for a
later venue.
