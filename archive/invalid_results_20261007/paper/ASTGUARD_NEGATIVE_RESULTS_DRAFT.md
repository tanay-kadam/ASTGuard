# Do Graph-Augmented Vulnerability Detectors Use Their Graphs?
> SUBMISSION HOLD (2026-10-06): A shifted-column bug was found in the historical Stage 0 split manifest. These numbers remain historical executed-input results, but the intended clean-split/untouched-test claims below are not valid for that cohort. Do not submit this draft or reuse these claims until the corrected-split campaign replaces or explicitly qualifies the affected results. See `docs/SUBMISSION_STRENGTHENING_PROTOCOL_20261006.md` and `artifacts/release_gates/strengthening_20261006/split_integrity_correction.json`.

## Controlled Shuffle, Intervention, and Null-Centering Evidence on PrimeVul

**Draft status:** results-complete working manuscript for a negative-results venue. This document intentionally prioritizes complete numerical reporting and claim discipline over prose polish. All reported evaluations use the development/tune role. The official test role was never opened.

## Abstract

Neural vulnerability detectors are often described as structure-aware when program graphs are supplied to the model, but the presence of a structural pathway does not establish that predictions depend on authentic graph topology. We audit one concrete detector, ASTGuard, which adds abstract-syntax-tree (AST) and data-flow-graph (DFG) information to CodeBERT. Our protocol combines sequence-only and fixed-bias controls, length-matched graph shuffling during training, graph-removal and graph-replacement interventions at inference, pathway diagnostics, and paired random seeds. Across the initial one-epoch campaign, authentic graphs did not outperform length-matched shuffled graphs: mean tune average precision (AP) was 0.201 for authentic graphs and 0.217 for shuffled graphs over seeds 42, 123, and 456. Increasing structural initialization and the learning rate of new modules moved the learned gates, but again produced essentially identical means for authentic and shuffled graphs (0.201728 versus 0.203674 AP); the paired authentic-minus-shuffled difference was -0.001946 AP, with seed differences +0.096851, -0.080513, and -0.022176. Mean absolute logit changes after graph removal remained below a preregistered 0.05 threshold for all authentic-graph checkpoints (0.034287, 0.035558, and 0.016434). We then evaluated a null-centered graph-response adapter intended to subtract responses shared by degree- and position-matched null graphs. The centered model reached mean AP 0.204046, below the matched sequence-only mean of 0.231982; the paired difference was -0.027936 AP (95% t interval [-0.164276, 0.108404], three seeds). Its final predictions were almost indistinguishable from its own sequence component: per-seed AP changes were +0.000024, +0.000321, and +0.000062. These results do not show that program structure is generally useless. They show that, for this model, dataset, extraction, and training budget, graph availability and moving gate parameters are insufficient evidence of topology use. We release a reproducible audit workflow and complete seed-level evidence for detecting structurally inert graph-augmented detectors.

## 1. Introduction

Graph-augmented vulnerability detectors have an easy failure mode: the implementation accepts graph inputs, training completes, and the full model obtains competitive predictive performance, yet the graph pathway contributes little or nothing to the prediction. A conventional full-model-versus-baseline comparison cannot distinguish authentic topological information from additional capacity, initialization differences, optimization noise, graph density or length statistics, or the pretrained sequence encoder.

This paper asks a narrower and falsifiable question: **does the trained detector rely on the identity of the supplied AST/DFG topology?** We study ASTGuard, a CodeBERT-based function-level vulnerability detector with additive structural attention biases. The study began as a method-development effort. The initial seed appeared favorable: authentic-graph ASTGuard reached 0.2299 AP, compared with 0.1511 for a length-matched shuffled-graph control and 0.1386 for a fixed structural bias. That apparent result did not replicate. At seeds 123 and 456, the shuffled condition reached 0.2402 and 0.2595 AP, while authentic graphs reached 0.2549 and 0.1173 AP. The reversal motivated a stricter audit rather than selective reporting.

We make three contributions.

1. We specify a structure-reliance audit that separates predictive performance, structural-pathway activity, and reliance on authentic topology. It combines seed-paired sequence-only, fixed, authentic, and length-matched shuffled controls with inference-time interventions.
2. We provide a negative empirical result for the studied ASTGuard configuration. Neither the default recipe nor a stronger structural optimization recipe establishes a benefit from authentic topology. The strong authentic-minus-shuffled mean difference is -0.001946 AP, and its three seed-level signs are inconsistent.
3. We implement and test a null-centered graph-response adapter that subtracts responses to matched null graphs. The intervention is mathematically capable of canceling graph-invariant nuisance components, and its null generator produces nontrivial alternatives, but the trained correction collapses toward zero and does not outperform the sequence-only control.

The scope of the claim is deliberately constrained. We do not conclude that program graphs are useless, that all graph-based vulnerability detectors fail, or that the PrimeVul task cannot benefit from structure. We conclude that the evaluated mechanisms fail the prespecified tests for authentic-topology reliance under the reported protocol.

## 2. Research questions and decision rules

**RQ1: Does training on authentic AST/DFG topology improve ranking performance over matched shuffled topology?**

The primary comparison is seed-paired tune AP between authentic-graph and length-matched shuffled-graph training. For the strong-recipe campaign, the decision rule was fixed before observing the results: authentic-minus-shuffled AP had to be positive for all three seeds and its mean had to be at least 0.02.

**RQ2: Do the trained predictions materially depend on the graph pathway?**

We remove graph edges at inference and measure the mean absolute logit change. For the strong-recipe campaign, graph use required a mean absolute change of at least 0.05 and a learned gate standard deviation above 0.05. The conjunction prevents moving gates alone from being treated as evidence that predictions use the graph.

**RQ3: Can a real-minus-matched-null response make the model rely on topology?**

We compare a centered graph-response adapter with a parameter- and optimization-matched uncentered adapter and a sequence-only control. The centered mechanism was considered promising only if centered-minus-sequence AP was positive at all three seeds with a mean of at least 0.02. We additionally compare the full centered prediction with the centered checkpoint's own base sequence logit.

All rules apply to the development/tune role. No official test result is reported.

## 3. Model and controls

### 3.1 Original ASTGuard attention-bias model

ASTGuard uses `microsoft/codebert-base` and injects AST/DFG masks into selected transformer attention layers. In the adaptive variant, a query-dependent relation gate scales an additive bias. If the unnormalized attention score from query token $i$ to token $j$ is $a_{ij}$, the structural term has the schematic form

\[
a'_{ij}=a_{ij}+\beta_r g_{ir} M_{ijr},
\]

where $r$ denotes AST or DFG, $M$ is the binary relation mask, $g$ is a learned query-dependent gate, and $\beta$ is learned. The Stage 0 model applies structure at layers 2, 5, 8, and 10. A structural bias in the last transformer layer is ineffective for the function classifier in this implementation because the head reads position 0 while structural edges exclude special tokens.

