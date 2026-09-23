# ASTGuard novelty audit for ML main tracks

Audit date: 2026-09-23. Target: NeurIPS, ICLR, ICML research main tracks, as
specified by the user. Starting commit: `b4ceb570adca5c232487c03b660bb4eb09a17465`.
This is a bounded primary-source audit, not a claim of exhaustive coverage or a
prediction of acceptance. The accompanying [proposal](MAIN_TRACK_RESEARCH_PROPOSAL.md)
is a research redesign; its proposed method has not been trained.

## Decision

**Do not make a main-track ML claim around query versus edge gating alone.**
Keep ASTGuard as an experimental platform and baseline. Pursue one more specific
methodological question: can a structural adapter learn useful graph-to-token
alignment corrections after subtracting its response to matched null graphs?

The proposed contribution is the *restricted correction function and its training
behavior*, evaluated across code and language tasks. It is not the invention of
gates, graph randomization, residual learning, negative controls, or risk calibration.
No exact equivalent was identified in the sources inspected, but the combination
has substantial incremental-contribution risk. Its value must survive the closest
controls, especially uncentered residual adapters, graph contrastive training,
modularity-based centering, and invariant graph learning.

The strongest defensible submission story would be a reproducible finding about
when alignment-specific structural corrections generalize, supported by a method
that improves that tradeoff. Renaming ASTGuard or adding a theorem to the old gate
does not establish this story.

## What the current implementation actually contributes

The original model adds `beta * sigmoid(w^T h_i + b) * M_ij` to attention scores.
The edge version adds an endpoint-conditioned gate with features
`[h_i, h_j, h_i * h_j]`. It preserves dense semantic attention and a pretrained
CodeBERT backbone. See the [R2 audit](EDGE_GATING_NOVELTY_AUDIT_AND_DIRECTION.md)
for equations and the exact implementation boundary.

| Candidate claim | Assessment for an ML methods paper |
|---|---|
| Put AST/DFG information into Transformer attention | Established mechanism family |
| Make a structural bias depend on the query | Established gate family; new task specialization |
| Let structural neighbors receive different gates | Established endpoint-dependent attention family |
| Preserve pretrained weights while injecting syntax | Established design goal |
| Use few additional parameters | Engineering property; must measure runtime too |
| Show a gate heatmap | Diagnostic; not proof of useful structure or explanation |
| Evaluate chronology, leakage, pairs, and transfer | Necessary rigor; not architectural novelty |
| Subtract the same adapter's matched-null response at prediction time | Candidate narrower method; requires comparisons below |

The final-layer limitation is also real: with CLS-only classification, no edges to
CLS, and no later token-mixing layer, layer 11's structural bias cannot affect the
classification logit. A future comparison must use a common active placement such
as `(2,5,8,10)` and retain the historical placement as a separate ablation.

### Local evidence, not a success claim

The saved [R2 pilot table](../runs/edge-pilot-20260923/pilot_results.csv) reports:

| Model | Development AP |
|---|---:|
| Sequence | 0.742588 |
| Fixed AST+DFG | 0.753004 |
| Query gate | 0.753004 |
| Edge gate | 0.753004 |
| Nominal parameter control | 0.753004 |

This is one seed, 16 optimizer steps per model, 32 balanced validation examples,
and a 64-token window. The saved verification records 87/96 truncated functions.
It provides **no positive evidence for edge selection**, and is too small to
establish equivalence or rejection of a properly trained method. The nominal
capacity control repeats query features and does not match effective capacity.

The earlier audit's CPU-only hardware statement is historical. A newer
[hardware artifact](../artifacts/environment/local_rtx6000ada.json) records an
RTX 6000 Ada with CUDA. That is evidence about the profiled host, not a new live
throughput measurement. Neither this audit nor the math checks run GPU training.

## Closest work and how it changes the claim

Inspection depth is explicit. A publisher abstract supports an overlap warning,
not an equation-equivalence verdict. Reported performance was not reproduced.

