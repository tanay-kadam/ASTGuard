# Chat summary: Stage 0 through Phase A/B (structure-usage study)

This document reconstructs the full conversation that ran the Stage 0 structure-usage study of ASTGuard on the lab server, diagnosed why structure was unused, designed and executed a follow-up (Phases A and B), and interpreted what that means for publication. Dates are local Eastern Time unless noted. Tune-split average precision (AP) is the only ranking metric used. The official PrimeVul test set was never opened.

Lab: `tkadam@seeklab-01.ece.ncsu.edu`, repo `~/ASTGuard`, venv `.venv`. Local workspace: `C:\Users\kadam\AST`. GitHub repo is ASTGuard (`tanay-kadam/ASTGuard`). Local branch used for the length-matched shuffle work: `stage0-length-matched-shuffle`. Commit of that work: `c571a47`. The lab copy of the same code was `scp`'d and is not necessarily at the same git hash.

---

## 1. The scientific question

ASTGuard is CodeBERT with an additive structural attention bias \(\beta \cdot g \cdot M\) on selected encoder layers (Stage 0 used layers 2, 5, 8, 10; the campaign default 2, 5, 8, 11 is dead for CLS because the classification head reads only position 0 and special tokens have no structural edges).

Two implemented variants were the main Stage 0 comparison:

| Variant | Mechanism | Extra structural params |
|---|---|---|
| `ast_dfg_fixed` | learned \(\beta\) only, no gate | 96 |
| `astguard` (query/adaptive) | `RelationGate(h_i)`, never sees edges | 73,920 |

Related but not the Stage 0 primary comparison: `edge_gated_astguard` (221,376 params, endpoint-conditioned gates) and `query_capacity_matched` (parameter-count match to the edge model, not a clean control for query `astguard`).

**H1 (from earlier protocol thinking):** `astguard` beats `ast_dfg_fixed` by at least 0.01 AP, attributed to structure, under a frozen protocol, 5 seeds. Official test locked.

**Stage 0 question actually asked in this chat:** does `astguard`'s gain over `ast_dfg_fixed` come from graph topology or from the gate's extra capacity?

The user started with `docs/STAGE0_HANDOFF.md`: run this study on the lab; they did not know how to set up SSH and asked the agent to do it.

---

## 2. Lab access and operational constraints

- An SSH key was generated locally (`~/.ssh/astguard_agent`, comment `cursor-agent-astguard`). The user authorized it on the lab. They can revoke it by removing that line from `~/.ssh/authorized_keys`.
- PowerShell repeatedly mangled inline remote commands (`$()`, awk, quotes). The working pattern is: write a `.sh` locally, `scp` it, `ssh ... bash /tmp/...`. Auto-review often blocked SSH/SCP; those calls were retried with explicit user approval.
- Long jobs run in `tmux`. Status lives under `artifacts/release_gates/`.
- Hardware: 8× L40S (~46 GB). Shared lab, high load. `CUDA_VISIBLE_DEVICES` pins GPUs.
- User constraint: **do not use GPUs 2 and 3** (occupied by other work). Later: restrict the Phase A/B queue to **GPUs 0, 1, 4, and 7** (7 only after the leftover 5-epoch job freed it).
- Training: 1 epoch = 4,424 optimizer steps at effective batch 32. `train_log.jsonl` is written at epoch end or at the step cap. Best checkpoint is by tune AP. With `max_optimizer_steps` set, patience is disabled.
- The ~36 GB `train.jsonl` takes about 15–27 minutes to index at startup, which looks like 0% GPU util / almost-empty VRAM even though a job is running.
- Diagnostics: `scripts/diagnose_structure_sensitivity.py` (`--seed` unused). First 512 tune rows, batch 16. Reports gradient reach, empty-graph logit change, gate values. OOM'd several times when other users filled the GPU; rerun on a quieter GPU.
- `pkill -f` once matched the SSH command line and killed a launch; that was relaunched.
- Lab `git checkout` was blocked by a local `preprocess.py` edit (stashed as "pre-shuffle-preprocess") and untracked files (backed up under `~/ASTGuard_untracked_backup_20261001`). `*.bak_pre_shuffle` copies exist on the lab.