The default adaptive model contains 73,920 extra structural parameters. The fixed-bias control contains 96 structural parameters. A previously implemented endpoint-conditioned edge gate has 221,376 parameters but is not the principal model in this study.

### 3.2 Controls

We use the following conditions.

- **Sequence only:** CodeBERT plus the same function-classification head, without a graph pathway.
- **Fixed AST+DFG bias:** learned relation/layer bias coefficients without the adaptive gate.
- **ASTGuard authentic:** adaptive gate trained with each function's extracted AST/DFG masks.
- **ASTGuard shuffled:** the same architecture trained with a fixed, length-matched donor graph assigned to every training example. Tune evaluation always uses authentic graphs.
- **Uncentered graph-response adapter:** a shared graph adapter contributes $\beta f(H,G)$ to the sequence logit.
- **Null-centered graph-response adapter:** the same adapter contributes $\beta[f(H,G)-K^{-1}\sum_{k=1}^{K}f(H,\widetilde{G}_k)]$, where the $K=4$ null graphs preserve relation type and local position blocks while permuting eligible node identities.

The length-matched shuffle uses exact token-length buckets whenever possible, merges singleton buckets, and applies a Sattolo cycle so that no example receives its own graph. In the strong campaign, its exact-length donor fraction was 0.9999858717151737 for every seed.

### 3.3 Null-centered graph-response adapter

For each AST and DFG relation, a 64-dimensional token projection is applied to the CodeBERT hidden states. For a node with nonzero degree, the model averages projected neighbor states, takes an elementwise interaction with the node projection, averages over active nonspecial tokens, concatenates relation summaries, and maps them to one scalar response. The output layer is zero-initialized. The centered variant subtracts the mean response of four matched null graphs before multiplying by a learned scalar $\beta$.

The null construction was designed as a control, not as a semantics-preserving program transformation. It keeps the number of tokens, relation type, edge counts/degrees induced by permutation, and coarse position blocks, but breaks the association between graph node identity and the code tokens. Accordingly, this study tests model reliance on the extracted topology-token alignment; it does not claim behavioral equivalence of the null graph.

## 4. Dataset, training, and evaluation

### 4.1 Cohort and leakage controls

All main campaigns use the same prepared `P_clean` development cohort:

- training examples: 141,560, comprising 4,224 positives and 137,336 negatives;
- tune examples: 10,566, comprising 347 positives and 10,219 negatives;
- split/manifest SHA-256: `e631d90d2f43ec09922bc2df806384d8b1aff091b58d2ae03a1c17e0052451e0`;
- preprocessing hash: `435aff72451638dae06492868e79a97c591178ea66ad2935799a61245bf0e869`;
- train feature SHA-256: `c400a0ddd73acea97cfc428eedc1499af03e3bb10a75681bcdc75431cff93466`;
- tune feature SHA-256: `5d3b97abfe3679bdb08ad584ae14895fb702f0dfdc60e14454f688d97c7101cc`.

The CodeBERT checkpoint revision is `3b0952feddeffad0063f274080e3c23d75e7eb39`. The official test role was programmatically rejected by the intervention evaluator and was never used for model selection or reporting.

### 4.2 Optimization

Unless explicitly labeled as a multi-epoch diagnostic, each run trains for one epoch, exactly 4,424 optimizer steps. The effective batch size is 32, from microbatches of 4 and gradient accumulation of 8. The backbone learning rate is $2\times10^{-5}$. Training uses BF16, weighted binary cross entropy, and class weights 0.5153783421681133 for class 0 and 16.75662878787879 for class 1. Runs execute on NVIDIA L40S GPUs.

The default attention-bias recipe initializes adaptive $\beta=0.10$ and uses a new-module learning-rate multiplier of 1. The strong recipe initializes adaptive $\beta=1.0$, initializes the fixed model at $\beta=0.5$ to match the adaptive model's approximate initial effective bias $1.0\times0.5$, and uses a new-module multiplier of 50 for every condition, including the classifier-only control. The null-centered campaign uses a multiplier of 10 and $\beta=1.0$.

### 4.3 Metric and uncertainty

The primary metric is average precision (AP) on the tune split. We report every seed, arithmetic means, sample standard deviations, and paired differences. With only three seeds, confidence intervals are necessarily wide. Where shown, 95% intervals use the two-sided Student t critical value for two degrees of freedom (4.302652729911275). We use these intervals descriptively; the prespecified sign-and-effect rules, not a post-hoc significance threshold, drive conclusions.

## 5. Results

### 5.1 Early probes and default-recipe Stage 0

The earliest 400-step probes suggested little graph sensitivity. Fixed AST+DFG reached 0.0967785534 AP, with mean absolute empty-graph logit change 0.00081 and Spearman rank correlation 0.9995 between authentic-graph and empty-graph predictions. Adaptive ASTGuard reached 0.1027543827 AP, empty-graph change 0.00052, and Spearman 0.9996.

At one epoch for seed 42, fixed AST+DFG reached 0.1385575064 AP and adaptive ASTGuard reached 0.2298638415 AP. Both nevertheless remained almost invariant to graph removal: their mean absolute logit changes were 0.00176 and 0.00175, and their authentic-versus-empty Spearman correlations were 1.0000 and 0.9998. Gates stayed close to 0.5 with standard deviations approximately 0.01--0.02. Structural beta/gate gradient norms were approximately $10^{-4}$ to $10^{-3}$, compared with total gradient norms around 10--14.

The first batch-shuffled control obtained 0.1571056590 AP at seed 42, but it was superseded because swapping graph tensors between different sequence lengths can drop edges or place them on padding/special tokens. The length-matched shuffle corrected this confound.

**Table 1. Default recipe, one epoch, tune AP.**

| Condition | Seed 42 | Seed 123 | Seed 456 | Mean |
|---|---:|---:|---:|---:|
| Fixed AST+DFG | 0.1385575064 | 0.1538930659 | 0.1776649078 | 0.1567051600 |
| ASTGuard, authentic | 0.2298638415 | 0.2548552529 | 0.1173138749 | 0.2006776564 |
| ASTGuard, length-matched shuffled | 0.1510978329 | 0.2402352257 | 0.2595036125 | 0.2169455570 |

The authentic-minus-shuffled gaps were +0.0787660086, +0.0146200272, and -0.1421897376 AP at seeds 42, 123, and 456. The shuffled mean exceeded the authentic mean by 0.0162679006 AP. Sample standard deviations were 0.0197047740 for fixed AST+DFG, 0.0732685657 for authentic ASTGuard, and 0.0578338980 for shuffled ASTGuard. The adaptive authentic condition spanned 0.1375413780 AP from its minimum (0.1173138749) to maximum (0.2548552529), much larger than the originally contemplated 0.01 AP method margin.