| Source | Relevant overlap and consequence | Inspection |
|---|---|---|
| [GREAT: Global Relational Models of Source Code, ICLR 2020](https://vhellendoorn.github.io/iclr2020.pdf) | Code relations modify global attention; multiple edge types combine. Compare against content-dependent relational attention, not just a scalar fixed bias. | Method equation, PDF pp. 2-3 |
| [XLM-E, ACL 2022](https://aclanthology.org/2022.acl-long.427.pdf) | Section 3.3 gates relative-position bias using queries. Query-conditioned bias modulation is not new. | Section 3.3 equations |
| [GATv2, ICLR 2022](https://arxiv.org/abs/2105.14491) | Query-dependent neighbor ranking is an established expressivity question. Endpoint interaction is insufficient as the central invention. | Primary abstract/argument |
| [K-ASTRO, v3, 13 Oct 2025](https://arxiv.org/html/2208.08067v3) | AST co-occurrence biases and structural augmentation for vulnerability detection. Its single-layer adaptation differs from ASTGuard, but directly overlaps the application claim. | Sections 3.2 and 4.3 |
| [Gated Tree Cross-Attention, 2026](https://arxiv.org/abs/2602.15846) | Gated syntax injection compatible with pretrained checkpoints. Compatibility and syntax gating cannot anchor novelty. | Primary abstract |
| [DualGraphVulD, 2026](https://www.sciencedirect.com/science/article/pii/S0950584926002508) | Semantic/structural alignment and gated local/global dependency processing in vulnerability detection. Relevant contemporary task comparison; equivalence unresolved. | Publisher abstract/preview |
| [Pro-GNN, 2020](https://arxiv.org/abs/2005.10203) | Learns graph structure to handle corrupted graphs. Broad claims about learning to trust imperfect graphs are already occupied. | Primary abstract |
| [Uncertainty-Aware Graph Structure Learning, 2025](https://arxiv.org/html/2502.12618v2) | Explicit uncertainty-aware graph learning is a close family. A confidence scalar alone is not a sufficient redesign. | Primary abstract and method-page inspection |
| [GSAT, ICML 2022](https://proceedings.mlr.press/v162/miao22a/miao22a.pdf) | Stochastic attention and an information bottleneck select relevant subgraphs; the paper also discusses pretrained models. Essential edge-selection/regularization comparator. | Method description and figure |
| [DIR, ICLR 2022](https://hexiangnan.github.io/papers/iclr22-invariant-gnn.pdf) | Intervention-based invariant rationale learning. Graph interventions and suppression of shortcuts are established. | Primary abstract/method overview |
| [CIGA, NeurIPS 2022](https://arxiv.org/abs/2202.05441) and [official implementation](https://github.com/LFhase/CIGA) | Invariant subgraph learning under graph distribution shifts. A generalization claim needs comparison to this family with matched inputs. | Primary abstract and author implementation description |
| [Deep Graph Infomax, ICLR 2019](https://openreview.net/pdf?id=rklz9iAcKQ) | Learns through real/corrupted graph contrasts. Distinguish a task-trained prediction correction from a graph-authenticity discriminator. | Method figure and corruption objective |
| [HYPA-DBGNN, 2024](https://arxiv.org/html/2406.16552v1) | Null ensembles identify unusual temporal patterns before message passing. Explicitly defeats a broad claim of being first to combine graph nulls and neural learning. | Sections 3-4 and discussion |
| [ModTGCN, 2026 preprint](https://arxiv.org/html/2606.23694v1) | Uses a degree-corrected modularity matrix in a text-classification objective. Mean-subtracted adjacency is not the proposed novelty; nonlinear adapter-response centering needs a separate comparison. | Section 3.3, equations 1-4 |
| [Modularity with conditional expected models, 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3880576/) | Conditional null subtraction predates neural methods. Do not market `A - E[A]` as an invention. | Primary methods section |
| [Learning to Defer to Multiple Experts, AISTATS 2023](https://proceedings.mlr.press/v206/verma23a.html) | Expert selection, confidence calibration, and consistent objectives are established. A sequence-versus-graph router needs direct comparison. | Primary proceedings abstract |
| [When Does Quality-Aware Multimodal Fusion Matter?, 2026](https://arxiv.org/abs/2606.26473) | Reliability permutation diagnoses whether scores affect decisions. Gate permutation and a reliability narrative alone are insufficient. | Primary abstract |
| [Learn then Test](https://arxiv.org/abs/2110.01052) | Calibrates policies using multiple testing and finite-sample risk control. Any optional risk-selection wrapper is borrowed methodology, not a novel theorem. | Primary abstract and author artifact |
| [Conformal Risk Control](https://arxiv.org/abs/2208.02814) | Expected-risk control under specified conditions is established. Generic conformal terminology cannot substantiate OOD safety. | Primary abstract |
| [Routing Ceilings, 2026](https://arxiv.org/abs/2607.14628) | Studies prompt cheatsheets in code-security tasks. Despite the title, it is not an AST/DFG attention router; treat as adjacent evidence about prior transfer. | Primary abstract |
| [VISION, 2025](https://arxiv.org/abs/2508.18933) | Counterfactual augmentation for vulnerability detection. Adding patch contrastive training would not by itself create an open contribution. | Primary abstract, checked in preceding audit work |
| [Causal-aware training, 2026](https://www.nature.com/articles/s41598-026-69332-6) | Combines counterfactual supervision and code-model adaptation. Another reason to avoid a generic causal-training pivot. | Publisher abstract, checked in preceding audit work |
| [PrimeVul](https://arxiv.org/abs/2403.18624) | Realistic vulnerability evaluation makes pair discrimination and dataset integrity central. Preserve the existing evaluation discipline. | Primary abstract and local pinned protocol |
| [GOOD benchmark](https://proceedings.neurips.cc/paper_files/paper/2022/hash/0dc91de822b71c66a7f54fa121d8cbb9-Abstract-Datasets_and_Benchmarks.html) | Supplies graph OOD settings. Useful for breadth, not evidence that any particular split isolates extraction noise. | Primary proceedings abstract and official repository |

### Why the selected redesign is narrower

For a fixed sequence representation `H`, compute a graph adapter response on the
observed graph and subtract the *same adapter's* mean response over a specified
permutation orbit of matched graphs. Add only that difference to a frozen sequence
prediction. Learn the difference with task supervision and a penalty on null-response
variance. This makes a precise restriction on what the added parameters can express.

Compared with the closest families:

- GSAT/DIR/CIGA select or train invariant graph representations. The proposed
  restriction cancels every graph response invariant under the chosen matching
  group; this is a different, narrower target than discovering causal subgraphs.
- HYPA and modularity methods compare graph statistics with null expectations.
  Here the centered quantity is a task-trained nonlinear *prediction response*
  conditioned on the same frozen tokens. Linear versions can collapse to familiar
  centered-adjacency methods and must be included as controls.
- DGI-style objectives can reward distinguishing real graphs from corrupted ones.
  The proposed response is trained to correct task errors; a realistic graph that
  supplies no useful task correction need not receive a reward.
- Ordinary residual learning and routing can exploit new sequence-only capacity.
  An additive term identical across the matched orbit cancels from this correction.
  Multiplicative token/graph shortcuts can remain; this is not complete disentanglement.

These distinctions specify experiments. They do not prove that the redesign is
more useful than existing methods or that reviewers will regard it as substantial.

## New feasibility evidence

The [audit script](../scripts/audit_structural_nulls.py) was run on the **32 train-role
functions** of the old R2 pilot, without using labels. It permutes graph endpoints
among nodes matched on per-node degrees, visible BPE-piece count, and optionally
four position blocks. Node features stay fixed. It checks degree and block-count
preservation. Sixteen draws per condition give:

| Relation | Position blocks | Nonempty graphs | Functions with any observed edge change | Mean edge-change fraction over nonempty graphs |
|---|---:|---:|---:|---:|
| AST | 1 | 25 | 22 | 0.2591 |
| AST | 4 | 25 | 16 | 0.0473 |
| DFG | 1 | 10 | 3 | 0.1194 |
| DFG | 4 | 10 | 2 | 0.1050 |

Source: [machine-readable report](../artifacts/audits/main_track_null_feasibility.json).
The graph-matching restriction can leave very little variation, especially in DFG.
That is a concrete feasibility risk, not an excuse to silently relax the null until
a performance gain appears. Measure a larger train-only, longer-window cohort before
training the candidate. No observed change in 16 draws is not proof of a singleton
orbit. These visible-node graphs came from full-function extraction; they are not
evidence for a prefix-only extraction protocol.

Exact small-graph numerical checks also passed: nuisance cancellation, null centering,
the binary-log-loss curvature bound, Monte Carlo variance, and a counterexample to
centering after graph-dependent gating. Those checks verify calculations on a finite
example, not a learned model or a new theorem's novelty.

## Search coverage and unresolved risks

Searches covered: gated relation bias; AST structural adaptation; uncertainty-aware
graph learning; graph rationalization/invariance; graph null models and modularity;
negative controls; graph counterfactual residuals; control variates; learning to defer;
quality-aware fusion; and finite-sample risk calibration. Exact-title follow-ups
checked the sources above. Search results were followed to papers, proceedings,
publisher pages, or author repositories; third-party summaries were not the basis
of technical distinctions. This is a targeted audit, not a systematic review with
a complete citation census.

Before submission, inspect and reproduce the closest applicable public artifacts,
run citation-neighbor searches around HYPA/GSAT/DIR/ModTGCN, and repeat the search
for subsequent work. Publisher previews remain unresolved where full methods were
not inspected. Paper availability does not imply independently verified results.

## Main-track decision criteria

Continue only if the new model beats an uncentered adapter and matched augmentation
controls, improves an operationally relevant metric without hiding regressions,
and has a consistent mechanism story across code and a non-code task. Small
algebraic identities plus a tiny benchmark gain are not enough. Theory can support
the contribution; these elementary identities are not a standalone theory paper.

If only the old edge model improves, the natural outcome is a narrower empirical
paper, potentially a workshop submission after adequate evaluation. If nulls have
little usable variation or centering removes useful signal, report that and stop
this redesign. The [proposal](MAIN_TRACK_RESEARCH_PROPOSAL.md) defines the bounded
experiment and failure criteria. The original 200-job campaign is not a test of
this new hypothesis.