---

## 3. Early Stage 0 evidence (before this chat's shuffle work)

From the handoff, same P_clean_stage0 cohort (5 pathological IDs excluded), layers 2, 5, 8, 10:

| run | steps | tune AP | empty-graph mean \|Δlogit\| | Spearman real vs empty |
|---|---|---|---|---|
| `ast_dfg_fixed` | 400 | 0.0968 | 0.00081 | 0.9995 |
| `astguard` | 400 | 0.1028 | 0.00052 | 0.9996 |
| `ast_dfg_fixed` | 4,424 (1 epoch) | 0.1386 | 0.00176 | 1.0000 |
| `astguard` | 4,424 (1 epoch) | 0.2299 | 0.00175 | 0.9998 |

Gates stayed near 0.5 (std ~0.01–0.02). Beta/gate gradient norms ~1e-4 to 1e-3 vs total ~10–14.

Handoff interpretation: `astguard` beats fixed a lot at 1 epoch, but emptying the graph barely changes predictions, so the gain looks like **gate capacity, not topology**. Proposed next step: shuffled-graph control.

Handoff interpretation thresholds (single-seed, later shown to be too tight given noise): shuffled AP ~0.23 → capacity; ~0.14 → topology.

`query_capacity_matched` was correctly rejected as a control for `astguard` (it matches the edge model, 221K vs 74K).

Missing docs: `docs/STRUCTURE_USAGE_PROTOCOL.md` and `docs/MAIN_TRACK_RESEARCH_PROPOSAL.md` were not in git, this machine, or the lab (possibly on another PC). Stage 1 was described as a 33-run, 5-epoch, ~460 GPU-hour matrix in that missing protocol.

---

## 4. Shuffled-graph controls

### 4.1 Batch shuffle (flawed)

Training-time only: derange `relation_masks` within a microbatch (`StructuralCollator._shuffle_batch_graphs`). Tune and diagnostics always use real graphs.

Config: `configs/structure_usage/astguard_shuffled_graphs_stage0fullprobe.yaml`. Script: `scripts/stage0_shuffle_control.sh` (GPU 4 originally).

**Problem:** examples in a batch have different token lengths. Swapping dense masks can drop edges or put edges on padding / the end token. Not length-safe.

Seed 42, 1 epoch: **tune AP 0.1571**.

### 4.2 Length-matched shuffle (the intended control)

New code: `astguard/data/graph_donors.py`.

- Bucket examples by exact token length; merge singletons; Sattolo cycle per bucket so each example gets a **fixed donor** of the same length.
- `transplant_graph` copies donor `edge_projection_groups` / AST / DFG token edges, dropping pairs that touch recipient special tokens or exceed recipient length.
- `GraphDonorDataset` wraps the train set. Stats written to `graph_donors.json`.
- Config: `model.graph_shuffle_scope` ∈ `{batch, length_matched}` (`astguard/config.py`). Factory only enables collator batch-shuffle when scope is `batch`. Train wraps with `GraphDonorDataset` when scope is `length_matched`.
- Tests: `tests/unit/test_graph_donors.py` (5 tests; suite 88 tests locally).
- Configs: `astguard_shuffled_graphs_lenmatched.yaml` (5-epoch) and `..._stage0fullprobe.yaml` (1 epoch / 4,424 steps).
- Script: `scripts/stage0_shuffle_lenmatched.sh`.

Seed 42, 1 epoch: **tune AP 0.1511**. Diagnostics: empty-graph Δ ~0.002, Spearman ~1.0.

At this point (one seed) it looked like shuffled ≈ fixed (0.14–0.15) and real `astguard` ≈ 0.23, i.e. **topology in training**. That reading was later overturned by more seeds.

---

## 5. Seed confirmation and 5-epoch pair

User asked whether extra seeds and 5 epochs were necessary. Answer used: 3 seeds for controls (42, 123, 456), 5 epochs to see if 1-epoch noise settles. Queue: `scripts/stage0_seed_queue.py` (tmux `seedq`), originally hard-coded jobs, `EXCLUDED_GPUS = {2, 3}`, free GPU = used mem < 3,000 MiB and util < 20%, poll 60s, 2-minute stagger between launches, retry once.