Default-recipe diagnostics showed mean absolute empty-graph logit changes from 0.0002765457 to 0.0020486113 across the audited full-probe, seed, shuffle, and multi-epoch checkpoints. Authentic-versus-empty Spearman correlations ranged from 0.9995404412 to 1.0. Adaptive gate standard deviations averaged 0.0065502595 to 0.0164450660 across layers and diagnostic batches, while gate means remained close to 0.50. Training-log structural gradients were generally orders of magnitude below total gradient norms. These jointly indicate an effectively inert structural pathway despite nontrivial tune AP.

Two seed-42 five-epoch checks did not resolve the issue. Authentic-graph AP by epoch was 0.2063742353, 0.2281712237, 0.2107605735, and 0.2076989521 before stopping after epoch 4, with the best result at epoch 2. Length-matched shuffled AP was 0.1803588524, 0.2191883017, 0.2016642061, and 0.2014683559, also with the best result at epoch 2. The matched authentic-minus-shuffled gaps were +0.0260153829, +0.0089829220, +0.0090963673, and +0.0062305961 AP. Because only one seed was run, these values cannot override the multi-seed reversal.

### 5.2 Strong optimization does not establish topology use

The Phase A/B campaign completed 15 of 15 planned jobs with no retries. All used the same train and tune feature hashes and 4,424 optimizer steps. An independent artifact audit rehashed 183 small run artifacts with zero mismatches. Large checkpoint hashes were recorded in the run manifests; the audit did not recompute them at that time.

**Table 2. Phase A/B exact tune AP.**

| Condition | Seed 42 | Seed 123 | Seed 456 | Mean | Sample SD |
|---|---:|---:|---:|---:|---:|
| Sequence only, default | 0.2057025193 | 0.1324261085 | 0.2491295878 | 0.1957527386 | 0.0589845244 |
| Sequence only, strong optimizer | 0.1186682851 | 0.2556018899 | 0.2254596547 | 0.1999099432 | 0.0719534144 |
| ASTGuard strong, authentic | 0.2350971627 | 0.1465470505 | 0.2235394538 | 0.2017278890 | 0.0481361492 |
| ASTGuard strong, shuffled | 0.1382462848 | 0.2270604181 | 0.2457155798 | 0.2036740942 | 0.0574247547 |
| Fixed AST+DFG strong | 0.2340411584 | 0.1119690776 | 0.1168076076 | 0.1542726145 | 0.0691239343 |

The strong authentic-minus-shuffled differences were +0.0968508779, -0.0805133677, and -0.0221761260 AP for seeds 42, 123, and 456. Their mean was -0.0019462053, sample SD 0.0903961071, and 95% paired t interval [-0.2265025838, 0.2226101733]. The result fails both preregistered requirements: not all differences are positive and the mean is below +0.02.

Authentic ASTGuard minus strong sequence-only produced +0.1164288776, -0.1090548394, and -0.0019202009 AP; mean +0.0018179458, sample SD 0.1127883281, and 95% interval [-0.2783637936, 0.2819996851]. Authentic ASTGuard minus fixed AST+DFG produced +0.0010560042, +0.0345779728, and +0.1067318462 AP; mean +0.0474552744, sample SD 0.0540019867, and 95% interval [-0.0866930972, 0.1816036461]. The latter comparison alone cannot attribute the gap to authentic topology because authentic and shuffled adaptive models have virtually identical means.

Changing only the sequence-only new-module optimization from the default to strong setting produced paired differences -0.0870342342, +0.1231757813, and -0.0236699332 AP; mean +0.0041572047, sample SD 0.1078323924, and 95% interval [-0.2637133079, 0.2720277172]. This demonstrates how a single seed can make an optimizer change resemble a large method effect.

**Table 3. Phase B structure-path diagnostics.**

| Condition | Seed | Mean absolute empty-graph logit change | Mean batch/layer gate SD |
|---|---:|---:|---:|
| ASTGuard strong, authentic | 42 | 0.0342870832 | 0.2829755984 |
| ASTGuard strong, authentic | 123 | 0.0355578481 | 0.2862422045 |
| ASTGuard strong, authentic | 456 | 0.0164343310 | 0.2968381362 |
| ASTGuard strong, shuffled | 42 | 0.0114645030 | 0.2625052184 |
| ASTGuard strong, shuffled | 123 | 0.0187584952 | 0.2795233552 |
| ASTGuard strong, shuffled | 456 | 0.0122305188 | 0.2785882864 |
| Fixed AST+DFG strong | 42 | 0.0215725006 | not applicable |
| Fixed AST+DFG strong | 123 | 0.0080217316 | not applicable |
| Fixed AST+DFG strong | 456 | 0.0068721900 | not applicable |

The strong optimizer clearly changed the gates: adaptive gate means were approximately 0.42--0.60 and standard deviations approximately 0.26--0.30, compared with roughly 0.50 and 0.01 under the default recipe. Seed-42 checkpoint beta means were approximately 1.00--1.07 for adaptive ASTGuard (initialized at 1.0) and 0.48--0.56 for fixed AST+DFG (initialized at 0.5). Training losses remained finite, approximately 0.76--0.85, so the prespecified multiplier-10 fallback was not triggered. Nevertheless, all three authentic-graph empty-intervention values were below 0.05. Gate movement therefore did not satisfy the joint structure-use criterion.

**Answer to RQ1:** No evidence establishes an authentic-topology advantage. Authentic and shuffled means are nearly equal under the strong recipe, and paired signs disagree.

**Answer to RQ2:** The default graph pathway is effectively inert. Strong optimization activates gate variation, but prediction changes remain below the preregistered graph-use threshold and do not translate into an authentic-topology advantage.

### 5.3 Null construction is nontrivial but does not rescue reliance

Before training the null-centered mechanism, an exact finite mathematical check used a group of 24 items containing six distinct graphs. The additive nuisance cancellation error was $1.1102230246251565\times10^{-15}$. Null binary-cross-entropy (BCE) increase was 0.0006483742256956498, below an upper bound of 0.0006740938916224229. A constructed useful-structure example changed BCE by -0.0006486717654335117. With two Monte Carlo null samples the mean-squared error was 0.002696375566489693, and the post-centering gate mean was 0.031120175875647433. These are mathematical/feasibility checks, not trained-model performance.

A small 32-function feasibility sample with 16 draws per condition gave the following results.

| Relation | Position blocks | Functions | Nonempty graphs | Functions with observed change | Mean changed-edge fraction among nonempty graphs |
|---|---:|---:|---:|---:|---:|
| AST | 1 | 32 | 25 | 22 | 0.2591070843 |
| AST | 4 | 32 | 25 | 16 | 0.0472530677 |
| DFG | 1 | 32 | 10 | 3 | 0.1193750000 |
| DFG | 4 | 32 | 10 | 2 | 0.1050000000 |

