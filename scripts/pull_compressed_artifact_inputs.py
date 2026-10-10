"""Stream large JSONL inputs through SSH gzip and verify their original hashes.

Uses native OpenSSH, existing host-key validation, and no remote temporary copy.
The original input remains untouched; the locally expanded file must match the
previously frozen inventory before becoming part of the import.
"""
import argparse
import gzip
import hashlib
import json
import shlex
import shutil
import subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',default='seeklab')
    p.add_argument('--ssh',default=r'C:\Windows\System32\OpenSSH\ssh.exe')
    p.add_argument('--import-root',type=Path,default=Path('artifacts/ssh_import_20261009'))
    a=p.parse_args();inventory=json.loads((a.import_root/'inventory.json').read_text())
    entries={r['path']:r for r in inventory['files']};assets=Path('output/artifact_release');assets.mkdir(parents=True,exist_ok=True)
    for role in ['train','regvd_train']:
        rel='data/strengthening_20261006/real/'+role+'.jsonl';record=entries[rel]
        asset=assets/('inputs-real-'+role+'.jsonl.gz')
        if not asset.exists():
            partial=asset.with_name(asset.name+'.partial')
            remote=inventory['source_root']+'/'+rel
            offset=partial.stat().st_size if partial.exists() else 0
            command='set -o pipefail; gzip -n -c -- '+shlex.quote(remote)
            if offset:command+=' | tail -c +'+str(offset+1)
            with partial.open('ab') as stream:
                subprocess.run([a.ssh,'-o','BatchMode=yes','-o','ConnectTimeout=20','-o','ServerAliveInterval=20',a.host,command],stdout=stream,check=True)
            partial.replace(asset)
        dest=a.import_root/'snapshot'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        partial=dest.with_name(dest.name+'.gzip_partial');h=hashlib.sha256();size=0
        with gzip.open(asset,'rb') as src,partial.open('wb') as dst:
            for b in iter(lambda:src.read(8*1024*1024),b''):dst.write(b);h.update(b);size+=len(b)
        if h.hexdigest()!=record['sha256'] or size!=record['bytes']:raise ValueError('Original hash mismatch: '+rel)
        # A concurrent normal import, if any, must describe the same immutable file.
        if dest.exists():
            existing=hashlib.sha256()
            with dest.open('rb') as f:
                for b in iter(lambda:f.read(8*1024*1024),b''):existing.update(b)
            if existing.hexdigest()!=record['sha256']:raise FileExistsError('Different import exists: '+rel)
            partial.unlink()
        else:partial.replace(dest)
        print(json.dumps({'verified_input':rel,'original_bytes':size,'compressed_bytes':asset.stat().st_size}),flush=True)

if __name__=='__main__':main()