Jobs: seeds 123 and 456 × (`astguard`, length-matched shuffled, `ast_dfg_fixed`), then `astguard_5ep_s42` and `shuffled_5ep_s42`. Status: `artifacts/release_gates/seedq/status.jsonl`.

### 5.1 One-epoch results (all three seeds)

| condition | seed 42 | seed 123 | seed 456 | mean |
|---|---|---|---|---|
| `ast_dfg_fixed` | 0.1386 | 0.1539 | 0.1777 | 0.157 |
| `astguard`, real graphs | 0.2299 | 0.2549 | **0.1173** | 0.201 |
| `astguard`, length-matched shuffled | 0.1511 | **0.2402** | **0.2595** | 0.217 |

Also: seed 42 batch-shuffled 0.1571 (superseded).

**This reversed the seed-42 "topology matters" story.** Shuffled mean (0.217) ≥ real mean (0.201). Seed spread for `astguard` is ~0.14 AP (0.117 to 0.255), far larger than H1's 0.01 margin. Seed 456 real `astguard` (0.117) is below the fixed baseline.

### 5.2 Five-epoch, seed 42

`astguard` real (run `20261003T031754Z-61a22fd254-42-fb6907`): epochs 1–4 AP **0.206 / 0.228 / 0.211 / 0.208**, status `complete` after 4 epochs (looks like early stopping; best at epoch 2). Started ~10:46 PM Oct 2 on GPU 5, finished ~9:31 AM Oct 3.

Length-matched shuffled (run `20261003T034858Z-0ded33e5d2-42-12b5ac`): **0.180 / 0.219 / 0.202 / …** still running when diagnostics were rerun; later finished and GPU 7 was reused by Phase A/B. Trailed real graphs by ~0.01–0.026 at matched epochs; both peaked at epoch 2. Single-seed, so not decisive given 0.1+ seed noise.

### 5.3 Diagnostics (default recipe)

Empty-graph mean |Δlogit| typically **0.001–0.005**, Spearman **1.0**. Gates ~**0.50**, std ~**0.01**. Same pattern for real-trained, shuffled-trained, and fixed. Inference does not use the graph.

Several diagnostics OOM'd (`astguard` s123, shuffled s123, `astguard` s456, later `fixed` s456). They were rerun in tmux `rediag` on GPUs 4, 5, 6 and succeeded (exit 0) for the three missing tagged files. `fixed` s456 diagnostics were never queued.

### 5.4 GPU / queue incidents

- Diagnostics OOM on GPU 1 then GPU 7 due to other users; user said rerun on GPU 0.
- GPU 5 and others became busy unexpectedly; always re-check free memory.
- UTC vs local mixup: a "4:30 AM" ETA was actually ~12:30 AM local; corrected.
- User asked repeatedly: is it running, ETAs, which GPUs, can I close my PC, did anything pause, how much is pending/done.

---

## 6. Intermediate scientific discussion (after Stage 0, before Phase B)

The agent initially treated seed 42 shuffled (0.15) vs real (0.23) as evidence that topology matters, then corrected after seeds 123/456.

**Honest Stage 0 conclusion:**

1. Topology is not what separates the models (shuffled ≥ real on average).
2. Seed noise dwarfs a 0.01 AP claim.
3. Empty-graph + gates show an **inert structural pathway** at the default recipe.
4. The ~0.05 mean gap of gated vs `fixed` is **not** established as capacity: there was no `sequence_only` control, extra gate init consumes RNG, and seed noise is huge.

**Should we drop the paper?** No. The pipeline, length-matched shuffle, and inert-pathway finding are usable. What is not supported is "structure-aware attention helps because of the graph."

User had **no deadline or venue**. Agent recommendation: keep the shuffle as the test; try to make structure used (stronger bias / LR / edge gating); if that fails, write an analysis / negative-result paper with more seeds. Novelty audits already said gate granularity alone is not main-track novel (`docs/EDGE_GATING_NOVELTY_AUDIT_AND_DIRECTION.md`, `docs/MAIN_TRACK_NOVELTY_AUDIT.md`).