The larger pretraining check used 1,000 training examples. Of these, 808 had nonempty ASTs, and all 808 changed under the null draw, with mean changed-edge fraction 0.3005. A total of 334 had nonempty DFGs; 270 changed, with mean changed-edge fraction 0.1961. Thus the negative trained result cannot be explained solely by a null generator that always returns the original graph, although DFG diversity remains weaker than AST diversity.

### 5.4 Null-centered campaign

All nine planned jobs completed: sequence-only, uncentered graph-response, and null-centered graph-response conditions at seeds 42, 123, and 456. Each completed 4,424 steps with the same data hashes and no recorded queue failure.

**Table 4. Null-centered campaign tune performance.**

| Condition | Seed 42 AP / ROC-AUC | Seed 123 AP / ROC-AUC | Seed 456 AP / ROC-AUC | Mean AP | Sample SD AP |
|---|---:|---:|---:|---:|---:|
| Sequence only | 0.2373412626 / 0.8490638588 | 0.2195994044 / 0.8543862044 | 0.2390053202 / 0.8443842106 | 0.2319819957 | 0.0107558681 |
| Uncentered adapter | 0.1403741784 / 0.8215209393 | 0.1643066184 / 0.8142341229 | 0.2151716910 / 0.8408537468 | 0.1732841626 | 0.0381983533 |
| Null-centered adapter | 0.2258739109 / 0.8443705332 | 0.1304302513 / 0.8186634886 | 0.2558334095 / 0.8507402581 | 0.2040458572 | 0.0654892050 |

Null-centered minus sequence-only AP was -0.0114673517, -0.0891691531, and +0.0168280893. The mean was -0.0279361385, sample SD 0.0548841466, and 95% paired t interval [-0.1642759169, 0.1084036399]. The differences were not positive at all seeds, and the mean did not reach +0.02.

Null-centered minus uncentered AP was +0.0854997325, -0.0338763671, and +0.0406617185. The mean was +0.0307616946, sample SD 0.0603006728, and 95% paired t interval [-0.1190334808, 0.1805568700]. Although the mean exceeds +0.02, the signs are inconsistent and the interval is wide.

The strongest evidence of collapse comes from decomposing each checkpoint into its own base sequence logit and learned graph correction.

**Table 5. Adapter response and within-checkpoint AP decomposition.**

| Variant | Seed | Full AP | Base-logit AP | Full minus base AP | Mean abs correction | RMS correction | Max abs correction |
|---|---:|---:|---:|---:|---:|---:|---:|
| Uncentered | 42 | 0.1403741784 | 0.1364859260 | +0.0038882525 | 0.1194266517 | 0.1437160873 | 0.4330398738 |
| Uncentered | 123 | 0.1643066184 | 0.1686308179 | -0.0043241996 | 0.1456050882 | 0.1795470471 | 0.3133337498 |
| Uncentered | 456 | 0.2151716910 | 0.2185638873 | -0.0033921962 | 0.1005847065 | 0.1228171713 | 0.1789015234 |
| Null-centered | 42 | 0.2258739109 | 0.2258503600 | +0.0000235510 | 0.0003366503 | 0.0015035577 | 0.0565671548 |
| Null-centered | 123 | 0.1304302513 | 0.1301087924 | +0.0003214588 | 0.0026247840 | 0.0116686589 | 0.4612031579 |
| Null-centered | 456 | 0.2558334095 | 0.2557719092 | +0.0000615003 | 0.0005867780 | 0.0016388161 | 0.0479578041 |

For the uncentered model, mean absolute graph responses were 0.1176339163, 0.1446254203, and 0.0998645977 for seeds 42, 123, and 456. For the centered model, authentic graph-response magnitudes were 0.0481635596, 0.2799395919, and 0.1379109367; matched-null response magnitudes were 0.0479037348, 0.2800115580, and 0.1376900806. The subtraction removes almost the entire response. Direct AP recomputation from stored raw predictions exactly matched the checkpoint reports, and all checked values were finite.

Training elapsed times in seconds were 5,681.631982, 5,677.852544, and 5,888.922169 for sequence-only seeds 42, 123, and 456; 9,876.763832, 9,975.970227, and 10,261.218282 for uncentered; and 30,957.881285, 30,715.897168, and 28,274.710441 for centered. The four-null centered mechanism was therefore approximately five times as expensive as sequence-only training in this implementation while producing virtually zero incremental correction at inference.

**Answer to RQ3:** No. Null-centering cancels the learned graph response almost completely and does not outperform the paired sequence-only control.

### 5.5 Matched inference interventions

For each centered checkpoint, we additionally evaluate five prediction paths on all 10,566 tune examples: normal centered prediction, the checkpoint's base sequence path, an uncentered real-graph response, a matched null graph substituted as the real graph, and an empty real graph. The per-example reports also record structural corrections and null-edge change fractions.

**Table 6. Final inference intervention results.**

| Prediction path / metric | Seed 42 | Seed 123 | Seed 456 | Mean |
|---|---:|---:|---:|---:|
| Normal null-centered AP | 0.2259007300 | 0.1299683881 | 0.2558310067 | 0.2039000416 |
| Same checkpoint, sequence-path AP | 0.2258503600 | 0.1301088081 | 0.2557719976 | 0.2039103885 |
| Same checkpoint, uncentered real-response AP | 0.2283234754 | 0.1268521861 | 0.2528681646 | 0.2026812753 |
| Matched null substituted as real graph AP | 0.2259481229 | 0.1301125687 | 0.2558706383 | 0.2039771100 |
| Empty real graph AP | 0.2266612086 | 0.1190069481 | 0.2519632960 | 0.1992104842 |
| Mean absolute structural correction | 0.0003421949 | 0.0026532111 | 0.0005886726 | 0.0011946929 |
| Mean AST null-edge change fraction | 0.1858912557 | 0.1859195530 | 0.1857714951 | 0.1858607680 |
| Mean DFG null-edge change fraction | 0.0908930302 | 0.0905795768 | 0.0900208503 | 0.0904978191 |

Normal centered minus sequence-path AP was +0.0000503701, -0.0001404200, and +0.0000590091; mean -0.0000103469, sample SD 0.0001127293, and 95% interval [-0.0002903822, 0.0002696883]. Removing centering while holding the checkpoint fixed changed AP relative to sequence by +0.0024731154, -0.0032566220, and -0.0029038331; mean -0.0012291132, sample SD 0.0032110727, and 95% interval [-0.0092058599, 0.0067476335]. Substituting a matched null graph for the real graph changed AP relative to normal by +0.0000473928, +0.0001441807, and +0.0000396316; mean +0.0000770684, sample SD 0.0000582503, and 95% interval [-0.0000676335, 0.0002217703]. Emptying the real graph changed AP relative to normal by +0.0007604785, -0.0109614400, and -0.0038677107; mean -0.0046895574, sample SD 0.0059040171, and 95% interval [-0.0193559488, 0.0099768340].

