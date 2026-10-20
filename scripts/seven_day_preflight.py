"""Read-only server and input inventory for the seven-day campaign."""
import hashlib
import json
import platform
import shutil
import subprocess
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    import torch
    root = Path('/home/tkadam/ASTGuard')
    paths = ['astguard/train.py', 'astguard/training/engine.py',
             'astguard/data/graph_donors.py', 'astguard/data/null_graphs.py',
             'data/strengthening_20261006/real/manifest.json',
             'data/strengthening_20261006/synthetic/manifest.json',
             'artifacts/release_gates/strengthening_20261006/jobs.json']
    print(json.dumps({'python': platform.python_version(), 'torch': torch.__version__,
        'cuda_count': torch.cuda.device_count(), 'cwd': str(Path.cwd()),
        'input_hashes': {p: sha(root/p) for p in paths},
        'tmp_free': shutil.disk_usage('/tmp').free,
        'gpu': subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,name,memory.used,utilization.gpu',
                                       '--format=csv,noheader'], text=True)}, indent=2))


if __name__ == '__main__':
    main()