User asked for a **full-fledged plan** and said the 5-epoch job could be killed if the GPU was needed. The plan **left the 5-epoch run running** (GPUs were otherwise free).

---

## 7. Publication plan (Phases 0–D)

Plan file: `.cursor/plans/astguard_publication_plan_7ef047bf.plan.md` (not edited after creation). Diagnosis of *why* structure is ignored:

- `beta_init = 0.10`, gates start at 0.5 → effective bias ~**0.05** vs attention scores of several units.
- `new_module_lr_multiplier = 1` → beta/gates train at backbone LR **2e-5**. Beta can only drift ~0.05–0.09 per epoch under AdamW.
- Optimizer already splits LRs: `astguard/training/optim.py` treats `.gate.`, `.beta`, `classifier` as "new". Phases A/B are **config-only**.

**Phase 0:** commit length-matched code; write `docs/STAGE0_RESULTS.md`; do not kill 5-epoch run.

**Phase A:** `sequence_only` at the same 4,424-step budget, seeds 42/123/456. If it lands in the same AP range as `astguard`/`fixed`, the gated-vs-fixed gap is noise.

**Phase B (strong setting, all conditions get `new_module_lr_multiplier: 50` so classifier LR is not a confound):**

| condition | `beta_init` | other |
|---|---|---|
| `astguard_strong` | 1.0 | real graphs |
| `astguard_strong_shuffled` | 1.0 | length-matched shuffle |
| `ast_dfg_fixed_strong` | 0.5 | matches initial effective bias of gated (1.0 × 0.5) |
| `sequence_only_strong` | 0 | classifier LR matched |

**Pre-registered checks (fixed before seeing Phase B results):**

- **Structure used:** mean |empty-graph Δlogit| ≥ **0.05** (~25× Stage 0) **and** gate std > **0.05**.
- **Topology matters:** real − shuffled AP **positive on all 3 seeds**, mean ≥ **0.02**.
- **Stability:** if loss blows up or AP falls below `sequence_only`, retry once at multiplier 10 and beta 0.5, log as protocol deviation.

**Phase C:** 5 seeds `[42, 123, 456, 789, 1024]`, 5 epochs, early stopping. ~30 runs, ~330 GPU-hours, ~3 days on 5–6 GPUs. Path:

- If both checks pass → **method paper** (sequence / fixed / query / edge / shuffled query / shuffled edge, strong setting).
- If not → **analysis paper** (default vs strong × sequence / fixed / astguard / shuffled).

**Phase D:** unlock official test **once** for the frozen set; AP, low-FPR recall, pair discrimination, bootstrap CIs; DiverseVul transfer without retraining; report mean ± std and every run.

Working title either way: *Do Pretrained Vulnerability Detectors Use Program Structure? Controlled Shuffle and Ablation Evidence on PrimeVul.*

Launch Phase C only after the user reviews Phase B.

---

## 8. What was implemented from the plan

### 8.1 Code and configs (local commit `c571a47`)

- Length-matched donors, config/factory/train wiring, tests.
- Queue generalized: `--jobs` JSON, `--qname`, later `--allowed-gpus`.
- Jobs file: `scripts/stage0_phaseAB_jobs.json` (15 jobs).
- Configs:
  - `sequence_only_stage0fullprobe.yaml`
  - `sequence_only_strong_stage0fullprobe.yaml`
  - `astguard_strong_stage0fullprobe.yaml`
  - `astguard_strong_shuffled_stage0fullprobe.yaml`
  - `ast_dfg_fixed_strong_stage0fullprobe.yaml`
- `docs/STAGE0_RESULTS.md`
- Scripts: `stage0_seed_queue.py`, `stage0_shuffle_control.sh`, `stage0_shuffle_lenmatched.sh`

Verified locally that configs resolve: sequence_only 0.0 / multiplier 1 or 50; astguard strong beta 1.0 shuffle false; shuffled strong beta 1.0 `length_matched`; fixed strong beta 0.5.

Not pushed. Lab received files via `scp`. `--allowed-gpus` was added after the commit (working tree + lab only).