The intervention evaluator used an independent deterministic null namespace (`intervention-tune`), so its normal centered AP can differ slightly from the selected validation report that used the training/evaluation null namespace. Each path used all 10,566 tune examples. Raw-prediction recomputation matched every reported intervention AP within an absolute tolerance of $10^{-12}$. Report SHA-256 values were `92d6beae3b621c950e151bb6a629cb474c6fe203a1b78cf6ad86985f080c89e9` (seed 42), `f3fa3b32602fc3f910b258c15978f624b63436118de7a472173837a15d652db4` (seed 123), and `1e31d814fda6ee45f640a47ceb20ae22083712977da4a7ffef40fb07c051aace` (seed 456). The checkpoint hashes were `d87c0ae6a06e411cd7cc0fc6fe74538a61c0f51f5720e3473ef35d960657335d`, `68fcaaad3d10ebf6227f1491541fb94222ac4e2969ec18bf9a1422afa69e3ed8`, and `6c478fac3f38780d9fbf8116fc1751db365c7a36294be60e69ec54bdac193a34`, respectively.

These matched interventions reinforce the same interpretation: the centered prediction is essentially the checkpoint's sequence prediction; matched-null substitution is immaterial; and emptying the graph produces only a small, inconsistent AP change. A nonzero raw graph response is not evidence of useful authentic-topology reliance.

## 6. Discussion

### 6.1 Performance is not evidence of graph use

The largest misleading result in the study is seed 42 under the strong recipe: authentic ASTGuard beats shuffled ASTGuard by +0.096851 AP. Reporting this seed alone would support the intended method narrative. The paired seed-123 result is -0.080513 AP and seed 456 is -0.022176 AP. Likewise, the original seed-42 authentic model appeared to beat its shuffled control by +0.0788 AP, while seed 456 reversed the gap by approximately -0.1422 AP. These reversals show why graph claims require paired seeds and direct intervention, not only a favorable aggregate or selected run.

### 6.2 Parameter movement is not prediction reliance

The strong recipe moved gate distributions from roughly 0.50 with 0.01 standard deviation to standard deviations of 0.263--0.297. If gate movement were used as the sole diagnostic, the pathway would appear active. Yet authentic-graph removal changes logits by only 0.0164--0.0356 on average, below the fixed 0.05 criterion, and authentic topology does not beat shuffled topology. The null-centered adapter provides an even sharper example: its raw authentic response can be sizable, but the matched-null response is nearly identical, leaving mean corrections of only 0.000337--0.002625.

### 6.3 Why the mechanisms may fail

Several nonexclusive mechanisms are consistent with the evidence.

1. **Pretrained sequence dominance.** CodeBERT already provides a strong token representation, and the function-level label may be learned primarily from lexical or local sequential correlates.
2. **Weak optimization of the default pathway.** The default effective initial bias is approximately $0.10\times0.5=0.05$, small relative to ordinary attention scores, and its new modules use the backbone learning rate. The strong recipe addresses but does not eliminate the negative result.
3. **Pooling mismatch.** A position-0 classification head may not efficiently expose local graph changes, especially when structural edges exclude special tokens.
4. **Approximate graph quality.** Extracted AST/DFG token edges may be incomplete or misaligned. A negative result for these features is not a negative result for ideal program dependence.
5. **Graph-statistic nuisance.** The adapter may respond primarily to degree, density, token position, or other statistics shared by authentic and matched-null graphs. The near equality of real and null response magnitudes in the centered checkpoints is consistent with this explanation.
6. **Small positive count and seed instability.** The tune split contains 347 positives. AP varies sharply across seeds even for sequence-only models, making single-seed effects unreliable.

### 6.4 Practical audit recommendation

A graph-augmented detector should not be described as using program structure merely because it consumes a graph or outperforms a differently parameterized baseline. At minimum, authors should report (i) a matched sequence-only control, (ii) an authentic-versus-shuffled topology comparison with fixed pairing across seeds, (iii) an inference-time graph removal or replacement intervention, (iv) the magnitude of the actual prediction change, and (v) every seed rather than only the mean or best run. A known-positive structural task or model is also desirable to show that the audit can detect reliance when it exists.

## 7. Threats to validity

**Construct validity.** Length-matched graph shuffling breaks topology-token alignment but can preserve graph density and some length-dependent statistics. It is a test of authentic alignment, not of every possible structural statistic. Empty-graph intervention is out of the training distribution. The matched-null construction is not guaranteed to preserve program semantics.

**Internal validity.** The primary campaigns use three seeds. Their paired intervals are wide, so the evidence supports failure to establish the preregistered claim rather than proof that the true effect is exactly zero. Some early diagnostics encountered GPU out-of-memory errors and were rerun; training jobs in the Phase A/B and null-centered queues completed without retries. The remote experiment tree was dirty relative to its Git commit, but the independent audit compared important executed source/configuration hashes with the local repository and found them matching. The final archive preserves resolved configs, command lines, provenance, selected checkpoints, training/validation summaries for all 38 runs, and per-example tune predictions for all nine null-centered-campaign runs and three final intervention reports.

**External validity.** The study concerns one CodeBERT-based detector, one approximate AST/DFG extraction stack, one function-level dataset/cohort, and mostly one-epoch budgets. It does not directly evaluate GraphCodeBERT, LineVul, ReGVD, NatGVD, other programming languages, or industrial code distributions. No claim should be generalized to all vulnerability detection or all program graphs.

**Evaluation validity.** All ranking numbers are tune AP, with ROC-AUC additionally reported for the null-centered campaign. The official test set was never used. This avoids repeated test adaptation, but a camera-ready predictive-performance claim would require a frozen final protocol and one test evaluation. The negative structure-reliance conclusion is presently a development-set audit.

**Null-generator validity.** The 1,000-example feasibility check shows frequent AST changes and less frequent DFG changes, but nonzero edge change does not guarantee a difficult or meaningful counterfactual. Four null samples may provide a noisy estimate, while increasing the number raises substantial compute cost.

## 8. Related work and novelty boundary

The closest conceptual precedent is work asking whether vulnerability detectors learn the intended features, including *Are We Learning the Right Features? A Framework for Evaluating Structural and Semantic Features in Vulnerability Detection* (ICSE 2025). Prior vulnerability-detector interpretation work also studies whether learned representations and explanations correspond to meaningful code properties. GraphFramEx provides a systematic framework for evaluating graph-neural-network explanations. Counterfactual explanation work such as CFExplainer evaluates graph changes that alter vulnerability predictions. Recent structure-aware detectors, including NatGVD, motivate continued scrutiny of whether graph components carry predictive signal beyond sequence encoders.

