#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8
CAMPAIGN=artifacts/release_gates/strengthening_20261006
mkdir -p "$CAMPAIGN"
if [[ -e "$CAMPAIGN/started.json" ]]; then
  echo "Campaign already started; preserve prior run evidence." >&2
  exit 1
fi
python scripts/prepare_strengthening_data.py --smoke-only --workers 4 > "$CAMPAIGN/preparation_smoke.log" 2>&1
python scripts/build_strengthening_jobs.py
python scripts/queue_strengthening.py --gpu 5 --smoke > "$CAMPAIGN/smoke.log" 2>&1
python -m pip freeze > "$CAMPAIGN/environment.txt"
nvidia-smi --query-gpu=index,name,driver_version,memory.total --format=csv,noheader > "$CAMPAIGN/gpu_environment.csv"
printf '{"status":"running","jobs":42,"gpus":[5,6],"utc":"%s"}\n' "$(date -u +%FT%TZ)" > "$CAMPAIGN/started.json"
(python scripts/prepare_strengthening_data.py --workers 32 > "$CAMPAIGN/preparation_full.log" 2>&1 || \
  python -c 'from pathlib import Path; Path("artifacts/release_gates/strengthening_20261006/preparation_failed.json").write_text("{\"status\":\"failed\"}")') & prep=$!
python scripts/queue_strengthening.py --gpu 5 --partition 0 > "$CAMPAIGN/worker_0.log" 2>&1 & w0=$!
python scripts/queue_strengthening.py --gpu 6 --partition 1 > "$CAMPAIGN/worker_1.log" 2>&1 & w1=$!
failed=0
for pid in "$prep" "$w0" "$w1"; do wait "$pid" || failed=1; done
python scripts/summarize_strengthening.py > "$CAMPAIGN/summary.log" 2>&1 || failed=1
printf '{"status":"%s","utc":"%s"}\n' "$([[ $failed == 0 ]] && echo complete || echo failed)" "$(date -u +%FT%TZ)" > "$CAMPAIGN/completion.json"
exit "$failed"