### 8.2 Phase A/B execution

First launch ~11:30 AM Oct 3 in tmux `phaseab`, 5 GPUs (0, 1, 4, 5, 6). User then said **use 3 GPUs**, clarified as: 3 for the queue plus GPU 7 when free.

Restart ~11:43 AM Oct 3: killed `phaseab`, `pkill` of the new train processes (jobs were still indexing; ~12 minutes lost), `--allowed-gpus 0,1,4,7`. First wave:

| GPU | Job | start |
|---|---|---|
| 0 | `pB_astguard_strong_s42` | 11:43 |
| 1 | `pB_shuffled_strong_s42` | 11:45 |
| 4 | `pB_fixed_strong_s42` | 11:47 |
| 7 | leftover shuffled 5-epoch (old) | already running |

Queue completed **12:35 AM Oct 4** (`queue_complete` 2026-10-04T04:35:29Z). All 15 jobs `job_done`, no retries. Tmux gone. GPUs idle.

Wall-clock: ~13 hours on 3–4 GPUs (GPU 7 joined after the 5-epoch job, ~1:57 PM Oct 3 for `pA_seqonly_s42`).

---

## 9. Phase A/B results (complete)

Tune AP, 1 epoch, 4,424 steps:

| condition | seed 42 | seed 123 | seed 456 | mean |
|---|---|---|---|---|
| `sequence_only`, default (Phase A) | 0.206 | 0.132 | 0.249 | **0.196** |
| `sequence_only`, strong | 0.119 | 0.256 | 0.225 | **0.200** |
| `astguard` strong, real graphs | 0.235 | 0.147 | 0.224 | **0.202** |
| `astguard` strong, shuffled graphs | 0.138 | 0.227 | 0.246 | **0.204** |
| `ast_dfg_fixed` strong | 0.234 | 0.112 | 0.117 | **0.154** |

Empty-graph mean |Δlogit| and gate std (where applicable):

| tag | empty Δ | gate std |
|---|---|---|
| `pB_astguard_strong_s42` | 0.0343 | 0.283 |
| `pB_astguard_strong_s123` | 0.0356 | 0.286 |
| `pB_astguard_strong_s456` | 0.0164 | 0.297 |
| `pB_shuffled_strong_s42` | 0.0115 | 0.263 |
| `pB_shuffled_strong_s123` | 0.0188 | 0.280 |
| `pB_shuffled_strong_s456` | 0.0122 | 0.279 |
| `pB_fixed_strong_s42` | 0.0216 | n/a |
| `pB_fixed_strong_s123` | 0.0080 | n/a |
| `pB_fixed_strong_s456` | 0.0069 | n/a |

Checkpoint betas, seed 42: `astguard` strong layer means ~1.00–1.07 (init 1.0); `fixed` strong ~0.48–0.56 (init 0.5). Gates moved: mean ~0.42–0.60, std ~0.26–0.30 (vs ~0.50 / 0.01 at default).

Losses stayed finite (~0.76–0.85); no blow-up, so the multiplier-10 fallback was **not** triggered.

### Pre-registered decision

| check | outcome |
|---|---|
| Structure used (Δ ≥ 0.05 **and** gate std > 0.05) | **FAIL.** Gate std passes; empty Δ max 0.036. |
| Topology (real−shuffled > 0 on all 3 seeds, mean ≥ 0.02) | **FAIL.** Exact deltas **+0.09685, −0.08051, −0.02218**; mean **−0.00195**. |
| Phase A: gated gap over sequence_only | **No.** Means ~0.202 vs ~0.196 (default) / ~0.200 (strong). |

Seed 42 alone looked favorable (real 0.235 vs shuffled 0.138; structure used more than Stage 0). Seeds 123 and 456 destroyed that pattern. Strong `sequence_only` 0.119 vs default 0.206 on seed 42 shows classifier-LR / seed noise can look like a method effect.

---

## 10. What this means for the project (as stated to the user)

The current method is **not** a structure-aware detector. Do not write a paper claiming AST/DFG attention bias helps vulnerability detection **because of topology**.

