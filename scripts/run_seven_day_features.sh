#!/usr/bin/env bash
set -eu
cd /tmp/astguard_seven_day_20261012
while [ ! -f artifacts/seven_day_20261012/holdout/component_report.json ]; do
  if [ -f artifacts/seven_day_20261012/holdout/failure.json ]; then
    exit 1
  fi
  sleep 30
done
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /home/tkadam/ASTGuard/.venv/bin/python -u scripts/seven_day_holdout.py --features \
  > artifacts/seven_day_20261012/holdout/features.log 2>&1
