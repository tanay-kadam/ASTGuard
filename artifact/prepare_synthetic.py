"""Unpack the packaged synthetic feature inputs with SHA256 verification."""
import gzip
import hashlib
import json
import shutil
from pathlib import Path

def main():
    root=Path(__file__).resolve().parent
    manifest=json.loads((root/'inputs/synthetic/manifest.json').read_text())
    dest=root/'downloads/inputs/synthetic';dest.mkdir(parents=True,exist_ok=True)
    for role,expected in manifest['hashes'].items():
        source=root/'inputs/synthetic'/(role+'.jsonl.gz');target=dest/(role+'.jsonl')
        if not target.exists():
            partial=target.with_suffix('.jsonl.partial')
            with gzip.open(source,'rb') as src,partial.open('wb') as dst:shutil.copyfileobj(src,dst)
            partial.replace(target)
        if hashlib.sha256(target.read_bytes()).hexdigest()!=expected:raise ValueError('Input hash: '+role)
        print('Verified',target)

if __name__=='__main__':main()
