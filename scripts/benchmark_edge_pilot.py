"""Retest saved pilot checkpoints serially, without training or model selection."""
import argparse
import gc
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch
from safetensors.torch import load_model
from torch.utils.data import DataLoader
from astguard.config import load_config
from astguard.data.schema import read_jsonl
from astguard.models.factory import create_model, create_collator
from astguard.training.engine import Trainer
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file
from run_edge_pilot import benchmark


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--output', required=True, help='new file only')
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(output)
    root = Path(args.run)
    torch.set_num_threads(2)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    features = list(read_jsonl(root/'features/development_validation.jsonl'))
    rows = []
    for metrics in json.loads((root/'pilot_results.json').read_text()):
        run = root/metrics['model']
        config = load_config(run/'resolved_config.json')
        model = create_model(config).to(device)
        load_model(model, str(run/'best.safetensors'))
        loader = DataLoader(features, batch_size=config.training.microbatch_size, collate_fn=create_collator(config))
        trainer = Trainer(model, None, device=device)
        if device == 'cuda':
            torch.cuda.reset_peak_memory_stats()
        row = {'model': metrics['model'], 'run_id': str(run), 'device': device, 'threads': 2,
               'checkpoint_hash': sha256_file(run/'best.safetensors'), **benchmark(trainer, loader),
               'peak_inference_gpu_bytes': torch.cuda.max_memory_allocated() if device == 'cuda' else None}
        rows.append(row)
        print(json.dumps(row), flush=True)
        del trainer, model
        gc.collect()
        if device == 'cuda':
            torch.cuda.empty_cache()
    atomic_write_json(output, {'kind': 'serial_saved_checkpoint_inference', 'training_rerun': False, 'rows': rows})


if __name__ == '__main__':
    main()
