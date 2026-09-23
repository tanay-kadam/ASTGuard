from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="protocol/experiment_manifest.jsonl")
    parser.add_argument("--sources", default="sources.lock.json")
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--preprocessing-manifest", required=True)
    parser.add_argument('--stage-evidence',required=True,help='Verified release-gate evidence manifest')
    parser.add_argument('--selected-configs',nargs='+',required=True)
    args = parser.parse_args(argv)
    sources = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    if not sources.get("sources"):
        raise RuntimeError("cannot freeze: no immutable sources are registered")
    from astguard.config import load_config
    from astguard.utils.hashing import object_hash
    import dataclasses
    evidence=json.loads(Path(args.stage_evidence).read_text())
    required={'data_integrity','extraction_gold','extraction_coverage','baseline_overfit','model_equivalence','hpo_complete','power_diagnostic'}
    if any(evidence.get(key,{}).get('status')!='passed' for key in required):
        raise RuntimeError('release gates have not all passed')
    for key in required:
        entry=evidence[key]
        if sha256_file(entry['artifact'])!=entry['sha256']:
            raise RuntimeError(f'gate evidence changed: {key}')
    configs=[load_config(path) for path in args.selected_configs]
    jobs = [json.loads(line) for line in Path(args.manifest).read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(jobs) != 200 or len({job["job_id"] for job in jobs}) != 200:
        raise RuntimeError("cannot freeze: finite registered ledger must contain 200 unique jobs")
    lock = {"status":"unlocked","frozen_utc":datetime.now(timezone.utc).isoformat(),
            "protocol_hash":sha256_file("protocol/protocol_v1.json"),"manifest_hash":sha256_file(args.manifest),
            "sources_hash":sha256_file(args.sources),"split_manifest_hash":sha256_file(args.split_manifest),
            "preprocessing_manifest_hash":sha256_file(args.preprocessing_manifest)}
    paths=['protocol/protocol_v1.json',args.manifest,args.sources,args.split_manifest,args.preprocessing_manifest,args.stage_evidence,*args.selected_configs]
    lock['artifacts']={path:sha256_file(path) for path in paths}
    lock['selected_config_hashes']=[object_hash(dataclasses.asdict(cfg)) for cfg in configs]
    atomic_write_json("protocol/test_unlock.json", lock)
    print(json.dumps(lock, indent=2))
    return 0


if __name__ == "__main__": raise SystemExit(main())
