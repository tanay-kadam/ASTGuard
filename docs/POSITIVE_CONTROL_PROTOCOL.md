# Topology-reliance positive control protocol

Status: frozen before training on 2026-10-06.

## Hypothesis and falsification

If the graph-reliance audit is sensitive to genuine topology-token dependence,
then an authentic-graph adapter will learn a paired synthetic task whose label is
encoded only by AST endpoint/token alignment, measured by tune average precision
(AP) and same-checkpoint graph interventions.

The hypothesis is falsified if any seed fails any primary success rule below. A
failed control must be reported; it cannot be discarded or redefined post hoc.

## Independent variable and controls

The only condition-level change is the structural information available during
training:

1. authentic AST-token alignment with the graph-response adapter;
2. the identical adapter trained with fixed length-matched donor graphs; or
3. sequence-only CodeBERT with an optimization-matched classifier.

Seeds are 42, 123, and 456. All conditions use the same generated rows, split,
backbone revision, effective batch size, optimizer family, backbone learning
rate, new-module multiplier, evaluation code, and 512-step budget.

## Dataset and label construction

Each example contains 24 nonspecial tokens: six occurrences of each of four
token types. For every generated token sequence, two rows are emitted with
identical `input_ids`, attention masks, token positions, token counts, sequence
length, and component ID but opposite labels and different AST edges.

- Positive graphs contain four within-type directed cycles. Every structural
  edge therefore connects equal token types.
- Negative graphs contain four alternating directed cycles: two over token types
  A/B and two over C/D. Every structural edge therefore connects different token
  types. Both labels therefore have the same unlabeled topology: four directed
  cycles of six nodes each.
- Every nonspecial token has exactly one incoming and one outgoing AST edge in
  both labels. DFG is empty in both labels.

Consequently, sequence-only inputs occur with both labels and cannot predict the
target above chance. Graph size, density, per-token degree, sequence length,
token counts, and class balance are also identical across labels. The estimand is
topology-token alignment, matching the paper's bounded claim; it is not a claim
about program semantics.

The frozen split contains 2,048 paired train components (4,096 rows) and 512
paired tune components (1,024 rows). Generated token sequences and component IDs
are disjoint across train and tune. The data-generation seed is 20261006.

## Leakage audit

The generator rejects repeated token sequences across components or splits. It
verifies paired opposite labels, identical paired sequence inputs, balanced
classes, disjoint components, one-in/one-out AST degree for every eligible node,
fully homophilic positive edges, fully heterophilic negative edges, empty DFG,
and the frozen manifest/preprocessing hashes. Sample IDs and component IDs are
metadata and are never model inputs.

## Metrics and primary success rules

AP is primary to match the paper; ROC-AUC is retained as a diagnostic. The
positive control passes only if all three seeds satisfy all of these rules:

1. authentic graph-adapter tune AP is at least 0.90;
2. authentic-minus-sequence tune AP is at least +0.30;
3. authentic-minus-shuffled tune AP is at least +0.30;
4. replacing the authentic graph with an empty graph in the same checkpoint
   reduces AP by at least 0.30; and
5. replacing it with a degree-matched null graph reduces AP by at least 0.20.

Every per-seed result is reported. Means and sample standard deviations are
secondary summaries, not substitutes for the all-seeds rules.

## Ablations and alternative explanations

The sequence-only condition rules out token, position, and sequence-length
leakage. Length-matched shuffled training rules out architecture capacity and
graph density. Empty-graph intervention tests dependence on the structural path.
Degree-matched null substitution tests endpoint/token alignment while retaining
per-token in/out degree. Exact paired construction, held-out sequences, raw
prediction retention, and recomputation rule out label imbalance, split overlap,
best-seed selection, and metric transcription as alternative explanations.

## Artifacts

The campaign preserves the generator parameters and manifest, generated JSONL
hashes, resolved configs, exact commands, environments, all checkpoints and
predictions, per-seed intervention reports, GPU provenance, logs, status records,
and a machine-generated pass/fail summary. The official PrimeVul test role is not
used by this synthetic development control.
