#!/usr/bin/env bash
set -eu
cd /tmp/astguard_seven_day_20261012
mkdir -p artifacts/seven_day_20261012/holdout
tar -xzf /tmp/astguard_seven_day_normalized_sources_20261012.tar.gz
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false \
  /home/tkadam/ASTGuard/.venv/bin/python -u scripts/seven_day_holdout.py --components \
  > artifacts/seven_day_20261012/holdout/components.log 2>&1
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /home/tkadam/ASTGuard/.venv/bin/python -u scripts/seven_day_holdout.py --features \
  > artifacts/seven_day_20261012/holdout/features.log 2>&1
