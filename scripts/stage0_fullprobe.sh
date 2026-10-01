#!/bin/bash
# Stage 0 "full probe": one full epoch (4424 optimizer steps, vs the earlier
# 400-step sanity probe) for ast_dfg_fixed and astguard, then rerun the
# structure-sensitivity diagnostic against both checkpoints. Cache/registry
# from the earlier Stage 0 run are reused as-is (no rebuild needed).
set -uo pipefail
cd ~/ASTGuard
source .venv/bin/activate
export TOKENIZERS_PARALLELISM=false

LOG=artifacts/release_gates/stage0_fullprobe.log
mkdir -p artifacts/release_gates artifacts/audits/diagnostics runs
exec > >(tee -a "$LOG") 2>&1

FEATDIR="data/processed/cohorts_stage0/P_clean/ccfd383df4ffc636ecebb995a0ba932be99b7f057cf0f80a5826737d5b97ec39/joined"
TRAIN="$FEATDIR/train.jsonl"
TUNE="$FEATDIR/tune.jsonl"
echo "train=$TRAIN tune=$TUNE"

echo "=== FULLPROBE_PHASE1_TRAIN_FIXED_START $(date -u +%FT%TZ) ==="
python -m astguard.train --config configs/structure_usage/ast_dfg_fixed_stage0fullprobe.yaml \
  --features "$TRAIN" --tune-features "$TUNE" --runs-root runs > /tmp/fullprobe_fixed_run_dir.txt
FIXED_RUN=$(tail -1 /tmp/fullprobe_fixed_run_dir.txt)
echo "fixed run dir: $FIXED_RUN"
if [ -z "$FIXED_RUN" ]; then echo "=== FULLPROBE_PHASE1_TRAIN_FIXED_FAILED ==="; exit 1; fi
echo "=== FULLPROBE_PHASE1_TRAIN_FIXED_DONE $(date -u +%FT%TZ) ==="

echo "=== FULLPROBE_PHASE2_TRAIN_ASTGUARD_START $(date -u +%FT%TZ) ==="
python -m astguard.train --config configs/structure_usage/astguard_stage0fullprobe.yaml \
  --features "$TRAIN" --tune-features "$TUNE" --runs-root runs > /tmp/fullprobe_astguard_run_dir.txt
ASTGUARD_RUN=$(tail -1 /tmp/fullprobe_astguard_run_dir.txt)
echo "astguard run dir: $ASTGUARD_RUN"
if [ -z "$ASTGUARD_RUN" ]; then echo "=== FULLPROBE_PHASE2_TRAIN_ASTGUARD_FAILED ==="; exit 1; fi
echo "=== FULLPROBE_PHASE2_TRAIN_ASTGUARD_DONE $(date -u +%FT%TZ) ==="

echo "=== FULLPROBE_PHASE3_DIAGNOSTIC_START $(date -u +%FT%TZ) ==="
python scripts/diagnose_structure_sensitivity.py \
  --config configs/structure_usage/ast_dfg_fixed.yaml \
  --features "$TUNE" --checkpoint "$FIXED_RUN/checkpoints/best.safetensors" \
  --batch-size 16 --max-examples 512 \
  --output artifacts/audits/diagnostics/fullprobe_ast_dfg_fixed_trained.json

python scripts/diagnose_structure_sensitivity.py \
  --config configs/structure_usage/astguard.yaml \
  --features "$TUNE" --checkpoint "$ASTGUARD_RUN/checkpoints/best.safetensors" \
  --batch-size 16 --max-examples 512 \
  --output artifacts/audits/diagnostics/fullprobe_astguard_trained.json
echo "=== FULLPROBE_PHASE3_DIAGNOSTIC_DONE $(date -u +%FT%TZ) ==="

echo "=== FULLPROBE_COMPLETE $(date -u +%FT%TZ) ==="
echo "FIXED_RUN=$FIXED_RUN" >> artifacts/release_gates/fullprobe_run_dirs.txt
echo "ASTGUARD_RUN=$ASTGUARD_RUN" >> artifacts/release_gates/fullprobe_run_dirs.txt