- Default recipe: graph ignored at inference.
- Strong recipe: parameters move, but emptying the graph still barely changes logits, and **real graphs do not beat shuffled graphs**.
- `astguard` ≈ `sequence_only` in mean AP. Extra gate params are not a clean capacity win.
- H1 (≥0.01 AP from structure) is not supported at this noise level.

This does **not** mean the work is scrap. There is a full stack, a length-matched shuffle control, and diagnostics most structure papers skip. The supported finding is: **this injection (additive β·g·M on a few layers, CLS head, approximate AST/DFG, CodeBERT, PrimeVul) does not make the model use topology.**

Options:

1. **Analysis paper (Phase C-alt)** — recommended if continuing. Need 5 seeds, 5 epochs, default vs strong, real vs shuffled, then locked test. Frame as controlled negative / diagnostic study.
2. **New mechanism** — hard graph attention, structural pooling, auxiliary graph loss. Different project; do not scale current `astguard` vs `fixed`.
3. **Stop at a tech report** — Stage 0 + A/B only.

User had not yet authorized Phase C or unlocking the test as of the last discussion of meaning.

---

## 11. Architecture and protocol notes that mattered in this chat

- **CLS / last-layer trap:** `FunctionClassificationHead` reads hidden state 0. Special tokens have no structural edges. Last-layer structural bias cannot affect logits. Stage 0 correctly used (2, 5, 8, 10).
- **Query gate never sees edges:** \(g = \sigma(W h_i + b)\). Algebraically it cannot assign different structural coefficients to two neighbors of the same query. Edge gating can; the tiny edge pilot (32 examples, length 64) showed **zero** AP difference among sequence / fixed / query / edge / capacity-matched.
- **Shuffle is train-only:** a shuffled-trained model evaluated on real graphs can still look "good" if it never used the graph, or if it used graph *statistics* (density, length) rather than identity. Empty-graph diagnostics at inference are required to interpret AP.
- **Feature path:** `data/processed/cohorts_stage0/P_clean/ccfd383df4ffc636ecebb995a0ba932be99b7f057cf0f80a5826737d5b97ec39/joined/{train,tune}.jsonl`.
- **All numbers in this chat are tune AP**, not test, not calibrated F1/FPR.

---

## 12. Chronology of user questions (compressed)

Setup and Stage 0 launch → is it running, GPU occupancy, ETAs, epochs for shuffle, extra seeds vs 5 epochs, can I close the PC, shuffle rerun needed, GPU sharing / metric contamination, stuck vs OOM, rerun diag on GPU 0, "are we stashing the project," pending/paused, how much done.

After seed 42 shuffle: interpretation updated, then overturned by more seeds.

Publication: drop the paper? No deadline/venue → full plan → implement plan (commit, configs, queue, launch) → restrict to 3+7 GPUs → time left → results in our favour? (mixed; then complete set: against topology/H1) → what does this mean → **this detailed summary**.

---

## 13. Still pending (not done in this chat)

- Phase C (analysis-path 5-seed 5-epoch campaign) — waiting on user go-ahead.
- Phase D — locked test, DiverseVul, paper draft.
- Commit/push `--allowed-gpus` and any lab-only files; push `c571a47`.
- `docs/STRUCTURE_USAGE_PROTOCOL.md` if it exists on another machine.
- Missing `fixed_s456` default-recipe diagnostics (optional; Phase B `fixed` strong diags exist).
- Human edge-quality review, leakage audit, GraphCodeBERT/LineVul same-setting runs — listed in novelty audit, never executed here.

---

## 14. Numbers cheat sheet

**Default 1-epoch means:** fixed 0.157 · real astguard 0.201 · shuffled 0.217.

**Strong 1-epoch means:** seq 0.200 · real astguard 0.202 · shuffled 0.204 · fixed 0.154.

**Empty-graph |Δlogit|:** default ~0.002 · strong real ~0.016–0.036 · strong shuffled ~0.012–0.019 (all < 0.05 bar).

**Gate std:** default ~0.01 · strong ~0.26–0.30.

**H1 margin:** 0.01 AP. **Observed seed range:** ~0.14 AP.
