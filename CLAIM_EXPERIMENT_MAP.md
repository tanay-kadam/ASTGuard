# Claim-to-experiment implementation map

| Paper claim | Experiment config / ledger | Implementation | Metric | Baseline | Expected artifact |
|---|---|---|---|---|---|
| Adaptive ranking over fixed | E1, `configs/experiments/main.yaml` | `ASTGuardClassifier` | AP difference | `ast_dfg_fixed` | T2 / `main_results.csv` |
| Full structure over sequence | E1 | structural attention | AP difference | `sequence_only` | T2 |
| Token-specific mechanism | A1/A2/A3 | controls, interventions, rewiring | AP/logit changes | adapter, linear, function gates | T3/F4 |
| Low-FPR benefit | E1 | calibration selector | recall at saved FPR threshold | fixed/sequence | T2 |
| Both relations contribute | E2 | relation selection | AP removal effect | AST-only/DFG-only | T3 |
| Patch discrimination | E6 | pair evaluator | order, margin, PC/PV/PB/PR | all E1 models | T4/F3 |
| Dropout robustness | E7 | robustness transforms | common-range corruption area | ordinary adaptive/fixed | F5 |
| Data efficiency | E4, `fractions.yaml` | nested components | AP/compute curve | sequence/fixed | F2 |
| Cross-dataset transfer | E5 | `SplitBuilder._d_transfer` on joint components; full audit not yet run | AP/fixed-threshold metrics | sequence/fixed/GraphCodeBERT | T5 |
| Held-out projects | E11, `project_transfer.yaml` | `SplitBuilder` P_project | AP/project macro AP | sequence/fixed | T5 |
| Modest overhead | E8, `efficiency.yaml` | benchmark utilities | latency/memory ratio | eager/optimized sequence | T6 |

The ledger is finite and traceable, but missing implementation or execution is
explicit in `IMPLEMENTATION_NOTES.md` and cannot support a claim.