Our novelty claim is intentionally modest. Query/edge gating, graph shuffling, and counterfactual graph evaluation are not individually new. The contribution is a reproducible, seed-paired falsification study for a concrete vulnerability detector that combines training-time matched shuffling, inference-time intervention, pathway-magnitude diagnostics, and a reported unsuccessful null-centered mechanism. The paper should be submitted as a negative-results or empirical analysis paper, not as a claim of a broadly novel graph architecture.

## 9. Reproducibility and artifact inventory

The local artifact contains:

- resolved configuration, command, environment, source-lock snapshot, feature references, selected checkpoint, train log, validation history, validation predictions, and checksums for every preserved run;
- per-example selected tune predictions for the nine null-centered-campaign runs and all three final intervention reports; older campaigns retain their training logs, checkpoint selections, validation histories, diagnostics, and audit summaries rather than full prediction vectors;
- all selected `.safetensors` checkpoints;
- queue status and launcher logs for the Stage 0, Phase A/B, and null-centered campaigns;
- per-checkpoint graph-sensitivity diagnostics;
- matched-null feasibility and intervention reports;
- the read-only server audit `artifacts/audits/phase_ab_server_audit_20261004.json`.

Transient `*.pt` optimizer/resume states are omitted from the portable archive because they are restart state rather than evidentiary output. The selected model weights and all data needed to audit the reported metrics are preserved. Raw/processed dataset files and the Python virtual environment are not committed; their hashes, manifests, dependency lock, and construction code are preserved.

## 10. Conclusion

Across default attention bias, strongly optimized attention bias, and null-centered graph-response mechanisms, we do not find reproducible evidence that the evaluated detector benefits from authentic AST/DFG topology. Authentic and shuffled training produce nearly identical mean AP under the strong recipe, graph removal causes small prediction changes, and null-centering almost completely cancels the learned response while failing to beat sequence only. The central lesson is methodological: graph availability, full-model performance, and moving gate parameters are each insufficient evidence of structural reliance. Direct matched interventions and seed-paired controls can expose structurally inert models before they become overclaimed results.

## Appendix A. Exact Phase A/B run ledger

| Tag | Run directory | Seed | Tune AP | Empty-graph mean abs logit delta | Gate SD |
|---|---|---:|---:|---:|---:|
| `pA_seqonly_s42` | `20261003T182907Z-1f297d07fa-42-204fbd` | 42 | 0.2057025192636403 | n/a | n/a |
| `pA_seqonly_s123` | `20261003T214016Z-a31b0330d8-123-d01874` | 123 | 0.13242610854866652 | n/a | n/a |
| `pA_seqonly_s456` | `20261004T005342Z-2f952d020d-456-8bd385` | 456 | 0.2491295878448513 | n/a | n/a |
| `pB_seqonly_strong_s42` | `20261003T193738Z-feab4f41f5-42-f8d836` | 42 | 0.11866828509896722 | n/a | n/a |
| `pB_seqonly_strong_s123` | `20261003T225017Z-7912775d42-123-cdb3ca` | 123 | 0.2556018898520549 | n/a | n/a |
| `pB_seqonly_strong_s456` | `20261004T025927Z-4125af0f69-456-5d0900` | 456 | 0.22545965466691592 | n/a | n/a |
| `pB_astguard_strong_s42` | `20261003T161149Z-b4a872948b-42-5bbaa7` | 42 | 0.23509716265020342 | 0.03428708319552243 | 0.2829755983548239 |
| `pB_astguard_strong_s123` | `20261003T194102Z-f95f747ce2-123-941f6d` | 123 | 0.14654705045504712 | 0.03555784813943319 | 0.2862422044854611 |
| `pB_astguard_strong_s456` | `20261003T234442Z-f60ae0a179-456-911516` | 456 | 0.22353945378395434 | 0.016434331017080694 | 0.2968381361570209 |
| `pB_shuffled_strong_s42` | `20261003T161600Z-b0949dd9bc-42-3ec918` | 42 | 0.13824628477565282 | 0.011464503011666238 | 0.2625052183866501 |
| `pB_shuffled_strong_s123` | `20261003T203659Z-96306587a5-123-ea9d77` | 123 | 0.22706041814473396 | 0.018758495221845806 | 0.2795233551878482 |
| `pB_shuffled_strong_s456` | `20261003T234724Z-0083e6af2d-456-01f83b` | 456 | 0.24571557979044378 | 0.012230518768774346 | 0.27858828636817634 |
| `pB_fixed_strong_s42` | `20261003T161824Z-bb2458902e-42-d3c284` | 42 | 0.23404115841864762 | 0.021572500583715737 | n/a |
| `pB_fixed_strong_s123` | `20261003T203915Z-a7a40dc191-123-7fb00c` | 123 | 0.1119690776380224 | 0.008021731599001214 | n/a |
| `pB_fixed_strong_s456` | `20261004T004143Z-0b36419e15-456-20d40f` | 456 | 0.11680760757987975 | 0.006872189987916499 | n/a |

## Appendix B. Exact null-centered run ledger

| Tag | Run directory | Seed | AP | ROC-AUC | Elapsed seconds |
|---|---|---:|---:|---:|---:|
| Sequence | `20261004T190617Z-35fd62ffcc-42-b479a8` | 42 | 0.23734126262263966 | 0.8490638588401048 | 5681.631981952116 |
| Sequence | `20261004T191257Z-38e7fb41fb-123-7edf43` | 123 | 0.21959940437413653 | 0.8543862043720899 | 5677.8525435794145 |
| Sequence | `20261004T222703Z-b67ee2edb7-456-7c0e9b` | 456 | 0.2390053202436881 | 0.8443842105723277 | 5888.922169107944 |
| Uncentered | `20261004T190831Z-6e540236c3-42-07e38c` | 42 | 0.1403741784436247 | 0.8215209392686337 | 9876.763831846416 |
| Uncentered | `20261004T211554Z-0940fcb013-123-53b16b` | 123 | 0.16430661837575775 | 0.8142341228535984 | 9975.970227228478 |
| Uncentered | `20261005T003156Z-37e2ab9a2c-456-e2178c` | 456 | 0.2151716910404553 | 0.8408537467502051 | 10261.218282045797 |
| Centered | `20261004T190827Z-2f7075de5b-42-f0808d` | 42 | 0.22587391093810827 | 0.844370533162361 | 30957.881284644827 |
| Centered | `20261004T212206Z-a3e71d7ef0-123-3ff9b7` | 123 | 0.13043025129127117 | 0.8186634886194079 | 30715.897167541087 |
| Centered | `20261005T003640Z-b594c1241e-456-697d18` | 456 | 0.2558334095167292 | 0.850740258088496 | 28274.71044064313 |

## Appendix C. Artifact-backed claim classification

