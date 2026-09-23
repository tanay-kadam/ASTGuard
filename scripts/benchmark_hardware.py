from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.provenance import environment_snapshot


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    result = environment_snapshot(["torch","transformers","tree-sitter","numpy"])
    try:
        import torch
        result["torch"] = {"version": torch.__version__, "cuda_available": torch.cuda.is_available(), "cuda_version": torch.version.cuda}
        result["gpus"] = [{"index": i, "name": torch.cuda.get_device_name(i), "total_memory_bytes": torch.cuda.get_device_properties(i).total_memory,
                           "bf16_supported": torch.cuda.is_bf16_supported()} for i in range(torch.cuda.device_count())]
    except ImportError:
        result["torch"] = None
        result["gpus"] = []
    atomic_write_json(args.output, result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__": raise SystemExit(main())

