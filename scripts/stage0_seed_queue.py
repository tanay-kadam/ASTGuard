#!/usr/bin/env python3
"""Run the Stage 0 seed/epoch confirmation jobs on whichever lab GPUs are idle.

A GPU counts as free only when it has under FREE_MEM_MIB used, low utilization, is not
on the exclusion list, and is not already held by a job this queue started. Jobs are
launched in priority order; failures are retried once.
"""
import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "ASTGuard"
FEATDIR = ROOT / "data/processed/cohorts_stage0/P_clean/ccfd383df4ffc636ecebb995a0ba932be99b7f057cf0f80a5826737d5b97ec39/joined"
QDIR = ROOT / "artifacts/release_gates/seedq"
STATUS = QDIR / "status.jsonl"
EXCLUDED_GPUS = {2, 3}
FREE_MEM_MIB = 3000
FREE_UTIL_PCT = 20
POLL_SECONDS = 60
CFG = "configs/structure_usage/"

CONDITIONS = {
    "fixed": (CFG + "ast_dfg_fixed_stage0fullprobe.yaml", CFG + "ast_dfg_fixed.yaml"),
    "astguard": (CFG + "astguard_stage0fullprobe.yaml", CFG + "astguard.yaml"),
    "shuffled": (CFG + "astguard_shuffled_graphs_lenmatched_stage0fullprobe.yaml", CFG + "astguard.yaml"),
    "astguard_5ep": (CFG + "astguard.yaml", CFG + "astguard.yaml"),
    "shuffled_5ep": (CFG + "astguard_shuffled_graphs_lenmatched.yaml", CFG + "astguard.yaml"),
}

JOBS = [(f"{name}_s{seed}", name, seed) for seed in (123, 456) for name in ("astguard", "shuffled", "fixed")]
JOBS += [("astguard_5ep_s42", "astguard_5ep", 42), ("shuffled_5ep_s42", "shuffled_5ep", 42)]


def load_jobs(path):
    """Jobs file: JSON list of {tag, train_cfg, diag_cfg (nullable), seed}. Registers each as a condition."""
    jobs = []
    for entry in json.loads(Path(path).read_text()):
        condition = f"custom_{entry['tag']}"
        CONDITIONS[condition] = (entry["train_cfg"], entry.get("diag_cfg"))
        jobs.append((entry["tag"], condition, int(entry["seed"])))
    return jobs


def log(event, **fields):
    row = {"utc": datetime.now(timezone.utc).isoformat(), "event": event, **fields}
    print(json.dumps(row), flush=True)
    with STATUS.open("a") as handle:
        handle.write(json.dumps(row) + "\n")


def gpu_state():
    out = subprocess.run(["nvidia-smi", "--query-gpu=index,memory.used,utilization.gpu",
                          "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout
    state = {}
    for line in out.strip().splitlines():
        index, mem, util = (int(x) for x in line.split(","))
        state[index] = (mem, util)
    return state


def launch(tag, condition, seed, gpu):
    train_cfg, diag_cfg = CONDITIONS[condition]
    dir_file = f"/tmp/seedq_{tag}_dir.txt"
    diag = "" if diag_cfg is None else f"""
python scripts/diagnose_structure_sensitivity.py --config {diag_cfg} \\
  --features {FEATDIR}/tune.jsonl --checkpoint "$RUN/checkpoints/best.safetensors" \\
  --batch-size 16 --max-examples 512 \\
  --output artifacts/audits/diagnostics/seedq_{tag}.json || echo DIAG_FAILED
"""
    script = f"""
set -uo pipefail
cd {ROOT}
source .venv/bin/activate
export TOKENIZERS_PARALLELISM=false CUDA_VISIBLE_DEVICES={gpu}
python -m astguard.train --config {train_cfg} --seed {seed} \
  --features {FEATDIR}/train.jsonl --tune-features {FEATDIR}/tune.jsonl --runs-root runs > {dir_file} || exit 1
RUN=$(tail -1 {dir_file})
echo "RUN=$RUN"
{diag}"""
    handle = (QDIR / f"{tag}.log").open("a")
    return subprocess.Popen(["bash", "-c", script], stdout=handle, stderr=subprocess.STDOUT)


def main():
    global JOBS, QDIR, STATUS
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", help="JSON jobs file; default is the legacy Stage 0 list")
    parser.add_argument("--qname", default="seedq", help="subdirectory of artifacts/release_gates for logs/status")
    args = parser.parse_args()
    if args.jobs:
        JOBS = load_jobs(args.jobs)
    QDIR = ROOT / "artifacts/release_gates" / args.qname
    STATUS = QDIR / "status.jsonl"
    QDIR.mkdir(parents=True, exist_ok=True)
    pending = list(JOBS)
    attempts = {tag: 0 for tag, _, _ in JOBS}
    running = {}
    log("queue_start", jobs=[tag for tag, _, _ in JOBS], excluded=sorted(EXCLUDED_GPUS))
    while pending or running:
        for tag, (proc, gpu) in list(running.items()):
            code = proc.poll()
            if code is None:
                continue
            del running[tag]
            if code == 0:
                log("job_done", tag=tag, gpu=gpu)
            else:
                log("job_failed", tag=tag, gpu=gpu, code=code, attempt=attempts[tag])
                if attempts[tag] < 2:
                    pending.insert(0, next(job for job in JOBS if job[0] == tag))
        if pending:
            held = {gpu for _, gpu in running.values()}
            state = gpu_state()
            free = [g for g, (mem, util) in sorted(state.items())
                    if g not in EXCLUDED_GPUS and g not in held and mem < FREE_MEM_MIB and util < FREE_UTIL_PCT]
            if free:
                tag, condition, seed = pending.pop(0)
                attempts[tag] += 1
                running[tag] = (launch(tag, condition, seed, free[0]), free[0])
                log("job_start", tag=tag, gpu=free[0], seed=seed, condition=condition, attempt=attempts[tag])
                time.sleep(120)
                continue
        time.sleep(POLL_SECONDS)
    log("queue_complete")


if __name__ == "__main__":
    main()
