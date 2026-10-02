# Stage 0 chat summary and reasoning (for continuing on another PC)

Read this together with `docs/STAGE0_HANDOFF.md`. This file records what was done, why, and what was decided, so a fresh agent can continue with the same thinking.

## 1. Goal
ASTGuard adds AST/DFG-derived structural attention bias to a CodeBERT vulnerability detector (PrimeVul, C functions). The "structure-usage" study asks: do these models actually use graph topology, or do they just gain capacity from the extra modules? Stage 0 is a cheap diagnostic gate before the expensive Stage 1 (33 runs of graph interventions, about 14h each at 5 epochs).

## 2. Setup facts
- Lab machine: `ssh astguard-lab` (tkadam@seeklab-01.ece.ncsu.edu), repo at `~/ASTGuard`, venv `.venv`. It is a heavily shared machine, so timings vary.
- Structural layers were changed to (2,5,8,10). Layer 11 cannot influence the CLS logit. (2,5,8,11) remains a named ablation.
- Data: P_clean manifest minus 5 pathological records (two ~480KB mis-parsed tables and three others that stalled AST/DFG construction). Result: `artifacts/audits/P_clean_stage0.json`, 186,893 records. The manifest's embedded file_hash was not recomputed. This is a Stage-0-only manifest, not a release manifest.
- `configs/structure_usage/base.yaml` cache_hash had to be updated to `435aff72...` because the preprocessing hash includes the SHA256 of source files that had been edited.
- Training config defaults: 5 epochs, effective batch 32 (microbatch 4 x accumulation 8). One epoch = 4424 optimizer steps; full 5-epoch training = 22,120 steps.
- Training logs only append once per epoch or at the max-steps boundary, so a long run looks silent. That is by design, not a hang.
- Windows PowerShell mangles inline ssh commands (quotes, `$?`, heredocs, pipes to grep). Write scripts to files and sync them, or use single-quoted ssh commands. Lab file sync used base64 over ssh; with the branch pushed, `git pull` on the lab is simpler.

## 3. What was run
1. Cache warming and feature registry on the lab (about 1.5h for the registry because it hashes ~45GB and counts lines).
2. 400-step probes of `ast_dfg_fixed` and `astguard`, then `scripts/diagnose_structure_sensitivity.py` on both checkpoints.
3. After seeing the 400-step signal, the user chose to run a longer probe: one full epoch (4424 steps) each, using `*_stage0fullprobe.yaml` configs and `scripts/stage0_fullprobe.sh`.

Timing of the 1-epoch run: `ast_dfg_fixed` 2h53m, `astguard` 2h52m, diagnostics 7 min.

## 4. Results
| run | steps | tune_ap | mean abs logit delta (real vs empty graph) | Spearman real vs empty |
|---|---|---|---|---|
| ast_dfg_fixed | 400 | 0.0968 | 0.00081 | 0.9995 |
| astguard | 400 | 0.1028 | 0.00052 | 0.9996 |
| ast_dfg_fixed | 4424 | 0.1386 | 0.00176 | 1.0000 |
| astguard | 4424 | 0.2299 | 0.00175 | 0.9998 |

- Run dirs on the lab: fixed `runs/20260928T194332Z-a3add681e4-42-c70360`, astguard `runs/20260928T223449Z-595b8259be-42-059b20`.
- Beta and gate gradient norms stay around 1e-4 to 1e-3, against a total gradient norm of about 10 to 14.
- Gate values stay near 0.5. Their std grew from about 0.003-0.010 (400 steps) to 0.012-0.024 (1 epoch), so the gates are learning a little.
- Diagnostic JSONs are on the lab in `artifacts/audits/diagnostics/{stage0,fullprobe}_*_trained.json`. The aggregation script was `scripts/_fullprobe_compare.py` (untracked, local).

## 5. Interpretation
- At 1 epoch `astguard` beats `ast_dfg_fixed` by +0.091 AP (about 66% relative), up from +0.006 at 400 steps.
- Yet deleting the whole graph at inference barely changes predictions in either model.
- Code facts: `ast_dfg_fixed` is mode "fixed" (96 structural params, no gate). `astguard` is mode "adaptive" with `RelationGate`, 73,920 structural params. The gate is computed only from each token's hidden state; it never looks at the edges. Both use the same graph.
- So the likely story is that the AP gain comes from the learned gate (extra capacity), not from using graph topology. This is a hypothesis, not yet shown.

## 6. Control decision
- Considered `query_capacity_matched`. It is capacity-matched to `edge_gated_astguard` (221,376 structural params, `EdgeRelationGate`), not to `astguard`. So it is not a clean control for `astguard`. Its configs exist but should not be treated as the answer.
- Chosen control (user selected it): train `astguard` with each example's graph replaced by another example's graph within the batch, training only. Same architecture and params; tune evaluation uses real graphs.
  - Config: `configs/structure_usage/astguard_shuffled_graphs_stage0fullprobe.yaml` (1 epoch, 4424 steps)
  - Code: `model.shuffle_training_graphs` in `astguard/config.py`; `StructuralCollator(shuffle_graphs=...)` in `astguard/data/collate.py`; wired in `astguard/models/factory.py`.
  - A derangement permutation is used, seeded from run seed, epoch, and a call counter.
  - Unit test of the collator passed locally (tokens and labels unchanged, graphs permuted, no fixed points).
  - A full model forward on the Windows box failed in the plain RoBERTa attention path (transformers version mismatch), unrelated to this change. Smoke-test on the lab before the long run.
- How to read the result: shuffled AP near 0.23 means the gain is capacity, not topology. Shuffled AP near 0.14 means real topology helps during training. Between the two is ambiguous.

## 7. Caveats
- Only 1 epoch of a 5-epoch protocol. Both models are undertrained (AP 0.14 / 0.23, still rising at 400 steps).
- Single seed per variant, so the +0.091 gap has no error bars.
- The empty-graph test only says removing all edges has little effect. It does not test whether the specific real edges matter versus plausible wrong ones; the shuffle control does.

## 8. Time estimates (measured about 2h50m per epoch)
| plan | time |
|---|---|
| shuffle control, 1 epoch + smoke test + diagnostics | ~3.5h |
| same, 3 seeds, sequential | ~9-10h |
| `astguard` + shuffled, 3 epochs | ~17h |
| `astguard` + shuffled, 5 epochs | ~28h |
| Stage 1 (33 runs x 5 epochs) | ~460 GPU-hours |
Whether the lab can run jobs on several of its 8 GPUs in parallel was not checked.

## 9. Next steps
1. `git fetch && git checkout stage0-shuffle-control`, then `git pull` on the lab repo.
2. Smoke-test the shuffled config with a tiny `max_optimizer_steps` on the lab.
3. Launch the 1-epoch shuffled run in tmux, then run `scripts/diagnose_structure_sensitivity.py --config configs/structure_usage/astguard.yaml --checkpoint <run>/checkpoints/best.safetensors` against it.
4. Compare tune_ap from `runs/<dir>/train_log.jsonl` with 0.2299 and 0.1386.
5. Decide: extend to more epochs and seeds, proceed to Stage 1, or pivot to the capacity-confound / null-centered analysis angle.

State at handoff: nothing is running on the lab. The user's other PC may have started its own run; confirm which config it is running before launching a duplicate.