- **Supported:** the default structural pathway has extremely small empty-graph effects under the evaluated recipe.
- **Supported:** strong authentic and shuffled conditions have nearly identical mean tune AP, with inconsistent paired signs.
- **Supported:** strong optimization moves gate distributions but does not satisfy the joint graph-use criterion.
- **Supported:** null-centering produces near-zero incremental corrections and does not beat sequence only across the paired seeds.
- **Not supported:** ASTGuard improves because it uses authentic AST/DFG topology.
- **Not supported:** adaptive gating provides a reproducible advantage over sequence only.
- **Not evaluated:** frozen official-test performance, external-dataset transfer, other published detectors, industrial deployment performance, and human-validated graph correctness.

## Appendix D. Exact graph-removal diagnostic ledger

Each row summarizes 32 batches and 512 tune examples, including 63 positives. `Mean |delta|` averages the per-batch mean absolute logit change. `Max |delta|` is the largest example-level absolute change reported across batches. Spearman is averaged across batches. Gate SD averages all reported layer-by-batch gate standard deviations.

| Checkpoint/condition | Mean \|delta\| | Max \|delta\| | Mean Spearman | Mean gate SD |
|---|---:|---:|---:|---:|
| Fixed, 400 steps, seed 42 | 0.0008056052 | 0.0056512356 | 0.9995404412 | n/a |
| ASTGuard, 400 steps, seed 42 | 0.0005154682 | 0.0056033134 | 0.9996323529 | 0.0051542879 |
| Fixed, one epoch, seed 42 | 0.0017636717 | 0.0117294788 | 1.0000000000 | n/a |
| ASTGuard authentic, one epoch, seed 42 | 0.0017508380 | 0.0174160004 | 0.9998161765 | 0.0164450660 |
| ASTGuard batch-shuffled, one epoch, seed 42 | 0.0019198086 | 0.0156322718 | 0.9999080882 | 0.0125085175 |
| ASTGuard length-matched shuffled, one epoch, seed 42 | 0.0020486113 | 0.0342469811 | 0.9995404412 | 0.0110034862 |
| ASTGuard authentic, one epoch, seed 123 | 0.0017379759 | 0.0104288459 | 0.9999080882 | 0.0152159014 |
| ASTGuard authentic, one epoch, seed 456 | 0.0004956651 | 0.0065710694 | 0.9998161765 | 0.0065502595 |
| ASTGuard shuffled, one epoch, seed 123 | 0.0014045395 | 0.0334187746 | 1.0000000000 | 0.0129091939 |
| ASTGuard shuffled, one epoch, seed 456 | 0.0008435126 | 0.0079708099 | 0.9998161765 | 0.0084191142 |
| Fixed, one epoch, seed 123 | 0.0009277290 | 0.0489542484 | 0.9998161765 | n/a |
| ASTGuard authentic, multi-epoch seed 42 best checkpoint | 0.0005834003 | 0.0194698572 | 0.9998161765 | 0.0162026763 |
| ASTGuard shuffled, multi-epoch seed 42 best checkpoint | 0.0002765457 | 0.0083277225 | 0.9998161765 | 0.0128118000 |
| Strong ASTGuard authentic, seed 42 | 0.0342870832 | 0.2570326626 | 0.9977941176 | 0.2829755984 |
| Strong ASTGuard authentic, seed 123 | 0.0355578481 | 0.3516298532 | 0.9971507353 | 0.2862422045 |
| Strong ASTGuard authentic, seed 456 | 0.0164343310 | 0.2227285504 | 0.9975183824 | 0.2968381362 |
| Strong ASTGuard shuffled, seed 42 | 0.0114645030 | 0.0888906121 | 0.9976102941 | 0.2625052184 |
| Strong ASTGuard shuffled, seed 123 | 0.0187584952 | 0.1705675125 | 0.9975183824 | 0.2795233552 |
| Strong ASTGuard shuffled, seed 456 | 0.0122305188 | 0.0939409733 | 0.9983455882 | 0.2785882864 |
| Strong fixed, seed 42 | 0.0215725006 | 0.2752729058 | 0.9956801471 | n/a |
| Strong fixed, seed 123 | 0.0080217316 | 0.1493283510 | 0.9988051471 | n/a |
| Strong fixed, seed 456 | 0.0068721900 | 0.0766075850 | 0.9982536765 | n/a |

## Appendix E. Complete remote training-run ledger

This ledger accounts for all 38 remote training directories. AP and loss vectors are in epoch order. Step vectors are cumulative optimizer steps. The term `authentic` means no training-time donor substitution, even where a resolved config retains the collator's default scope field.

