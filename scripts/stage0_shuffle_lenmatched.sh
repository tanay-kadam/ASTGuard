#!/bin/bash
# Stage 0 length-matched shuffled-graph control: each training example gets a fixed
# donor graph from an example with the same token length, then runs the diagnostic.
set -uo pipefail
cd ~/ASTGuard
source .venv/bin/activate
export TOKENIZERS_PARALLELISM=false
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-5}"

LOG=artifacts/release_gates/stage0_shuffle_lenmatched.log
mkdir -p artifacts/release_gates artifacts/audits/diagnostics runs
exec > >(tee -a "$LOG") 2>&1

FEATDIR="data/processed/cohorts_stage0/P_clean/ccfd383df4ffc636ecebb995a0ba932be99b7f057cf0f80a5826737d5b97ec39/joined"
TRAIN="$FEATDIR/train.jsonl"
TUNE="$FEATDIR/tune.jsonl"

echo "=== LENMATCH_TRAIN_START $(date -u +%FT%TZ) GPU=$CUDA_VISIBLE_DEVICES ==="
python -m astguard.train --config configs/structure_usage/astguard_shuffled_graphs_lenmatched_stage0fullprobe.yaml \
  --features "$TRAIN" --tune-features "$TUNE" --runs-root runs > /tmp/lenmatched_run_dir.txt
RUN=$(tail -1 /tmp/lenmatched_run_dir.txt)
echo "lenmatched run dir: $RUN"
if [ -z "$RUN" ]; then echo "=== LENMATCH_TRAIN_FAILED ==="; exit 1; fi
echo "=== LENMATCH_TRAIN_DONE $(date -u +%FT%TZ) ==="

echo "=== LENMATCH_DIAG_START $(date -u +%FT%TZ) ==="
python scripts/diagnose_structure_sensitivity.py \
  --config configs/structure_usage/astguard.yaml \
  --features "$TUNE" --checkpoint "$RUN/checkpoints/best.safetensors" \
  --batch-size 16 --max-examples 512 \
  --output artifacts/audits/diagnostics/lenmatched_astguard_trained.json
echo "=== LENMATCH_DIAG_DONE $(date -u +%FT%TZ) ==="
echo "LENMATCHED_RUN=$RUN" >> artifacts/release_gates/fullprobe_run_dirs.txt
echo "=== LENMATCH_COMPLETE $(date -u +%FT%TZ) ==="
