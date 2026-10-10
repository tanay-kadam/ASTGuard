#!/bin/bash
set -uo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate
export TOKENIZERS_PARALLELISM=false
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

DATA_ROOT="data/positive_control/v1"
CAMPAIGN="artifacts/release_gates/positive_control_v1_20261006"
if [[ -e "$CAMPAIGN/started.json" && "${1:-}" != "--resume" ]]; then
  echo "campaign already started: $CAMPAIGN" >&2
  exit 1
fi
if [[ "${1:-}" == "--resume" && -f "$CAMPAIGN/completion.json" ]]; then
  mv "$CAMPAIGN/completion.json" "$CAMPAIGN/completion_before_resume_$(date -u +%Y%m%dT%H%M%SZ).json"
fi
mkdir -p "$CAMPAIGN/logs" "$CAMPAIGN/run_dirs" "$CAMPAIGN/interventions" artifacts/audits
printf '{"status":"running","utc":"%s"}\n' "$(date -u +%FT%TZ)" > "$CAMPAIGN/started.json"
python --version > "$CAMPAIGN/runtime_environment.txt" 2>&1
python -m pip freeze > "$CAMPAIGN/python_environment.txt"
nvidia-smi --query-gpu=index,name,driver_version,memory.total --format=csv,noheader \
  > "$CAMPAIGN/gpu_environment.csv"

if [[ ! -f "$DATA_ROOT/manifest.json" ]]; then
  python scripts/generate_topology_positive_control.py --output-root "$DATA_ROOT" > "$CAMPAIGN/generation.log"
fi

status_line() {
  local tag="$1" phase="$2" status="$3" gpu="$4" seed="$5" config="$6"
  printf '{"tag":"%s","phase":"%s","status":"%s","gpu":%s,"seed":%s,"config":"%s","utc":"%s"}\n' \
    "$tag" "$phase" "$status" "$gpu" "$seed" "$config" "$(date -u +%FT%TZ)" >> "$CAMPAIGN/status.jsonl"
}

run_job() {
  local gpu="$1" condition="$2" seed="$3" config="$4"
  local tag="pc_${condition}_s${seed}"
  local log="$CAMPAIGN/logs/${tag}.log"
  local run_dir=""
  if [[ -f "$CAMPAIGN/run_dirs/${tag}.txt" ]]; then
    run_dir="$(cat "$CAMPAIGN/run_dirs/${tag}.txt")"
    if [[ ! -f "$run_dir/checkpoints/best.safetensors" ]]; then
      echo "Missing checkpoint for saved run: $tag" >&2
      return 1
    fi
  fi
  if [[ -z "$run_dir" ]]; then
  status_line "$tag" train running "$gpu" "$seed" "$config"
  if ! CUDA_VISIBLE_DEVICES="$gpu" python -m astguard.train \
      --config "$config" --features "$DATA_ROOT/train.jsonl" \
      --tune-features "$DATA_ROOT/tune.jsonl" --seed "$seed" --runs-root runs > "$log" 2>&1; then
    status_line "$tag" train failed "$gpu" "$seed" "$config"
    return 1
  fi
  run_dir="$(tail -n 1 "$log")"
  if [[ -z "$run_dir" || ! -f "$run_dir/status.json" || ! -f "$run_dir/checkpoints/best.safetensors" ]]; then
    status_line "$tag" artifact_check failed "$gpu" "$seed" "$config"
    return 1
  fi
  printf '%s\n' "$run_dir" > "$CAMPAIGN/run_dirs/${tag}.txt"
  status_line "$tag" train complete "$gpu" "$seed" "$config"
  fi
  if [[ "$condition" == "authentic" && ! -f "$CAMPAIGN/interventions/${tag}.json" ]]; then
    status_line "$tag" intervention running "$gpu" "$seed" "$run_dir/config.resolved.yaml"
    if ! CUDA_VISIBLE_DEVICES="$gpu" python scripts/evaluate_graph_interventions.py \
        --config "$run_dir/config.resolved.yaml" --features "$DATA_ROOT/tune.jsonl" \
        --checkpoint "$run_dir/checkpoints/best.safetensors" --role tune --batch-size 64 \
        --output "$CAMPAIGN/interventions/${tag}.json" >> "$log" 2>&1; then
      status_line "$tag" intervention failed "$gpu" "$seed" "$run_dir/config.resolved.yaml"
      return 1
    fi
    status_line "$tag" intervention complete "$gpu" "$seed" "$run_dir/config.resolved.yaml"
  fi
}

(run_job 0 authentic 42 configs/positive_control/graph_adapter.yaml || exit 1; \
 run_job 0 shuffled 123 configs/positive_control/graph_adapter_shuffled.yaml || exit 1; \
 run_job 0 sequence 456 configs/positive_control/sequence_only.yaml || exit 1) & p0=$!
(run_job 1 authentic 123 configs/positive_control/graph_adapter.yaml || exit 1; \
 run_job 1 shuffled 456 configs/positive_control/graph_adapter_shuffled.yaml || exit 1) & p1=$!
(run_job 4 authentic 456 configs/positive_control/graph_adapter.yaml || exit 1; \
 run_job 4 sequence 42 configs/positive_control/sequence_only.yaml || exit 1) & p4=$!
(run_job 7 shuffled 42 configs/positive_control/graph_adapter_shuffled.yaml || exit 1; \
 run_job 7 sequence 123 configs/positive_control/sequence_only.yaml || exit 1) & p7=$!

failed=0
for pid in "$p0" "$p1" "$p4" "$p7"; do
  wait "$pid" || failed=1
done
if [[ "$failed" -ne 0 ]]; then
  printf '{"status":"failed","utc":"%s"}\n' "$(date -u +%FT%TZ)" > "$CAMPAIGN/completion.json"
  exit 1
fi

python scripts/summarize_topology_positive_control.py --campaign-root "$CAMPAIGN" \
  --output artifacts/audits/topology_positive_control_v1_summary.json \
  > "$CAMPAIGN/summary.log" 2>&1
summary_status=$?
printf '{"status":"complete","summary_exit_code":%s,"utc":"%s"}\n' \
  "$summary_status" "$(date -u +%FT%TZ)" > "$CAMPAIGN/completion.json"
exit "$summary_status"
