#!/bin/bash
# Stage 0 shuffled-graph control: train astguard for 1 epoch with training graphs
# shuffled across examples, then run the structure-sensitivity diagnostic.
set -uo pipefail
cd ~/ASTGuard
source .venv/bin/activate
export TOKENIZERS_PARALLELISM=false
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-4}"

LOG=artifacts/release_gates/stage0_shuffle_control.log
mkdir -p artifacts/release_gates artifacts/audits/diagnostics runs
exec > >(tee -a "$LOG") 2>&1

FEATDIR="data/processed/cohorts_stage0/P_clean/ccfd383df4ffc636ecebb995a0ba932be99b7f057cf0f80a5826737d5b97ec39/joined"
TRAIN="$FEATDIR/train.jsonl"
TUNE="$FEATDIR/tune.jsonl"

echo "=== SHUFFLE_TRAIN_START $(date -u +%FT%TZ) GPU=$CUDA_VISIBLE_DEVICES ==="
python -m astguard.train --config configs/structure_usage/astguard_shuffled_graphs_stage0fullprobe.yaml \
  --features "$TRAIN" --tune-features "$TUNE" --runs-root runs > /tmp/shuffle_run_dir.txt
RUN=$(tail -1 /tmp/shuffle_run_dir.txt)
echo "shuffle run dir: $RUN"
if [ -z "$RUN" ]; then echo "=== SHUFFLE_TRAIN_FAILED ==="; exit 1; fi
echo "=== SHUFFLE_TRAIN_DONE $(date -u +%FT%TZ) ==="

echo "=== SHUFFLE_DIAG_START $(date -u +%FT%TZ) ==="
python scripts/diagnose_structure_sensitivity.py \
  --config configs/structure_usage/astguard.yaml \
  --features "$TUNE" --checkpoint "$RUN/checkpoints/best.safetensors" \
  --batch-size 16 --max-examples 512 \
  --output artifacts/audits/diagnostics/shuffle_astguard_trained.json
echo "=== SHUFFLE_DIAG_DONE $(date -u +%FT%TZ) ==="
echo "SHUFFLE_RUN=$RUN" >> artifacts/release_gates/fullprobe_run_dirs.txt
echo "=== SHUFFLE_COMPLETE $(date -u +%FT%TZ) ==="
