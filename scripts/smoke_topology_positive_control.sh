#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate
export TOKENIZERS_PARALLELISM=false

GPU_INDEX="${1:-0}"
DATA_ROOT="data/positive_control/v1"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="artifacts/release_gates/positive_control_smoke/$STAMP"
mkdir -p "$OUT" "runs/positive_control_smoke"

if [[ ! -f "$DATA_ROOT/manifest.json" ]]; then
  python scripts/generate_topology_positive_control.py --output-root "$DATA_ROOT" > "$OUT/generation.log"
fi

CUDA_VISIBLE_DEVICES="$GPU_INDEX" python -m astguard.train \
  --config configs/positive_control/graph_adapter_smoke.yaml \
  --features "$DATA_ROOT/train.jsonl" \
  --tune-features "$DATA_ROOT/tune.jsonl" \
  --seed 42 --runs-root runs/positive_control_smoke > "$OUT/train.log" 2>&1

RUN_DIR="$(tail -n 1 "$OUT/train.log")"
python - "$RUN_DIR" "$OUT/smoke_verification.json" <<'PY'
import json, pathlib, sys
run = pathlib.Path(sys.argv[1])
status = json.loads((run / "status.json").read_text())
provenance = json.loads((run / "provenance.json").read_text())
selection = json.loads((run / "checkpoint_selection.json").read_text())
report = {
    "run_dir": str(run),
    "status": status.get("status"),
    "device": provenance.get("hardware", {}).get("device"),
    "device_name": provenance.get("hardware", {}).get("device_name"),
    "optimizer_steps": provenance.get("optimizer_steps"),
    "selected_tune_ap": selection.get("best_value"),
    "checkpoint_exists": (run / "checkpoints" / "best.safetensors").is_file(),
}
pathlib.Path(sys.argv[2]).write_text(json.dumps(report, indent=2) + "\n")
if report["status"] != "complete" or report["device"] != "cuda" or report["optimizer_steps"] != 2 or not report["checkpoint_exists"]:
    raise SystemExit(json.dumps(report))
print(json.dumps(report, indent=2))
PY

