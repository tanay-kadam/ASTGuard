# Stage 0 results (development, tune split only)

All numbers are tune-split average precision (AP) after 1 epoch (4,424 optimizer steps,
effective batch 32) unless stated. The official test split was not touched.
Shuffled controls swap graphs at training time only (length-matched donors via
`astguard/data/graph_donors.py`); tune and diagnostics always use the real graphs.

| condition | seed 42 | seed 123 | seed 456 | mean |
|---|---|---|---|---|
| `ast_dfg_fixed` | 0.1386 | 0.1539 | 0.1777 | 0.157 |
| `astguard`, real graphs | 0.2299 | 0.2549 | 0.1173 | 0.201 |
| `astguard`, length-matched shuffled graphs | 0.1511 | 0.2402 | 0.2595 | 0.217 |

Seed 42 also: batch-level shuffled `astguard` 0.1571 (superseded by the length-matched
control, because batch shuffling can drop edges or place them on special tokens).

5 epochs, seed 42: real graphs 0.206 / 0.228 / 0.211 / 0.208 (stopped after epoch 4);
shuffled graphs 0.180 / 0.219 / 0.202 / (see run logs).

## Findings

1. Seed-to-seed spread is about 0.14 AP for `astguard`, far larger than the 0.01 AP
   margin of hypothesis H1. The seed-42-only reading "real topology matters" did not replicate.
2. Shuffled graphs match real graphs on average, so topology is not what separates the models.
3. Diagnostics on six checkpoints: removing the graph at inference changes the logit by
   0.001 to 0.005 on average with Spearman 1.0 vs the real-graph ranking; gates stay at
   about 0.50 with std about 0.01; beta gradients are about 1e-4. The structural pathway is
   effectively inert at the default recipe.

## Likely cause (hypothesis, tested in Phase B)

`beta_init = 0.10` with gates at 0.5 gives a bias of about 0.05 against attention scores
of several units, and `new_module_lr_multiplier = 1` lets beta move at most about the
backbone LR (2e-5) per step. The default recipe therefore cannot make structure matter.
The apparent 0.05 AP advantage of gated models over `ast_dfg_fixed` has no
`sequence_only` reference and may be noise (Phase A).

## Next

Phase A adds `sequence_only` (3 seeds). Phase B repeats real / shuffled / fixed /
sequence_only with `beta_init` 1.0 (0.5 for fixed) and `new_module_lr_multiplier = 50`.
Pre-registered checks: structure used (mean |empty-graph logit change| >= 0.05 and gate
std > 0.05) and topology matters (real minus shuffled AP positive on all 3 seeds, mean >= 0.02).
