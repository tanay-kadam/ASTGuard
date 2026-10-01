# Stage 0 handoff (structure-usage study)

Lab: `ssh astguard-lab` (tkadam@seeklab-01.ece.ncsu.edu), repo at `~/ASTGuard`, venv `.venv`. Nothing is running there now (no tmux sessions).
Run long jobs with `tmux new-session -d -s NAME 'bash scripts/xxx.sh'`; poll logs under `artifacts/release_gates/`.
Tip: PowerShell mangles inline remote commands. Write scripts to files, then sync via git on the lab (`git pull`) or base64 over ssh.

## Results so far (P_clean_stage0 manifest, 5 pathological ids excluded, layers 2,5,8,10)
| run | steps | tune_ap | empty-graph mean abs logit delta | spearman real vs empty |
|---|---|---|---|---|
| ast_dfg_fixed | 400 | 0.0968 | 0.00081 | 0.9995 |
| astguard | 400 | 0.1028 | 0.00052 | 0.9996 |
| ast_dfg_fixed | 4424 (1 epoch) | 0.1386 | 0.00176 | 1.0000 |
| astguard | 4424 (1 epoch) | 0.2299 | 0.00175 | 0.9998 |

Beta/gate gradient norms stay ~1e-4..1e-3 vs total ~10-14; gates stay near 0.5 (std 0.01-0.02).
Reading: astguard (adaptive gate) beats the fixed baseline by a lot at 1 epoch, but removing the whole graph barely changes predictions. The gain looks like gate capacity, not topology. Note `astguard`'s RelationGate depends only on token hidden states, not on edges.

Diagnostics JSONs on lab: `artifacts/audits/diagnostics/{stage0,fullprobe}_*_trained.json`.
Aggregation script: `scripts/_fullprobe_compare.py` (local, untracked).

## Chosen next step: shuffled-graph control (not yet run)
Train `astguard` for 1 epoch (4424 steps) with each example's graph swapped for another example's graph in the batch (training only; tune uses real graphs). Same architecture and params as astguard.
- Config: `configs/structure_usage/astguard_shuffled_graphs_stage0fullprobe.yaml`
- Code: `model.shuffle_training_graphs` (config.py), `StructuralCollator(shuffle_graphs=...)` (data/collate.py), wired in models/factory.py.
- Collator logic unit-tested locally; a full model forward was not verifiable on the Windows box (HF version mismatch), so smoke-test on the lab first.
- Interpretation: if shuffled-trained tune_ap is about 0.23, the gain is capacity, not topology. If it is near 0.14, real topology matters in training.
- Expected cost: about 2h50m training plus 7 min diagnostics.

Steps on the lab:
1. `cd ~/ASTGuard && git pull`
2. Smoke test: run `python -m astguard.train` with the shuffled config and a tiny `max_optimizer_steps` (e.g. copy the config with 3 steps).
3. Copy `scripts/stage0_fullprobe.sh` into a script that trains only the shuffled config, then runs `scripts/diagnose_structure_sensitivity.py --config configs/structure_usage/astguard.yaml --checkpoint <run>/checkpoints/best.safetensors`. FEATDIR is `data/processed/cohorts_stage0/P_clean/ccfd383df4ffc636ecebb995a0ba932be99b7f057cf0f80a5826737d5b97ec39/joined`.
4. Launch in tmux, compare tune_ap in `runs/<dir>/train_log.jsonl`.

## Not recommended
`query_capacity_matched` is capacity-matched to `edge_gated_astguard` (221K structural params), not to `astguard` (74K). Configs for it exist but it is not an apples-to-apples control.

## Later
Stage 1 (33-run graph-intervention matrix) is not started; decide after the shuffle control.