| Run directory | Condition | Seed | Beta init | New-module LR multiplier | Steps | Tune AP | Train loss |
|---|---|---:|---:|---:|---|---|---|
| `20260928T020828Z-1f496c262c-42-e6d20b` | fixed, authentic, 400-step probe | 42 | 0.05 | 1 | 400 | 0.0967785533662579 | 0.8167719595477684 |
| `20260928T030536Z-f5e3012b42-42-99f3fd` | ASTGuard, authentic, 400-step probe | 42 | 0.10 | 1 | 400 | 0.10275438274347783 | 0.7924885131325573 |
| `20260928T194332Z-a3add681e4-42-c70360` | fixed, authentic | 42 | 0.05 | 1 | 4424 | 0.13855750636559 | 0.8077981698076765 |
| `20260928T223449Z-595b8259be-42-059b20` | ASTGuard, authentic | 42 | 0.10 | 1 | 4424 | 0.22986384147380423 | 0.764939130174694 |
| `20261002T002704Z-10a4d58c81-42-0721ca` | ASTGuard, batch-shuffled | 42 | 0.10 | 1 | 4424 | 0.1571056590476416 | 0.7598504408745568 |
| `20261002T162739Z-188abddcd7-42-b243c4` | ASTGuard, length-matched shuffled | 42 | 0.10 | 1 | 4424 | 0.15109783290087 | 0.8271630489855308 |
| `20261002T213440Z-361b27e4c7-123-347aa2` | ASTGuard, authentic | 123 | 0.10 | 1 | 4424 | 0.2548552529139805 | 0.7381567183604101 |
| `20261002T224028Z-18c9d5041b-123-1e2759` | ASTGuard, length-matched shuffled | 123 | 0.10 | 1 | 4424 | 0.24023522569199737 | 0.7448330302867227 |
| `20261002T234251Z-37b37c664c-123-90184e` | fixed, authentic | 123 | 0.05 | 1 | 4424 | 0.1538930658806252 | 0.7479731857134269 |
| `20261003T000653Z-1de43bc6cf-456-ad39b8` | ASTGuard, authentic | 456 | 0.10 | 1 | 4424 | 0.1173138748935871 | 0.7823631905768236 |
| `20261003T012836Z-cd70002d1e-456-95d345` | ASTGuard, length-matched shuffled | 456 | 0.10 | 1 | 4424 | 0.2595036124880651 | 0.7790484555344844 |
| `20261003T013155Z-cbb94b0aa4-456-0f135d` | fixed, authentic | 456 | 0.05 | 1 | 4424 | 0.1776649077861526 | 0.758890996886313 |
| `20261003T031754Z-61a22fd254-42-fb6907` | ASTGuard, authentic, multi-epoch | 42 | 0.10 | 1 | 4424 / 8848 / 13272 / 17696 | 0.20637423531510224 / 0.22817122373373902 / 0.21076057347136667 / 0.20769895205305844 | 0.7859812396041513 / 0.779629245507798 / 0.7554045263129542 / 0.7135227999686653 |
| `20261003T034858Z-0ded33e5d2-42-12b5ac` | ASTGuard, length-matched shuffled, multi-epoch | 42 | 0.10 | 1 | 4424 / 8848 / 13272 / 17696 | 0.18035885239203378 / 0.21918830171557643 / 0.20166420613040356 / 0.2014683559359908 | 0.8136001421094696 / 0.7694990450310157 / 0.7615050548585471 / 0.7010956252496016 |
| `20261003T161149Z-b4a872948b-42-5bbaa7` | strong ASTGuard, authentic | 42 | 1.0 | 50 | 4424 | 0.23509716265020342 | 0.8089883152845851 |
| `20261003T161600Z-b0949dd9bc-42-3ec918` | strong ASTGuard, length-matched shuffled | 42 | 1.0 | 50 | 4424 | 0.13824628477565282 | 0.8454787446387197 |
| `20261003T161824Z-bb2458902e-42-d3c284` | strong fixed, authentic | 42 | 0.5 | 50 | 4424 | 0.23404115841864762 | 0.8005777254371086 |
| `20261003T182907Z-1f297d07fa-42-204fbd` | sequence only, default | 42 | 0.0 | 1 | 4424 | 0.2057025192636403 | 0.8239701118626808 |
| `20261003T193738Z-feab4f41f5-42-f8d836` | sequence only, strong optimizer | 42 | 0.0 | 50 | 4424 | 0.11866828509896722 | 0.7957825899241975 |
| `20261003T194102Z-f95f747ce2-123-941f6d` | strong ASTGuard, authentic | 123 | 1.0 | 50 | 4424 | 0.14654705045504712 | 0.8274227847954717 |
| `20261003T203659Z-96306587a5-123-ea9d77` | strong ASTGuard, length-matched shuffled | 123 | 1.0 | 50 | 4424 | 0.22706041814473396 | 0.7777024375318281 |
| `20261003T203915Z-a7a40dc191-123-7fb00c` | strong fixed, authentic | 123 | 0.5 | 50 | 4424 | 0.1119690776380224 | 0.8439690280944147 |
| `20261003T214016Z-a31b0330d8-123-d01874` | sequence only, default | 123 | 0.0 | 1 | 4424 | 0.13242610854866652 | 0.7654274375678977 |
| `20261003T225017Z-7912775d42-123-cdb3ca` | sequence only, strong optimizer | 123 | 0.0 | 50 | 4424 | 0.2556018898520549 | 0.795150884577799 |
| `20261003T234442Z-f60ae0a179-456-911516` | strong ASTGuard, authentic | 456 | 1.0 | 50 | 4424 | 0.22353945378395434 | 0.8199299937428661 |
| `20261003T234724Z-0083e6af2d-456-01f83b` | strong ASTGuard, length-matched shuffled | 456 | 1.0 | 50 | 4424 | 0.24571557979044378 | 0.7961381011788669 |
| `20261004T004143Z-0b36419e15-456-20d40f` | strong fixed, authentic | 456 | 0.5 | 50 | 4424 | 0.11680760757987975 | 0.8366872433914951 |
| `20261004T005342Z-2f952d020d-456-8bd385` | sequence only, default | 456 | 0.0 | 1 | 4424 | 0.2491295878448513 | 0.8030365275182767 |
| `20261004T025927Z-4125af0f69-456-5d0900` | sequence only, strong optimizer | 456 | 0.0 | 50 | 4424 | 0.22545965466691592 | 0.860300557170226 |
| `20261004T190617Z-35fd62ffcc-42-b479a8` | null-campaign sequence only | 42 | 0.0 | 10 | 4424 | 0.23734126262263966 | 0.7839175359833147 |
| `20261004T190827Z-2f7075de5b-42-f0808d` | null-centered adapter | 42 | 1.0 | 10 | 4424 | 0.22587391093810827 | 0.8065522962421264 |
| `20261004T190831Z-6e540236c3-42-07e38c` | uncentered adapter | 42 | 1.0 | 10 | 4424 | 0.1403741784436247 | 0.767222406803879 |
| `20261004T191257Z-38e7fb41fb-123-7edf43` | null-campaign sequence only | 123 | 0.0 | 10 | 4424 | 0.21959940437413653 | 0.7679904742571468 |
| `20261004T211554Z-0940fcb013-123-53b16b` | uncentered adapter | 123 | 1.0 | 10 | 4424 | 0.16430661837575775 | 0.8218839454433133 |
| `20261004T212206Z-a3e71d7ef0-123-3ff9b7` | null-centered adapter | 123 | 1.0 | 10 | 4424 | 0.13043025129127117 | 0.7889349004307232 |
| `20261004T222703Z-b67ee2edb7-456-7c0e9b` | null-campaign sequence only | 456 | 0.0 | 10 | 4424 | 0.2390053202436881 | 0.817074088567196 |
| `20261005T003156Z-37e2ab9a2c-456-e2178c` | uncentered adapter | 456 | 1.0 | 10 | 4424 | 0.2151716910404553 | 0.784117196216773 |
| `20261005T003640Z-b594c1241e-456-697d18` | null-centered adapter | 456 | 1.0 | 10 | 4424 | 0.2558334095167292 | 0.7863221859903762 |

## References to resolve into venue format

1. *Are We Learning the Right Features? A Framework for Evaluating Structural and Semantic Features in Vulnerability Detection.* ICSE 2025. arXiv:2501.13291.
2. *Interpreters for GNN-based Vulnerability Detection.* ISSTA 2023. DOI: 10.1145/3597926.3598145.
3. *CFExplainer: Counterfactual Explanations for Graph Neural Network-based Vulnerability Detection.* arXiv:2404.15687.
4. *PrimeVul: A Benchmark for AI-based Vulnerability Detection.* arXiv:2403.18624.
5. *GraphFramEx: Towards Systematic Evaluation of Explainability Methods for Graph Neural Networks.* PMLR 198, 2022.
6. *NatGVD: Natural Graph-based Vulnerability Detection.* arXiv:2510.04987.
