# Maintainer validation

These records describe the local packaging checks, not a new training campaign
or independent real-data test. The isolated environment used Python 3.11.16,
Torch 2.5.1, Transformers 4.49.0, NumPy 2.2.6, SciPy 1.15.3 and scikit-learn 1.7.2
on Windows CPU. The metric verifier is also executed by GitHub Actions.

`saved_metrics.json` recomputes all selected/intervention results from the
included predictions. `inference_smoke.json` checks four inputs each for
attention, centered adapter, and ReGVD, including all their graph conditions.
`inference_full_synthetic.json` re-evaluates all 1,024 held-out synthetic inputs
for one centered checkpoint. `repository_tests.json` records the 114-test result.

The complete 42-checkpoint import and GitHub asset receipts are release assets,
produced after all transfers finish. No full 42-run retraining is claimed.
