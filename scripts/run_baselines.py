from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from astguard.baselines import graphcodebert,linevul,regvd,devign,unixcoder
from astguard.utils.atomic_io import atomic_write_json

LITERATURE_ONLY = [
    {"model_id":"k_astro","status":"source_not_verified",
     "reason":"No runnable public repository was verified in the registered Stage 0 audit; no surrogate implementation is permitted."},
    {"model_id":"tna_caf","status":"source_not_verified",
     "reason":"Publisher-preview method; no runnable public repository was verified in the registered Stage 0 audit."},
    {"model_id":"dualgraphvuld","status":"source_not_verified",
     "reason":"Publisher-preview method; no runnable public repository was verified in the registered Stage 0 audit."},
]


def main(argv=None):
    parser=argparse.ArgumentParser(); parser.add_argument("--baselines",nargs="+",required=True); parser.add_argument("--stage",default="smoke"); parser.add_argument("--output",default="artifacts/baseline_status.json")
    args=parser.parse_args(argv)
    statuses={x["model_id"]:x for x in [graphcodebert.STATUS,linevul.STATUS,regvd.STATUS,devign.STATUS,unixcoder.STATUS,*LITERATURE_ONLY]}
    rows=[statuses.get(name,{"model_id":name,"status":"unknown","reason":"No registered adapter"}) for name in args.baselines]
    atomic_write_json(args.output,rows); print(json.dumps(rows,indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
