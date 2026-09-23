from __future__ import annotations

import argparse
from pathlib import Path

from astguard.analysis.runner import (efficiency_report, failure_strata, gate_report,
                                      pair_report, read_rows, write_report)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--analyses", nargs="+", default=["gates"])
    parser.add_argument("--predictions")
    parser.add_argument("--pairs", help="JSON/JSONL rows with pair_id,vulnerable_id,patched_id")
    parser.add_argument("--features", help="feature rows for failure-strata joins")
    parser.add_argument("--gate-values", help="rows with layer,head,relation,gate,degree")
    parser.add_argument("--timing", nargs="*", default=[])
    parser.add_argument("--output-dir")
    args = parser.parse_args(argv)
    run = Path(args.run)
    output = Path(args.output_dir or run / "analysis")
    output.mkdir(parents=True, exist_ok=True)
    prediction_path = Path(args.predictions or run / "predictions" / "test.json")
    predictions = read_rows(prediction_path) if any(name in args.analyses for name in ("pairs", "failures")) else []
    for name in args.analyses:
        if name == "pairs":
            if not args.pairs:
                raise ValueError("pairs analysis requires --pairs definitions")
            write_report(output / "paired_results.json", pair_report(predictions, read_rows(args.pairs)))
        elif name == "failures":
            if not args.features:
                raise ValueError("failures analysis requires --features")
            write_report(output / "failure_strata.json", failure_strata(predictions, read_rows(args.features)))
        elif name == "gates":
            if not args.gate_values:
                raise ValueError("gates analysis requires --gate-values captured during inference")
            write_report(output / "gate_statistics.json", gate_report(read_rows(args.gate_values)))
        elif name == "efficiency":
            if not args.timing:
                raise ValueError("efficiency analysis requires one or more --timing JSON artifacts")
            write_report(output / "efficiency.json", efficiency_report(args.timing))
        else:
            raise ValueError(f"unknown analysis {name}")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
