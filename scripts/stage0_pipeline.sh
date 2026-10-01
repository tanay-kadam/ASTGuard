#!/bin/bash
# Stage 0 unattended pipeline for the structure-usage study.
# Runs inside a detached tmux session on astguard-lab so it survives
# disconnects. Each phase writes a clear marker so progress and failures
# are visible in the log.
set -uo pipefail
cd ~/ASTGuard
source .venv/bin/activate
export TOKENIZERS_PARALLELISM=false

LOG=artifacts/release_gates/stage0_pipeline.log
mkdir -p artifacts/release_gates artifacts/launcher runs artifacts/audits/diagnostics
exec > >(tee -a "$LOG") 2>&1

echo "=== STAGE0_PHASE1_WARM_START $(date -u +%FT%TZ) ==="
python scripts/warm_feature_cache.py \
  --plan artifacts/release_gates/registry_plan_stage0.json \
  --variants 0 --views P_clean --workers 110 --progress-every 10000 \
  --report artifacts/release_gates/stage0_cache_warm_report.json
if [ $? -ne 0 ]; then echo "=== STAGE0_PHASE1_WARM_FAILED ==="; exit 1; fi
echo "=== STAGE0_PHASE1_WARM_DONE $(date -u +%FT%TZ) ==="

echo "=== STAGE0_PHASE2_REGISTRY_START $(date -u +%FT%TZ) ==="
python scripts/prepare_feature_registry.py \
  --plan artifacts/release_gates/registry_plan_stage0.json \
  --output-root data/processed/cohorts_stage0 \
  --context artifacts/launcher/stage0_context.json
if [ $? -ne 0 ]; then echo "=== STAGE0_PHASE2_REGISTRY_FAILED ==="; exit 1; fi
echo "=== STAGE0_PHASE2_REGISTRY_DONE $(date -u +%FT%TZ) ==="

FEATDIR=$(python3 -c "
import json
ctx = json.load(open('artifacts/launcher/stage0_context.json'))
entry = next(iter(ctx['feature_registry'].values()))
print(entry['train'].rsplit('/',1)[0])
")
echo "feature dir: $FEATDIR"
TRAIN="$FEATDIR/train.jsonl"
TUNE="$FEATDIR/tune.jsonl"
echo "train=$TRAIN tune=$TUNE"

echo "=== STAGE0_PHASE3_TRAIN_FIXED_START $(date -u +%FT%TZ) ==="
python -m astguard.train --config configs/structure_usage/ast_dfg_fixed_stage0probe.yaml \
  --features "$TRAIN" --tune-features "$TUNE" --runs-root runs > /tmp/stage0_fixed_run_dir.txt
FIXED_RUN=$(tail -1 /tmp/stage0_fixed_run_dir.txt)
echo "fixed run dir: $FIXED_RUN"
if [ -z "$FIXED_RUN" ]; then echo "=== STAGE0_PHASE3_TRAIN_FIXED_FAILED ==="; exit 1; fi
echo "=== STAGE0_PHASE3_TRAIN_FIXED_DONE $(date -u +%FT%TZ) ==="

echo "=== STAGE0_PHASE4_TRAIN_ASTGUARD_START $(date -u +%FT%TZ) ==="
python -m astguard.train --config configs/structure_usage/astguard_stage0probe.yaml \
  --features "$TRAIN" --tune-features "$TUNE" --runs-root runs > /tmp/stage0_astguard_run_dir.txt
ASTGUARD_RUN=$(tail -1 /tmp/stage0_astguard_run_dir.txt)
echo "astguard run dir: $ASTGUARD_RUN"
if [ -z "$ASTGUARD_RUN" ]; then echo "=== STAGE0_PHASE4_TRAIN_ASTGUARD_FAILED ==="; exit 1; fi
echo "=== STAGE0_PHASE4_TRAIN_ASTGUARD_DONE $(date -u +%FT%TZ) ==="

echo "=== STAGE0_PHASE5_DIAGNOSTIC_START $(date -u +%FT%TZ) ==="
python scripts/diagnose_structure_sensitivity.py \
  --config configs/structure_usage/ast_dfg_fixed.yaml \
  --features "$TUNE" --checkpoint "$FIXED_RUN/checkpoints/best.safetensors" \
  --batch-size 16 --max-examples 512 \
  --output artifacts/audits/diagnostics/stage0_ast_dfg_fixed_trained.json

python scripts/diagnose_structure_sensitivity.py \
  --config configs/structure_usage/astguard.yaml \
  --features "$TUNE" --checkpoint "$ASTGUARD_RUN/checkpoints/best.safetensors" \
  --batch-size 16 --max-examples 512 \
  --output artifacts/audits/diagnostics/stage0_astguard_trained.json
echo "=== STAGE0_PHASE5_DIAGNOSTIC_DONE $(date -u +%FT%TZ) ==="

echo "=== STAGE0_PIPELINE_COMPLETE $(date -u +%FT%TZ) ==="
echo "FIXED_RUN=$FIXED_RUN" >> artifacts/release_gates/stage0_run_dirs.txt
echo "ASTGUARD_RUN=$ASTGUARD_RUN" >> artifacts/release_gates/stage0_run_dirs.txt
