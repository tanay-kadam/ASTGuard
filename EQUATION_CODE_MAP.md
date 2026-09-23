# Equation-to-code map

| Equation / mechanism | Source | Function/class | Test | Experiment |
|---|---|---|---|---|
| M1 canonical input and offsets | `astguard/alignment/tokenizer.py`, `byte_spans.py` | `CanonicalTokenizer`, `ByteSpanAligner` | `test_alignment.py`, `test_lexical.py` | E1, E10b |
| M2 radius-4 leaf path | `astguard/parsing/relations.py` | `SyntaxRelationBuilder.build` | `test_alignment.py`; manual gold coverage pending | E1, E2, A4 |
| M3 reaching definitions | `astguard/parsing/lowering.py`, `reaching_defs.py` | `extract_dependencies`, `ReachingDefinitions.solve` | `test_lowering.py`, `test_reaching_defs.py`; manual gold pending | E1, E2, A3 |
| M4 directed DFG projection | `astguard/alignment/projection.py`, `parsing/lowering.py` | `RelationProjector.project`, `extract_dependencies` | `test_alignment.py`, `test_lowering.py` | E1, E2 |
| M5 contextual gate | `astguard/models/gates.py` | `RelationGate.forward` | `test_neural.py` | E1, A1, A2, A6 |
| M6 additive structural score | `astguard/models/attention.py` | `StructuralSelfAttention.forward` | `test_neural.py`, `check_pretrained_equivalence.py` | E1, A3, A4 |
| M7 attention output | `astguard/models/attention.py` | `StructuralSelfAttention.forward` | `test_neural.py`, `check_pretrained_equivalence.py` | E1 |
| M8 shared classifier | `astguard/models/heads.py` | `FunctionClassificationHead.forward` | `test_neural.py` | E1 |
| M9 weighted BCE | `astguard/training/engine.py` | `weighted_bce_logits` | `test_neural.py` | E1, A4 |
| M10 lexical edge dropout | `astguard/data/collate.py` | `StructuralCollator` | `test_neural.py` | E1 dropout, E7 |
| M11 AP | `astguard/evaluation/metrics.py` | `average_precision` | `test_metrics.py` | all evaluations |
| M12 calibrated operating point | `astguard/evaluation/thresholds.py` | `ThresholdSelector.fit` | `test_metrics.py` | E1, E5, E7 |
| M13 pairs | `astguard/evaluation/pairs.py` | `evaluate_pairs` | `test_metrics.py` | E6 |

Unit and smoke tests establish engineering behavior; the extraction gate and manual gold review still block scientific release.
