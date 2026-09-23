from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from astguard.analysis.aggregate import ResultAggregator
from astguard.utils.atomic_io import atomic_write_json


def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--manifest"); p.add_argument("--experiment",default="E1")
    p.add_argument("--stage",default="final_train");p.add_argument("--predictions",nargs="+")
    p.add_argument("--output-dir",default="results/tables"); args=p.parse_args(argv)
    if not args.predictions: raise RuntimeError("no prediction artifacts supplied; numeric tables are never fabricated")
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True); agg=ResultAggregator(); rows=agg.aggregate_predictions(args.predictions,out/"aggregate.json"); agg.build_markdown_table(rows,out/"main.md")
    summary=agg.summarize_seeds(rows)
    if args.manifest:
        jobs=[json.loads(line) for line in Path(args.manifest).read_text(encoding="utf-8").splitlines() if line.strip()]
        expected={}
        for job in jobs:
            if job["experiment_id"]==args.experiment and job["stage"]==args.stage:
                expected.setdefault(job["model_id"],set()).add(int(job["seed"]))
        for row in summary:
            if row["model_id"] in expected and set(row["seeds"])!=expected[row["model_id"]]:
                raise ValueError(f"incomplete planned seed set for {row['model_id']}: expected {sorted(expected[row['model_id']])}, got {row['seeds']}")
    agg.write_summary_tables(summary,out)
    from astguard.analysis.plots import write_metric_figure
    write_metric_figure(summary,out/'main_results')
    atomic_write_json(out/'provenance_map.json',{row['model_id']:row['run_prediction_hashes'] for row in summary})
    return 0


if __name__ == "__main__": raise SystemExit(main())
